from dataclasses import dataclass
from loguru import logger
import base64
import requests
import json


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
        "webhook_subscribe": "/webhooks/subscribe/",
        "update_order": "/orders/createorder/",
    }
    order_status_able_to_be_updated = [
        "awaiting_payment",
        "awaiting_shipment",
        "on_hold",
    ]
    remove_order_keys_before_updating = [
        "createDate",
        "modifyDate",
        "customerId",
        "orderTotal",
        "holdUntilDate",
        "userId",
        "externallyFulfilled",
        "externallyFulfilledBy",
        "externallyFulfilledById",
        "externallyFulfilledByName",
        "labelMessages",
    ]
    host: str = "ssapi.shipstation.com"
    request_remaining: int = 40
    request_next_cycle_in_seconds: int = 60

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

    def create_webhook_endpoint(
        self,
        target_url: str,
        event: str = "ORDER_NOTIFY",
        store_id: str = None,
        friendly_name: str = None,
    ) -> bool:
        if self.api_limit_at_max():
            logger.error(
                f"API limit reached. Try again after {self.request_next_cycle_in_seconds} seconds -- order {order_id}"
            )
            return False
        webhook_url = self.build_path_url("webhook_subscribe")
        event_body = {"target_url": target_url, "event": event}
        if store_id:
            event_body = event_body | {"store_id": store_id}
        if friendly_name:
            event_body = event_body | {"friendly_name": friendly_name}
        headers = self.authorization_header | {"Content-Type": "application/json"}
        res = requests.post(webhook_url, json=event_body, headers=headers)
        if not res.ok:
            logger.error(f"Failed to make webhook: {res.status_code} -- {res.text}")
            return False
        logger.success(f"Webhook created: {res.json()}")
        return True

    def get_webhooks(self) -> dict:
        if self.api_limit_at_max():
            logger.error(
                f"API limit reached. Try again after {self.request_next_cycle_in_seconds} seconds -- order {order_id}"
            )
            return False
        webhook_url = self.build_path_url("webhooks")
        res = requests.get(webhook_url, headers=self.authorization_header)
        if not res.ok:
            logger.error(f"Failed to get webhook lists {res.status_code} -- {res.text}")
            return {}
        return res.json()


    def get_all_stores(self, show_inactive_stores: bool = False) -> dict[str, dict]:
        stores_url = self.build_path_url("stores")
        params = {"showInactive": show_inactive_stores}
        res = requests.get(
            stores_url, params=params, headers=self.authorization_header, timeout=10
        )
        if not res.ok:
            logger.error(f"Failed to get stores URL: {res.reason} -- {res.text}")
            return {}
        self.request_remaining = res.headers["X-Rate-Limit-Remaining"]
        self.request_next_cycle_in_seconds = res.headers["X-Rate-Limit-Reset"]
        return res.json()

    def get_order(self, order_id: str, custom_params: dict = {}) -> dict[str, dict]:
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
        self.request_next_cycle_in_seconds = res.headers["X-Rate-Limit-Reset"]
        self.request_remaining = res.headers["X-Rate-Limit-Remaining"]
        return res.json()

    def get_order_by_order_number(self, order_number: str) -> dict[str, dict]:
        order = self.get_all_orders(custom_params={"orderNumber": order_number})
        if not order:
            logger.error(f"Failed to get order with order number {order_number}")
            return {}
        return order

    def api_limit_at_max(self) -> bool:
        return int(self.request_remaining) <= 0

    def get_all_orders(self, custom_params: dict = {}) -> dict[str, str]:
        order_url = self.build_path_url("orders")
        params = custom_params
        res = requests.get(
            order_url, params=params, headers=self.authorization_header, timeout=10
        )
        if not res.ok:
            logger.error(f"Failed to get all orders: {res.status_code} -- {res.text}")
            return {}
        self.request_remaining = res.headers["X-Rate-Limit-Remaining"]
        self.request_next_cycle_in_seconds = res.headers["X-Rate-Limit-Reset"]
        return res.json()

    def get_waiting_orders(self, status: str = "awaiting_shipment") -> dict[str, str]:
        order = self.get_all_orders(custom_params={"orderStatus": status})
        if not order:
            logger.error(f"Unable to get orders with {status} status")
            return {}
        return order

    def get_order_id_by_order_number(self, order_number: str) -> list[str]:
        orders = self.get_all_orders(custom_params={"orderNumber": order_number})
        if not orders:
            logger.error(f"Failed to get order with order number {order_number}")
            return []
        elif len(orders["orders"]) >= 2:
            logger.warning(
                f"Ambiguous number of orders for order number {order_number}"
            )
        return [str(order["orderId"]) for order in orders["orders"]]

    def is_order_able_to_be_updated(self, order_json: dict) -> str:
        order_status = order_json["orderStatus"]
        return order_status in self.order_status_able_to_be_updated

    def update_order_notes(
        self,
        order_id: str,
        custom_note: str,
        custom_note2: str = "",
        custom_note3: str = "",
    ) -> bool:
        """
        Updates the custom note fields in a ShipStation order
            :param order_id: The id of the order needed to be updated
            :param custom_note: String for the Order's first custom note field
            :param custom_note2: (Optional) String for the Order's second custom note field
            :param custom_note3: (Optional) String for the Order's third custom note field
        Note: As of 2-22-24, partial updates to orders are not supported, you need to update the entire order as it was originally entered

        Production Test Order ID: 372872713
        """
        update_status = False
        order = self.get_order(order_id=order_id)
        if not order:
            logger.error(f"Unable to get order {order_id}")
            return update_status
        if self.api_limit_at_max():
            logger.error(
                f"API limit reached. Try again after {self.request_next_cycle_in_seconds} seconds -- order {order_id}"
            )
            return update_status
        if not self.is_order_able_to_be_updated(order):
            order_status = order["orderStatus"]
            logger.error(
                f"Order {order_id} is not able to be updated. In status {order_status}"
            )
        order_body = {
            k: v
            for k, v in order.items()
            if k not in self.remove_order_keys_before_updating
        }
        order_body["advancedOptions"]["customField1"] = custom_note
        if custom_note2:
            order_body["advancedOptions"]["customField2"] = custom_note2
        if custom_note3:
            order_body["advancedOptions"]["customField3"] = custom_note3
        order_url = self.build_path_url("update_order")
        headers = self.authorization_header | {"Content-Type": "application/json"}
        res = requests.post(order_url, json=order_body, headers=headers, timeout=10)
        if not res.ok:
            logger.error(f"Failed to send order. {res.status_code} -- {res.text}")
            return update_status
        self.request_remaining = res.headers["X-Rate-Limit-Remaining"]
        self.request_next_cycle_in_seconds = res.headers["X-Rate-Limit-Reset"]
        update_status = True
        return update_status
