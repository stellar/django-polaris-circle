from decimal import Decimal
from typing import Tuple

from stellar_sdk import Memo, IdMemo

from polaris.models import Transaction
from polaris.integrations import CustodyIntegration

from polaris_circle.client import CircleClient

__all__ = ["CircleIntegration"]


class CircleIntegration(CustodyIntegration):
    def __init__(self, api_key: str, api_url: str, wallet_id: str):
        self.api_key = api_key
        self.api_url = api_url
        self.wallet_id = wallet_id
        self.client = CircleClient(
            api_key=self.api_key, api_url=self.api_url, wallet_id=self.wallet_id
        )

    def get_receiving_account_and_memo(
        self, transaction: Transaction
    ) -> Tuple[str, Memo]:
        response = self.client.create_address(idempotency_key=str(transaction.id))
        return response["data"]["address"], IdMemo(int(response["data"]["addressTag"]))

    def submit_deposit_transaction(self, transaction: Transaction) -> dict:
        payment_amount = round(
            Decimal(transaction.amount_in) - Decimal(transaction.amount_fee),
            transaction.asset.significant_decimals,
        )
        return self.client.create_transfer(
            idempotency_key=str(transaction.id),
            account=transaction.to_address,
            amount=str(payment_amount),
            memo=transaction.memo,
        )

    def create_destination_account(self, transaction: Transaction) -> dict:
        raise NotImplementedError()
