from dataclasses import dataclass
from loguru import logger
import base64
import requests


@dataclass
class ShipStationMeta:
    rate_limit_headers = [
        "X-Rate-Limit-Limit",
        "X-Rate-Limit-Remaining",
        "X-Rate-Limit-Reset",
    ]
    route_map = {
        "orders": "/orders/",
        "stores": "/stores/",
        "webhooks": "/webhooks/",
    }
    host: str = "ssapi.shipstation.com"
    request_remaining: int = 40

    def build_path_url(self, path: str) -> str:
        if path.lower() in self.route_map:
            return "https://" + self.host + self.route_map[path]
        return "https://" + self.host


class ShipStation(ShipStationMeta):
    def __init__(self, api_key, api_secret):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.__build_authorization_header()

    @staticmethod
    def authorize_request(self, auth_string: str) -> bool:
        is_authorized = False

        if "basic" in auth_string.lower():
            auth_string = auth_string.lower().split("basic ")[-1]

        decoded_string = base64.standard_b64decode(auth_string).decode("utf-8")
        decoded_string = decoded_string.split(":")
        if len(decoded_string) < 2:
            logger.error("Authorization Failed: decoded auth key has length < 2")
            return is_authorized

        given_key = decoded_string[0]
        given_secret = decoded_string[1]

        if given_key != self.api_key and given_secret != self.api_secret:
            logger.error("Authorization Failed: Given information is invalid")
            return is_authorized

        is_authorized = True
        return is_authorized

    def __build_authorization_header(self):
        auth_key_base64 = base64.b64encode(
            f"{self.api_key}:{self.api_secret}".encode("utf-8")
        )
        auth_key_base64 = auth_key_base64.decode("utf-8")
        self.authorization_header = {"Authorization": f"Basic {auth_key_base64}"}

    @staticmethod
    def create_webhook_endpoint(
        self,
        target_url: str,
        event: str = "ORDER_NOTIFY",
        store_id: str = None,
        friendly_name: str = None,
    ):
        pass

    def get_all_stores(self, show_inactive_stores: bool = False) -> {}:
        stores_url = self.build_path_url("stores")
        params = {"showInactive": show_inactive_stores}
        print(self.request_remaining)
        res = requests.get(
            stores_url, params=params, headers=self.authorization_header, timeout=10
        )
        if not res.ok:
            logger.error(f"Failed to get stores URL: {res.reason} -- {res.text}")
            return {}
        self.request_remaining = res.headers["X-Rate-Limit-Remaining"]
        return res.json()

    def get_order(self, order_id: str, custom_params: dict = {}) -> {}:
        order_url = self.build_path_url("orders") + order_id
        params = custom_params
        res = requests.get(
            order_url, params=params, headers=self.authorization_header, timeout=10
        )
        if not res.ok:
            logger.error(
                f"Failed to get order {order_id}: {res.status_code} -- {res.text}"
            )
            return {}
        self.request_remaining = res.headers["X-Rate-Limit-Remaining"]
        return res.json()

    def get_order_by_order_number(self, order_number: str) -> {}:
        order = self.get_all_orders(custom_params={"orderNumber": order_number})
        if not order:
            logger.error(f"Failed to get order with order number {order_number}")
            return {}
        return order

    def get_all_orders(self, custom_params: dict = {}) -> {}:
        order_url = self.build_path_url("orders")
        params = custom_params
        res = requests.get(
            order_url, params=params, headers=self.authorization_header, timeout=10
        )
        if not res.ok:
            logger.error(f"Failed to get all orders: {res.status_code} -- {res.text}")
            return {}
        self.request_remaining = res.headers["X-Rate-Limit-Remaining"]
        return res.json()

    def get_waiting_orders(self, status: str = "awaiting_shipment") -> {}:
        order = self.get_all_orders(custom_params={"orderStatus": status})
        if not order:
            logger.error(f"Unable to get orders with {status} status")
            return {}
        return order

    def get_order_id_by_order_number(self, order_number: str) -> [str]:
        orders = self.get_all_orders(custom_params={"orderNumber": order_number})
        if not orders:
            logger.error(f"Failed to get order with order number {order_number}")
            return []
        elif len(orders["orders"]) >= 2:
            logger.warning(
                f"Ambiguous number of orders for order number {order_number}"
            )
        return [str(order["orderId"]) for order in orders["orders"]]

    def update_order_notes(self, order_id: str, notes_to_update: dict = {}) -> bool:
        """
            z["advancedOptions"]["customField1"]
        """
        return False
