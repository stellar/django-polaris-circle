import time
import sys
import signal
from typing import Optional
from datetime import datetime, timezone
from urllib3.exceptions import NewConnectionError

from requests import RequestException
from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError
from polaris.integrations import registered_custody_integration as rci
from polaris.models import Transaction
from polaris.utils import getLogger, maybe_make_callback

from polaris_circle.integrations import CircleIntegration
from polaris_circle.client import CircleClient


TERMINATE = False
"""
SIGINT and SIGTERM signals to this process set TERMINATE to True,
and once all pending tasks complete, the process exits.
Only relevant if the --loop option is specified.
"""

DEFAULT_INTERVAL = 10
"""
The default amount of time to sleep before querying for transfers again
Only used if the --loop option is specified.
"""

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    @staticmethod
    def exit_gracefully(*_):
        """
        TODO: use logger
        """
        logger.info("Exiting process_pending_deposits...")
        module = sys.modules[__name__]
        module.TERMINATE = True

    def add_arguments(self, parser):  # pragma: no cover
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Continually restart command after a specified number of seconds.",
        )
        parser.add_argument(
            "--interval",
            "-i",
            type=int,
            help="The number of seconds to wait before restarting command. "
            "Defaults to {}.".format(DEFAULT_INTERVAL),
        )

    @staticmethod
    def sleep(seconds: int):  # pragma: no cover
        for _ in range(seconds):
            if TERMINATE:
                break
            time.sleep(1)

    def handle(self, *_args, **options):
        if not isinstance(rci, CircleIntegration):
            raise CommandError(
                "registered custodial integration is not an instance of CircleIntegration"
            )
        client_kwargs = {
            "api_key": rci.api_key,
            "api_url": rci.api_url,
            "wallet_id": rci.wallet_id,
        }
        with CircleClient(**client_kwargs) as client:
            if options.get("loop"):
                while True:
                    if TERMINATE:
                        break
                    self.poll_incoming_transfers(client)
                    self.sleep(options.get("interval") or DEFAULT_INTERVAL)
            else:
                self.poll_incoming_transfers(client)

    @classmethod
    def poll_incoming_transfers(cls, client: CircleClient):
        get_transfers_before = datetime.now(timezone.utc)
        reached_processed_transfer = False
        last_seen_transfer_id = None
        while not (reached_processed_transfer or TERMINATE):
            transfers = cls.get_transfers(client, get_transfers_before)
            # failed to fetch transfers or all transfers have been processed
            if not transfers:
                break
            for transfer in transfers["data"]:
                # GET /transfers 'to' parameter is inclusive so we need to skip
                # the first record returned in the response if we've seen it before.
                if transfer["id"] == last_seen_transfer_id:
                    continue
                get_transfers_before = datetime.strptime(
                    transfer["createDate"], "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                last_seen_transfer_id = transfer["id"]
                # skip outgoing transactions
                # TODO: confirm the only "status" for incoming transfers is "complete"
                if transfer["destination"]["type"] != "wallet":
                    continue
                transaction = cls.get_matching_transaction(
                    transfer["destination"]["address"],
                    transfer["destination"]["addressTag"],
                )
                if not transaction:
                    continue
                elif transaction.external_transaction_id:
                    reached_processed_transfer = True
                    break
                cls.process_matched_transaction(transaction, transfer)

    @staticmethod
    def get_transfers(client: CircleClient, before: datetime) -> Optional[dict]:
        try:
            transfers = client.get_transfers(to_datetime=before)
        except (RequestException, NewConnectionError):
            logger.exception("an exception was raised making a GET /transfers request")
            return
        if "data" not in transfers:
            logger.error(
                f"unexpected response format for GET /transfers request: {transfers}"
            )
            return
        elif len(transfers["data"]) == 0:
            return
        else:
            return transfers

    @staticmethod
    def get_matching_transaction(account: str, memo: str) -> Optional[Transaction]:
        withdraw_filters = Q(
            status=Transaction.STATUS.pending_user_transfer_start,
            kind=Transaction.KIND.withdrawal,
        )
        send_filters = Q(
            status=Transaction.STATUS.pending_sender, kind=Transaction.KIND.send,
        )
        transaction = Transaction.objects.filter(
            withdraw_filters | send_filters, receiving_anchor_account=account, memo=memo
        ).first()
        return transaction

    @staticmethod
    def process_matched_transaction(transaction: Transaction, transfer: dict):
        transaction.external_transaction_id = transfer["id"]
        transaction.stellar_transaction_id = transfer["transactionHash"]
        transaction.amount_in = transfer["amount"]["amount"]
        if transaction.protocol == Transaction.PROTOCOL.sep31:
            transaction.status = Transaction.STATUS.pending_receiver
        else:
            transaction.status = Transaction.STATUS.pending_anchor
        transaction.save()
        maybe_make_callback(transaction)