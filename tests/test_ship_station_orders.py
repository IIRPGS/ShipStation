from ship_station import ShipStation, ShipStationOrderResponse
import unittest
from unittest.mock import patch, MagicMock
from validators import url

order_build_string = "orders"
update_order_build_string = "order_update"
expected_order_url = "https://ssapi.shipstation.com/orders/"
expected_update_order_url = "https://ssapi.shipstation.com/orders/createorder/"
invalid_order_url = "https://ssapi.shipstation.com"
invalid_api_url = "https://api.shipstation.com/"
invalid_order_return = ShipStationOrderResponse([])


def get_ship_station_instance(ss_api_key="Fake Key", ss_api_secret="Fake Secret"):
    return ShipStation(ss_api_key, ss_api_secret)


class TestShipStationStores(unittest.TestCase):
    def test_validate_url_get_order(self):
        ship_station = get_ship_station_instance()

        order_url = ship_station.build_path_url(order_build_string)
        self.assertEqual(order_url, expected_order_url)
        self.assertTrue(url(order_url))

    def test_validate_url_get_order_with_id(self):
        ship_station = get_ship_station_instance()
        order_id = "5678"

        order_url = ship_station.build_path_url(order_build_string, order_id)
        self.assertEqual(order_url, expected_order_url + order_id)
        self.assertTrue(url(order_url))

    def test_validate_url_update_order(self):
        ship_station = get_ship_station_instance()

        order_url = ship_station.build_path_url(update_order_build_string)
        self.assertEqual(order_url, expected_update_order_url)
        self.assertTrue(url(order_url))

    def test_validate_url_update_order_with_id(self):
        ship_station = get_ship_station_instance()
        order_id = "1234"

        order_url = ship_station.build_path_url(update_order_build_string, order_id)
        self.assertEqual(order_url, expected_update_order_url + order_id)
        self.assertTrue(url(order_url))


if __name__ == "__main__":
    unittest.main()
