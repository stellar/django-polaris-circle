from polaris.integrations import CustodyIntegration

__all__ = ["CircleIntegration"]


class CircleIntegration(CustodyIntegration):
    def __init__(self, api_key: str, api_url: str, wallet_id: str):
        self.api_key = api_key
        self.api_url = api_url
        self.wallet_id = wallet_id
