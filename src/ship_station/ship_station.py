import base64
from dataclasses import dataclass
from typing import Any, Annotated

import requests
from requests.exceptions import ReadTimeout, ConnectionError
from loguru import logger
from .order_response import ShipStationOrderResponse


@dataclass
class ShipStationMeta:
    """
    Dataclass for holding meta information about the ShipStation API
    and current instance's request limits

    Attributes:
        rate_limit_headers: (list) Request headers.
                Used to keep track of request limits
        route_map: (dict) Used to retrieve api resource paths.
                Key is the simplified name,
                Value is the url path
        order_status_able_to_be_updated: (list)
                Order statuses that can be
                changed/updated by the api
        remove_order_keys_before_updating: (list)
                Keys from an order call
                that need to be removed before updating an order.
                See child function update_order_notes for reasoning
        host: (str) the host url for the ShipStation API
        request_remaining: (int) number of requests remaning in current api cycle
        request_next_cycle_in_seconds: (int)
            Amount of seconds before the request cycle refreshes

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
        "order_hold": "/orders/holduntil/",
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

    def __remove_basic_in_auth_string(self, auth_string: str) -> str:
        if "Basic" in auth_string:
            auth_string = auth_string.replace("Basic ", "")
        return auth_string

    def __decode_b64_auth_string(self, auth_string: str) -> list[str]:
        decoded_string = base64.standard_b64decode(auth_string).decode("utf-8")
        return decoded_string.split(":")

    def authorize_request(self, auth_string: str) -> bool:
        """
        Checks if the given key matches instance's saved key + secret combo
            :param auth_string: Base64 encoded string given by ShipStation
        Returns True/False if the given string matchs the instance's

        Decoded string format {api_key}:{api_secret}
        """
        is_authorized = False

        auth_string = self.__remove_basic_in_auth_string(auth_string)
        decoded_string = self.__decode_b64_auth_string(auth_string)

        if len(decoded_string) < 2:
            logger.error("Authorization Failed: decoded auth key has length < 2")
            return is_authorized

        given_key = decoded_string[0]
        given_secret = decoded_string[1]

        if given_key != self.api_key and given_secret != self.api_secret:
            logger.error("Authorization Failed: Given information is invalid")
            return is_authorized
        return True

    def __build_authorization_header(self):
        """
        Internal function to create the authorization header needed for API requests

        Runs on init and saves to self.authorization_header
        """
        auth_key_base64 = base64.b64encode(
            f"{self.api_key}:{self.api_secret}".encode("utf-8")
        ).decode("utf-8")
        self.authorization_header = {"Authorization": f"Basic {auth_key_base64}"}

    def create_webhook_subscription(
        self,
        target_url: str,
        event: str = "ORDER_NOTIFY",
        store_id: str = "",
        friendly_name: str = "",
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
        try:
            res = requests.post(
                webhook_url, json=event_body, headers=headers, timeout=3
            )
        except ReadTimeout as rt:
            logger.error(f"Timeout on {webhook_url} -- {rt}")
            return False
        except ConnectionError as connect_error:
            logger.error(
                f"Invalid connection attempted {webhook_url} -- {connect_error}"
            )
            return False
        if not res.ok:
            logger.error(f"Failed to make webhook: {res.status_code} -- {res.text}")
            return False
        logger.success(f"Webhook created: {res.json()}")
        return True

    def get_webhooks(
        self,
    ) -> Annotated[
        Any,
        "JSON like object, typically reponse from request library. On failure returns list with empty dict",
    ]:
        """
        Lists all webhook subscriptions in the ShipStation instance
        Returns all subscriptions in ShipStation account. Dict format
        """
        if self.api_limit_at_max():
            logger.error(
                f"API limit reached. Try again after {self.request_next_cycle_in_seconds} seconds"
            )
            return []
        webhook_url = self.build_path_url("webhooks")
        try:
            res = requests.get(
                webhook_url, headers=self.authorization_header, timeout=3
            )
        except ReadTimeout as timeout:
            logger.error(f"Timeout when calling {webhook_url} -- {timeout}")
            return []
        except ConnectionError as connect_error:
            logger.error(
                f"Invalid connection attempted {webhook_url} -- {connect_error}"
            )
            return []
        if not res.ok:
            logger.error(f"Failed to get webhook lists {res.status_code} -- {res.text}")
            return []
        webhook_list = res.json()["webhooks"]
        return webhook_list

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
        try:
            res = requests.delete(
                webhook_url, headers=self.authorization_header, timeout=3
            )
        except ReadTimeout as timeout:
            logger.error(f"Timeout when calling {webhook_url} -- {timeout}")
            return False
        except ConnectionError as connect_error:
            logger.error(
                f"Invalid connection attempted {webhook_url} -- {connect_error}"
            )
            return False
        if not res.ok:
            logger.error(f"Failed to get webhook lists {res.status_code} -- {res.text}")
            return False
        return True

    def get_all_stores(self, show_inactive_stores: bool = False) -> Annotated[
        Any,
        "JSON like object, typically reponse from request library. On failure returns empty list of dict",
    ]:
        """
        Retrieve all stores in a ShipStation instance
            :param show_inactive_stores: True if results should have inactive stores, false if not
        Returns a list of dictionaries with all store information
        """
        stores_url = self.build_path_url("stores")
        params = {"showInactive": show_inactive_stores}
        try:
            res = requests.get(
                stores_url, params=params, headers=self.authorization_header, timeout=3
            )
        except ReadTimeout as timeout:
            logger.error(f"Timeout when calling {stores_url} -- {timeout}")
            return []
        except ConnectionError as connect_error:
            logger.error(
                f"Invalid connection attempted {stores_url} -- {connect_error}"
            )
            return []
        if not res.ok:
            logger.error(f"Failed to get stores URL: {res.reason} -- {res.text}")
            return []
        self.__update_api_limits(
            int(res.headers["X-Rate-Limit-Remaining"]),
            int(res.headers["X-Rate-Limit-Reset"]),
        )
        return res.json()

    def get_order(self, order_id: str) -> ShipStationOrderResponse:
        """
        Attempts to get a single order given an order ID
            :param order_id: The order ID to search for
            :param custom_params: any custom fields to filter the request by
        Returns a list of dicts containing the order information
        """
        order_url = self.build_path_url("orders") + str(order_id)
        try:
            res = requests.get(order_url, headers=self.authorization_header, timeout=3)
        except ReadTimeout as timeout:
            logger.error(f"Timeout when calling {order_url} -- {timeout}")
            return ShipStationOrderResponse([])
        except ConnectionError as connect_error:
            logger.error(f"Invalid connection attempted {order_id} -- {connect_error}")
            return ShipStationOrderResponse([])
        if not res.ok:
            logger.error(
                f"Failed to get order {str(order_id)}: {res.status_code} -- {res.text}"
            )
            return ShipStationOrderResponse([])
        self.__update_api_limits(
            int(res.headers["X-Rate-Limit-Remaining"]),
            int(res.headers["X-Rate-Limit-Reset"]),
        )
        return ShipStationOrderResponse([res.json()])

    def get_order_by_order_number(self, order_number: str) -> ShipStationOrderResponse:
        """
        Returns a list of orders given an order number
            :param order_number: order number to search for
        Returns a list of dictionaries containing order details
        """
        order = self.get_all_orders(custom_params={"orderNumber": order_number})
        if not order:
            logger.error(f"Failed to get order with order number {order_number}")
            return order
        return order

    def api_limit_at_max(self) -> bool:
        """
        Checks if the instance has reached it's max request in current cycle
        Returns True if instance cannot make a request, False if it can
        """
        return int(self.request_remaining) <= 0

    def get_all_orders(
        self, custom_params: dict[str, Any] = {}
    ) -> ShipStationOrderResponse:
        """
        Get all orders in a ShipStation Instance
            :param custom_params: Custom filters for retrieving orders
        Returns
        """
        order_url = self.build_path_url("orders")
        params = custom_params
        try:
            res = requests.get(
                order_url, params=params, headers=self.authorization_header, timeout=3
            )
        except ReadTimeout as timeout:
            logger.error(f"Timeout when calling {order_url} -- {timeout}")
            return ShipStationOrderResponse([])
        except ConnectionError as connect_error:
            logger.error(f"Invalid connection attempted {order_url} -- {connect_error}")
            return ShipStationOrderResponse([])
        if not res.ok:
            logger.error(f"Failed to get all orders: {res.status_code} -- {res.text}")
            return ShipStationOrderResponse([])
        self.__update_api_limits(
            int(res.headers["X-Rate-Limit-Remaining"]),
            int(res.headers["X-Rate-Limit-Reset"]),
        )
        order_detail = ShipStationOrderResponse(res.json()["orders"])
        return order_detail

    def get_waiting_orders(
        self, status: str = "awaiting_shipment"
    ) -> ShipStationOrderResponse:
        """
        Gets all orders with a specific status
            :param status: status of orders to look for
        Returns dictionary containing all order information
        """
        order = self.get_all_orders(custom_params={"orderStatus": status})
        if not order:
            logger.error(f"Unable to get orders with {status} status")
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
        elif orders.order_count >= 2:
            logger.warning(
                f"Ambiguous number of orders for order number {order_number}"
            )
        return list(orders.order_ids)

    def is_order_able_to_be_updated(self, order_json: Any) -> bool:
        """
        Determines if the given order is able to be updated
            :param order_json: order information from the ShipStation API in json/dict format
        Returns True if the order is able to be updated. False otherwise
        """
        if "orderStatus" in order_json:
            order_status = order_json["orderStatus"]
            return order_status in self.order_status_able_to_be_updated
        else:
            return False

    def __remove_invalid_order_keys(self, order_body: Any) -> dict[Any, Any]:
        """
        Removes any keys not needed to update an order in ShipStation
            :param order_body: the order information recieved by the ShipStation API
        Returns the original dictionary without any of the keys that can't be proceesed by the update order API
        """
        return {
            k: v
            for k, v in order_body.items()
            if k not in self.remove_order_keys_before_updating
        }

    def update_order_custom_note(
        self,
        order_body: dict[Any, Any],
        custom_note_key: str,
        custom_note_str: str,
        custom_note_parent_key: str = "advancedOptions",
    ) -> dict[Any, Any]:
        """
        Updates the custom note sections of the order json
            :param order_body: the json body to update/return after updating
            :param custom_note_key: the dict key to update the
        """
        order_body[custom_note_parent_key][custom_note_key] = custom_note_str
        return order_body

    def __pre_update_order_checks(self, order: ShipStationOrderResponse) -> bool:
        """
        Internal function used to ensure order can be updated:
            Checks:
                - If the order response is empty
                - If the api limit has been reached
                - Does the order have a status that is able to be updated
        """
        if order.is_empty:
            logger.error(f"Unable to get order {order}")
            return False
        if self.api_limit_at_max():
            logger.error(
                f"API limit reached. Try again after {self.request_next_cycle_in_seconds} seconds -- order {order}"
            )
            return False
        for _, single_order in order.orders.items():
            print(single_order["orderStatus"])
            if not self.is_order_able_to_be_updated(single_order):
                order_status = single_order["orderStatus"]
                order_number = single_order["orderNumber"]
                logger.error(
                    f"Order is not able to be updated in {order_status} status -- {order_number}"
                )
                return False
        return True

    def __update_api_limits(
        self, request_remaining: int, seconds_before_cycle_reset: int
    ) -> bool:
        """
        Internal function for updating the remaining limits and API cycle
            :param request_remaining: the number of request remaining in this cycle
            :param seconds_before_cycle_reset: the number of seconds remaining before the API limit resets
        Returns true if the internal counters were updated, False if not
        """
        try:
            self.request_remaining = request_remaining
            self.request_next_cycle_in_seconds = seconds_before_cycle_reset
        except Exception as e:
            logger.error("Failed to update API limits", e)
            return False
        return True

    def update_order_notes(
        self,
        order_id: str,
        internal_note: str,
        custom_note: str = "",
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
        if not self.__pre_update_order_checks(order=order):
            return update_status
        order_body = self.__remove_invalid_order_keys(order.orders)
        order_body["internalNotes"] = internal_note
        if custom_note:
            order_body = self.update_order_custom_note(
                order_body=order_body,
                custom_note_key="customField",
                custom_note_str=custom_note,
            )
        if custom_note2:
            order_body = self.update_order_custom_note(
                order_body=order_body,
                custom_note_key="customField2",
                custom_note_str=custom_note2,
            )
        if custom_note3:
            order_body = self.update_order_custom_note(
                order_body=order_body,
                custom_note_key="customField3",
                custom_note_str=custom_note3,
            )
        order_url = self.build_path_url("order_update")
        headers = self.authorization_header | {"Content-Type": "application/json"}
        try:
            res = requests.post(order_url, json=order_body, headers=headers, timeout=3)
        except ReadTimeout as timeout:
            logger.error(f"Timeout when calling {order_url} -- {timeout}")
            return update_status
        except ConnectionError as connect_error:
            logger.error(f"Invalid connection attempted {order_url} -- {connect_error}")
            return update_status
        if not res.ok:
            logger.error(f"Failed to send order. {res.status_code} -- {res.text}")
            return update_status
        self.__update_api_limits(
            int(res.headers["X-Rate-Limit-Remaining"]),
            int(res.headers["X-Rate-Limit-Reset"]),
        )
        return True

    def hold_order(
        self, order_id: int, hold_until_date: Annotated[str, "Format: YYYY-MM-DD"]
    ) -> bool:
        """
        Does not check if order exists
        """
        order_url = self.build_path_url("order_hold")
        headers = self.authorization_header | {"Content-Type": "application/json"}
        order_body = {"orderID": order_id, "holdUntilDate": hold_until_date}
        try:
            res = requests.post(order_url, json=order_body, headers=headers, timeout=3)
        except ReadTimeout as timeout:
            logger.error(f"Timeout when calling {order_url} -- {timeout}")
            return False
        except ConnectionError as connect_error:
            logger.error(f"Invalid connection attempted {order_url} -- {connect_error}")
            return False
        if not res.ok:
            logger.error(f"Failed to send order. {res.status_code} -- {res.text}")
            return False
        self.__update_api_limits(
            int(res.headers["X-Rate-Limit-Remaining"]),
            int(res.headers["X-Rate-Limit-Reset"]),
        )
        return True
