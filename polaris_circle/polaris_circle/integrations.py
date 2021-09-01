from polaris.integrations import CustodialIntegration

__all__ = ["CircleIntegration"]


class CircleIntegration(CustodialIntegration):
    def __init__(self, api_key: str, wallet_id: str):
        self.api_key = api_key
        self.wallet_id = wallet_id
