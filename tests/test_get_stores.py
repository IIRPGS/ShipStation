from ship_station import ShipStation
import unittest
from unittest.mock import patch, MagicMock
from validators import url

store_build_string = "stores"
expected_build_url = "https://ssapi.shipstation.com/stores/"
invalid_api_url = "https://api.shipstation.com/"
invalid_store_return = []


def get_ship_station_instance(ss_api_key="Fake Key", ss_api_secret="Fake Secret"):
    return ShipStation(ss_api_key, ss_api_secret)


class TestShipStationStores(unittest.TestCase):
    @patch("ship_station.requests")
    def test_get_all_stores(self, mock_request):
        ship_station = get_ship_station_instance()

        mock_res = MagicMock()
        expected_json_response = [
            {
                "storeId": 123,
                "storeName": "Bookstore",
                "marketplaceId": 123,
                "marketplaceName": "BigCommerce V3",
                "accountName": None,
                "email": None,
                "integrationUrl": "https://api.bigcommerce.com/stores",
                "active": True,
                "companyName": "",
                "phone": "123-456-789",
                "publicEmail": "",
                "website": "",
                "refreshDate": "2024-03-22T10:04:10.193",
                "lastRefreshAttempt": "2024-03-22T10:04:13.463",
                "createDate": "2022-09-29T09:10:30.707",
                "modifyDate": "2023-01-10T07:15:58.347",
                "autoRefresh": True,
                "statusMappings": None,
            },
            {
                "storeId": 456,
                "storeName": "Manual Orders",
                "marketplaceId": 456,
                "marketplaceName": "ShipStation",
                "accountName": None,
                "email": None,
                "integrationUrl": None,
                "active": True,
                "companyName": "",
                "phone": "",
                "publicEmail": "",
                "website": "",
                "refreshDate": "2024-03-05T10:55:55.67",
                "lastRefreshAttempt": "2024-03-05T10:56:05.503",
                "createDate": "2022-09-29T08:01:22.85",
                "modifyDate": "2022-11-17T08:11:29.353",
                "autoRefresh": True,
                "statusMappings": None,
            },
            {
                "storeId": 789,
                "storeName": "Salesforce Core Store",
                "marketplaceId": 789,
                "marketplaceName": "Salesforce Core",
                "accountName": None,
                "email": None,
                "integrationUrl": None,
                "active": True,
                "companyName": "",
                "phone": "",
                "publicEmail": "",
                "website": "",
                "refreshDate": "2024-03-22T11:07:59.453",
                "lastRefreshAttempt": "2024-03-22T11:08:01.06",
                "createDate": "2023-10-11T08:45:52.56",
                "modifyDate": "2024-03-22T11:07:59.877",
                "autoRefresh": True,
                "statusMappings": None,
            },
        ]
        mock_res.ok = True
        mock_res.json.return_value = expected_json_response
        mock_request.get.return_value = mock_res
        self.assertEqual(ship_station.get_all_stores(), expected_json_response)

    @patch("ship_station.requests")
    def test_get_all_stores_empty_response(self, mock_request):
        ship_station = get_ship_station_instance()

        mock_res = MagicMock()
        expected_json_response = []
        mock_res.ok = True
        mock_res.json.return_value = expected_json_response
        mock_request.get.return_value = mock_res
        self.assertEqual(ship_station.get_all_stores(), expected_json_response)

    @patch("ship_station.ShipStation.build_path_url")
    @patch("ship_station.requests")
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

    def test_validate_url_get_all_stores(self):
        ship_station = get_ship_station_instance()

        store_url = ship_station.build_path_url(store_build_string)
        self.assertEqual(store_url, expected_build_url)
        self.assertTrue(url(store_url))

    @patch("ship_station.ShipStation.build_path_url")
    def test_connection_error_get_stores(self, mock_url):
        ship_station = get_ship_station_instance()
        mock_url.return_value = invalid_api_url

        self.assertEqual(ship_station.get_all_stores(), invalid_store_return)

    def test_timeout_get_all_stores(self):
        ship_station = get_ship_station_instance()

        self.assertEqual(ship_station.get_all_stores(), invalid_store_return)

    @patch("ship_station.requests.get")
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
