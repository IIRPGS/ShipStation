from dataclasses import dataclass
from typing import Any


@dataclass
class ShipStationOrderResponse:
    def __init__(self, order_dict: list[dict[Any, dict[Any, Any]]]) -> None:
        self.orders = self.__map_order_ids_with_json(order_dict)
        self.is_empty = self.__has_empty_values()
        self.order_ids = self.__get_all_order_ids(order_dict)
        self.order_id_to_number_map = self.__map_order_id_to_order_number(order_dict)
        self.order_count = self.__get_order_count()

    orders: dict[str, dict[Any, Any] | None]
    order_ids: list[str]
    order_id_to_number_map: dict[str, str | None]
    order_count: int = 0
    is_empty: bool = True

    def __repr__(self) -> str:
        return str(self.order_ids)

    def __has_empty_values(self) -> bool:
        if not self.orders:
            return True
        for item in self.orders:
            if item:
                return False
        return True

    def __get_all_order_ids(
        self, order_dict: list[dict[str, dict[Any, Any]]]
    ) -> list[str]:
        try:
            return [str(order["orderId"]) for order in order_dict]
        except KeyError:
            return []
        except TypeError:
            return []

    def __map_order_ids_with_json(
        self, order_dict: list[dict[str, dict[Any, Any]]]
    ) -> dict[str, dict[Any, Any] | None]:
        try:
            return {str(order_info["orderId"]): order_info for order_info in order_dict}
        except KeyError:
            return {}
        except TypeError:
            return {}

    def __map_order_id_to_order_number(
        self, order_dict: list[dict[str, Any]]
    ) -> dict[str, str | None]:
        try:
            return {
                str(order_info["orderId"]): str(order_info["orderNumber"])
                for order_info in order_dict
            }
        except KeyError:
            return {}
        except TypeError:
            return {}

    def __get_order_count(self) -> int:
        return len(self.order_ids)

    def get_order_json(self, order_id: str) -> dict[Any, Any] | None:
        if not self.order_ids or order_id not in self.order_ids:
            return {}
        return self.orders[order_id]

    def get_order_number_id_map(self) -> dict[str, str | None]:
        try:
            return {k: v for k, v in self.order_id_to_number_map.items()}
        except KeyError:
            return {}

    def get_order_id(self, order_number: str) -> str:
        try:
            id_map = {v: k for k, v in self.order_id_to_number_map.items()}
            return id_map[order_number]
        except KeyError:
            return ""
