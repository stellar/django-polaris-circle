from decimal import Decimal

from rest_framework.request import Request
from polaris.models import Transaction, Asset
from polaris.integrations import CustodyIntegration

from polaris_circle.client import CircleClient
from polaris import settings
from stellar_sdk import Server

__all__ = ["CircleIntegration"]


class CircleIntegration(CustodyIntegration):
    def __init__(self, api_key: str, api_url: str, wallet_id: str):
        self.api_key = api_key
        self.api_url = api_url
        self.wallet_id = wallet_id
        self.client = CircleClient(
            api_key=self.api_key, api_url=self.api_url, wallet_id=self.wallet_id
        )

    def save_receiving_account_and_memo(
        self, request: Request, transaction: Transaction
    ):
        response = self.client.create_address(idempotency_key=str(transaction.id))
        transaction.receiving_anchor_account = response["data"]["address"]
        transaction.memo = response["data"]["addressTag"]
        transaction.memo_type = Transaction.MEMO_TYPES.id
        transaction.save()

    def submit_deposit_transaction(
        self, transaction: Transaction, has_trustline: bool = True
    ) -> dict:
        payment_amount = round(
            Decimal(transaction.amount_in) - Decimal(transaction.amount_fee),
            transaction.asset.significant_decimals,
        )
        response = self.client.create_transfer(
            idempotency_key=str(transaction.id),
            account=transaction.to_address,
            amount=str(payment_amount),
            memo=transaction.memo,
        )
        transaction_hash = response.get("transactionHash")
        while not transaction_hash:
            response = self.client.get_transfer(response["id"])
            if response["status"] == "failed":
                raise RuntimeError(
                    "Circle failed to complete the transfer. "
                    f"Error code: {response['errorCode']}"
                )
            if response["status"] == "complete":
                transaction_hash = response["transactionHash"]
                break
        with Server(horizon_url=settings.HORIZON_URI) as server:
            return server.transactions().transaction(transaction_hash).call()

    def requires_third_party_signatures(self, transaction: Transaction) -> bool:
        return False

    def create_destination_account(self, transaction: Transaction) -> dict:
        raise NotImplementedError()

    def get_distribution_account(self, asset: Asset) -> str:
        raise NotImplementedError()

    @property
    def account_creation_supported(self):
        return False

    @property
    def claimable_balances_supported(self):
        return False
