import unittest
from unittest.mock import MagicMock, patch

from validators import url

from ship_station.ship_station import ShipStation

store_build_string = "stores"
expected_build_url = "https://ssapi.shipstation.com/stores/"
invalid_api_url = "https://api.shipstation.com/"
invalid_store_return = []


def get_ship_station_instance(ss_api_key="Fake Key", ss_api_secret="Fake Secret"):
    return ShipStation(ss_api_key, ss_api_secret)


class TestShipStationStores(unittest.TestCase):
    
    @patch("ship_station.ship_station.ShipStation.build_path_url")
    @patch("ship_station.ship_station.requests")
    def test_build_url_get_all_stores(self, mock_request, mock_url):
        ship_station = get_ship_station_instance()

        expected_json = []

        mock_res = MagicMock()
        mock_res.status_code.return_value = 200
        mock_res.json.return_value = expected_json
        mock_res.ok = True
        mock_request.get.return_value = mock_res

        ship_station.get_all_stores()
        mock_url.assert_called_once()
        self.assertEqual(store_build_string, mock_url.call_args[0][0])

    @patch("ship_station.ship_station.requests.get")
    def test_failed_request_to_get_all_stores(self, mock_request):
        ship_station = get_ship_station_instance()

        expected_json = invalid_store_return

        mock_res = MagicMock()
        mock_res.status_code.return_value = 404
        mock_res.json.return_value = expected_json
        mock_res.ok = False
        mock_request.return_value = mock_res

        self.assertEqual(ship_station.get_all_stores(), invalid_store_return)
        mock_request.assert_called_once()


if __name__ == "__main__":
    unittest.main()
