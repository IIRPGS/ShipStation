import base64
from dataclasses import dataclass

import requests
from loguru import logger


@dataclass
class ShipStationMeta:
    """
    Dataclass for holding meta information about the ShipStation API and current instance's request limits

    Attributes:
        rate_limit_headers: (list) Headers used to keep track of request limits
        route_map: (dict) Used to retrieve api resource paths. Key is the simplified name, Value is the url path
        order_status_able_to_be_updated: (list) order statuses that are able to be changed/updated by the api
        remove_order_keys_before_updating: (list) keys from an order call that need to be removed before updating an order. See child function update_order_notes for reasoning
        host: (str) the host url for the ShipStation API
        request_remaining: (int) number of requests remaning in current api cycle
        request_next_cycle_in_seconds: (int) amount of seconds before the request cycle refreshes

    Methods:
        build_path_url: builds the api url based on the route_map
    """

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
        "webhook_delete": "/webhooks/",
        "order_update": "/orders/createorder/",
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

    def build_path_url(self, path: str, additional_path: str = "") -> str:
        """
        Helper function to build a specific api url
        i.e. build_path_url("orders") will return a str containing the url to the orders api
            :param path: a key in the route_map
            :param additional_path: any additional paths that should be included after the URL
        Returns the api url in str format
        """
        url = "https://" + self.host
        if path.lower() in self.route_map:
            url += self.route_map[path]
        if additional_path:
            url += additional_path
        return url


class ShipStation(ShipStationMeta):
    """
    Controller class for making requests to the ShipStation API
        Attributes:
            api_key: (str) ShipStation API key
            api_secret: (str) ShipStation API Secret
            authorization_headers: (dict) Header used for Basic HTTP authentication
    """

    def __init__(self, api_key, api_secret):
        """
        Initialization for the ShipStation class

        Args:
            api_key (str): ShipStation API key
            api_secret (str): ShipStation API Secret
        """
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.__build_authorization_header()

    def authorize_request(self, auth_string: str) -> bool:
        """
        Checks if the given key matches instance's saved key + secret combo
            :param auth_string: Base64 encoded string given by ShipStation
        Returns True/False if the given string matchs the instance's

        Decoded string format {api_key}:{api_secret}
        """
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
        """
        Internal function to create the authorization header needed for API requests

        Runs on init and saves to self.authorization_header
        """
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
        """
        Creates a webhook subscription
            :param target_url: URL where the webhook event should go to
            :param event: type of event to listen for
            :param store_id: (Optional) The store ID where the events should be watched
            :param friendly_name: (Optional) Easy to identify name for the webhook subscription
        Returns True/False depending on if the subscription was created or not
        """
        if self.api_limit_at_max():
            logger.error(
                f"API limit reached. Try again after {self.request_next_cycle_in_seconds} seconds"
            )
            return False
        webhook_url = self.build_path_url("webhook_subscribe")
        event_body = {"target_url": target_url, "event": event}
        if store_id:
            event_body = event_body | {"store_id": store_id}
        if friendly_name:
            event_body = event_body | {"friendly_name": friendly_name}
        headers = self.authorization_header | {"Content-Type": "application/json"}
        res = requests.post(webhook_url, json=event_body, headers=headers, timeout=5)
        if not res.ok:
            logger.error(f"Failed to make webhook: {res.status_code} -- {res.text}")
            return False
        logger.success(f"Webhook created: {res.json()}")
        return True

    def get_webhooks(self) -> list[dict]:
        """
        Lists all webhook subscriptions in the ShipStation instance
        Returns all subscriptions in ShipStation account. Dict format
        """
        if self.api_limit_at_max():
            logger.error(
                f"API limit reached. Try again after {self.request_next_cycle_in_seconds} seconds"
            )
            return False
        webhook_url = self.build_path_url("webhooks")
        res = requests.get(webhook_url, headers=self.authorization_header, timeout=5)
        if not res.ok:
            logger.error(f"Failed to get webhook lists {res.status_code} -- {res.text}")
            return {}
        return res.json()

    def delete_webhook(self, webhook_id: str) -> bool:
        """
        Deletes a specific webhook subscription from a ShipStaion account
            :param webhook_id: the webhook id to remove
        Returns True if webhook has been deleted, False if not
        """
        if self.api_limit_at_max():
            logger.error(
                f"API limit reached. Try again after {self.request_next_cycle_in_seconds} seconds"
            )
            return False
        webhook_url = self.build_path_url("webhook_delete", str(webhook_id))
        res = requests.delete(webhook_url, headers=self.authorization_header, timeout=5)
        if not res.ok:
            logger.error(f"Failed to get webhook lists {res.status_code} -- {res.text}")
            return False
        return True

    def get_all_stores(self, show_inactive_stores: bool = False) -> list[dict]:
        """
        Retrieve all stores in a ShipStation instance
            :param show_inactive_stores: True if results should have inactive stores, false if not
        Returns a dictionary containing all
        """
        stores_url = self.build_path_url("stores")
        params = {"showInactive": show_inactive_stores}
        res = requests.get(
            stores_url, params=params, headers=self.authorization_header, timeout=5
        )
        if not res.ok:
            logger.error(f"Failed to get stores URL: {res.reason} -- {res.text}")
            return {}
        self.request_remaining = res.headers["X-Rate-Limit-Remaining"]
        self.request_next_cycle_in_seconds = res.headers["X-Rate-Limit-Reset"]
        return res.json()

    def get_order(self, order_id: str, custom_params: dict = {}) -> list[dict]:
        """
        Attempts to get a single order given an order ID
            :param order_id: The order ID to search for
            :param custom_params: any custom fields to filter the request by
        Returns a list of dicts containing the order information
        """
        order_url = self.build_path_url("orders") + str(order_id)
        params = custom_params
        res = requests.get(
            order_url, params=params, headers=self.authorization_header, timeout=5
        )
        if not res.ok:
            logger.error(
                f"Failed to get order {str(order_id)}: {res.status_code} -- {res.text}"
            )
            return {}
        self.request_next_cycle_in_seconds = res.headers["X-Rate-Limit-Reset"]
        self.request_remaining = res.headers["X-Rate-Limit-Remaining"]
        return res.json()

    def get_order_by_order_number(self, order_number: str) -> list[dict]:
        """
        Returns a list of orders given an order number
            :param order_number: order number to search for
        Returns a list of dictionaries containing order details
        """
        order = self.get_all_orders(custom_params={"orderNumber": order_number})
        if not order:
            logger.error(f"Failed to get order with order number {order_number}")
            return {}
        return order

    def api_limit_at_max(self) -> bool:
        """
        Checks if the instance has reached it's max request in current cycle
        Returns True if instance cannot make a request, False if it can
        """
        return int(self.request_remaining) <= 0

    def get_all_orders(self, custom_params: dict = {}) -> list[dict]:
        """
        Get all orders in a ShipStation Instance
            :param custom_params: Custom filters for retrieving orders
        Returns
        """
        order_url = self.build_path_url("orders")
        params = custom_params
        res = requests.get(
            order_url, params=params, headers=self.authorization_header, timeout=5
        )
        if not res.ok:
            logger.error(f"Failed to get all orders: {res.status_code} -- {res.text}")
            return {}
        self.request_remaining = res.headers["X-Rate-Limit-Remaining"]
        self.request_next_cycle_in_seconds = res.headers["X-Rate-Limit-Reset"]
        return res.json()

    def get_waiting_orders(self, status: str = "awaiting_shipment") -> list[dict]:
        """
        Gets all orders with a specific status
            :param status: status of orders to look for
        Returns dictionary containing all order information
        """
        order = self.get_all_orders(custom_params={"orderStatus": status})
        if not order:
            logger.error(f"Unable to get orders with {status} status")
            return {}
        return order

    def get_order_id_by_order_number(self, order_number: str) -> list[str]:
        """
        Gets order information given an order number. May return more than one order if same number is being used in system
            :param order_number: Order number to get
        Returns a list of orders with given order number
        """
        orders = self.get_all_orders(custom_params={"orderNumber": order_number})
        if not orders:
            logger.error(f"Failed to get order with order number {order_number}")
            return []
        elif len(orders["orders"]) >= 2:
            logger.warning(
                f"Ambiguous number of orders for order number {order_number}"
            )
        return [str(order["orderId"]) for order in orders["orders"]]

    def is_order_able_to_be_updated(self, order_json: dict) -> bool:
        """
        Determines if the given order is able to be updated
            :param order_json: order information from the ShipStation API in json/dict format
        Returns True if the order is able to be updated. False otherwise
        """
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
                f"Order {order_id} is not able to be updated in {order_status} status"
            )
            return update_status
        order_body = {
            k: v
            for k, v in order.items()
            if k not in self.remove_order_keys_before_updating
        }
        # TODO: Change this to internal notes
        order_body["internalNotes"] = custom_note
        if custom_note2:
            order_body["advancedOptions"]["customField2"] = custom_note2
        if custom_note3:
            order_body["advancedOptions"]["customField3"] = custom_note3
        order_url = self.build_path_url("order_update")
        headers = self.authorization_header | {"Content-Type": "application/json"}
        res = requests.post(order_url, json=order_body, headers=headers, timeout=5)
        if not res.ok:
            logger.error(f"Failed to send order. {res.status_code} -- {res.text}")
            return update_status
        self.request_remaining = res.headers["X-Rate-Limit-Remaining"]
        self.request_next_cycle_in_seconds = res.headers["X-Rate-Limit-Reset"]
        update_status = True
        return update_status
