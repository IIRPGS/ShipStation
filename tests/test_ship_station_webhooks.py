from ship_station import ShipStation
from unittest.mock import patch, MagicMock
import unittest
from validators import url


get_webhook_build_string = "webhooks"
subscribe_to_webhook_build_string = "webhook_subscribe"
delete_webhook_build_string = "webhook_delete"
expected_delete_webhook_url = expected_webhook_url = (
    "https://ssapi.shipstation.com/webhooks/"
)
expected_subscribe_webhook_url = "https://ssapi.shipstation.com/webhooks/subscribe/"


def get_ship_station_instance(ss_api_key="Fake Key", ss_api_secret="Fake Secret"):
    return ShipStation(ss_api_key, ss_api_secret)


class TestShipStationWebhook(unittest.TestCase):

    def test_validate_url_get_webhooks(self):
        ship_station = get_ship_station_instance()

        get_webhook_url = ship_station.build_path_url(get_webhook_build_string)
        self.assertEqual(get_webhook_url, expected_webhook_url)
        self.assertTrue(url(get_webhook_url))

    def test_validate_url_subscribe_to_webhook(self):
        ship_station = get_ship_station_instance()

        sub_webhook_url = ship_station.build_path_url(subscribe_to_webhook_build_string)
        self.assertEqual(sub_webhook_url, expected_subscribe_webhook_url)
        self.assertTrue(url(sub_webhook_url))

    def test_validate_url_subscribe_to_webhook(self):
        ship_station = get_ship_station_instance()

        delete_webhook_url = ship_station.build_path_url(delete_webhook_build_string)
        self.assertEqual(delete_webhook_url, expected_delete_webhook_url)
        self.assertTrue(url(delete_webhook_url))

    @patch("ship_station.requests")
    def test_successful_webhook_subscription(self, mock_request):
        ship_station = get_ship_station_instance()

        mock_res = MagicMock()
        expected_json_response = {"id": 30686}
        callback_url = "https://hello-world.org"
        mock_res.ok = True
        mock_res.json.return_value = expected_json_response
        mock_request.post.return_value = mock_res

        subscription_status = ship_station.create_webhook_subscription(callback_url)
        self.assertTrue(subscription_status)

    @patch("ship_station.requests")
    def test_failed_webhook_subscription(self, mock_request):
        ship_station = get_ship_station_instance()

        mock_res = MagicMock()
        callback_url = "https://hello-world.org"
        mock_res.ok = False
        mock_request.post.return_value = mock_res

        subscription_status = ship_station.create_webhook_subscription(callback_url)
        self.assertFalse(subscription_status)

    def test_overloaded_webhook_subscription(self):
        ship_station = get_ship_station_instance()

        ship_station.request_remaining = 0
        callback_url = "https://hello-world.org"

        subscription_status = ship_station.create_webhook_subscription(callback_url)
        self.assertFalse(subscription_status)

    @patch("ship_station.requests")
    def test_invalid_auth_webhook_subscription(self, mock_request):
        ship_station = get_ship_station_instance()

        mock_res = MagicMock()
        callback_url = "https://hello-world.org"
        mock_res.status_code.return_value = 401
        mock_res.ok = False
        mock_request.post.return_value = mock_res

        subscription_status = ship_station.create_webhook_subscription(callback_url)
        self.assertFalse(subscription_status)

    @patch("ship_station.requests")
    def test_webhook_subscription_with_optional_details(self, mock_request):
        ship_station = get_ship_station_instance()

        mock_res = MagicMock()
        callback_url = "https://hello-world.org"
        mock_res.status_code.return_value = 201
        expected_json_response = {"id": 12345}
        mock_res.json.return_value = expected_json_response
        mock_res.ok = True
        mock_request.post.return_value = mock_res

        store_id = "56789"
        friendly_name = "Test Name"
        event_type = "FULFILLMENT_SHIPPED"

        subscription_status = ship_station.create_webhook_subscription(
            callback_url,
            event=event_type,
            store_id=store_id,
            friendly_name=friendly_name,
        )
        self.assertTrue(subscription_status)

    def test_timeout_webhook_subscription(self):
        ship_station = get_ship_station_instance()
        callback_url = "https:123.com/"

        self.assertFalse(ship_station.create_webhook_subscription(callback_url))

    @patch("ship_station.ShipStation.build_path_url")
    def test_build_url_webhook_subscription(self, mock_url):
        ship_station = get_ship_station_instance()
        expected_build_url = "https://ssapi.shipstation.com/webhooks/"
        mock_url.return_value = expected_build_url

        self.assertEqual(expected_build_url, ship_station.build_path_url("webhook"))

    @patch("ship_station.ShipStation.build_path_url")
    def test_url_build_webhook_subscription(self, mock_url):
        ship_station = get_ship_station_instance()
        expected_build_url = "https://api.shipstation.com/webhooks/"
        mock_url.return_value = expected_build_url

        callback_url = "https:123.com/"

        self.assertFalse(ship_station.create_webhook_subscription(callback_url))

    @patch("ship_station.requests")
    def test_get_webooks(self, mock_request):
        ship_station = get_ship_station_instance()
        expected_json = {
            "webhooks": [
                {
                    "IsLabelAPIHook": False,
                    "WebHookID": 30704,
                    "SellerID": 4215589,
                    "StoreID": None,
                    "HookType": "ORDER_NOTIFY",
                    "MessageFormat": "Json",
                    "Url": "https://58d7-216-164-127-92.ngrok-free.app/",
                    "Name": "",
                    "BulkCopyBatchID": None,
                    "BulkCopyRecordID": None,
                    "Active": True,
                    "SerializedHeaders": None,
                    "WebhookLogs": [],
                    "Seller": None,
                    "Store": None,
                }
            ]
        }
        mock_res = MagicMock()
        mock_res.status_code.return_value = 200
        mock_res.json.return_value = expected_json
        mock_res.ok = True
        mock_request.get.return_value = mock_res
        recieved_res = ship_station.get_webhooks()
        self.assertEqual(recieved_res, expected_json["webhooks"])

    @patch("ship_station.requests")
    def test_empty_get_webhook_list(self, mock_request):
        ship_station = get_ship_station_instance()

        expected_json = {"webhooks": []}
        mock_res = MagicMock()
        mock_res.status_code.return_value = 200
        mock_res.json.return_value = expected_json
        mock_res.ok = True
        mock_request.get.return_value = mock_res
        recieved_res = ship_station.get_webhooks()
        self.assertEqual(recieved_res, expected_json["webhooks"])

    def test_overloaded_webhook_list(self):
        ship_station = get_ship_station_instance()

        ship_station.request_remaining = 0
        self.assertEqual(ship_station.get_webhooks(), [])

    def test_timeout_get_webhook_list(self):
        ship_station = get_ship_station_instance()

        self.assertEqual(ship_station.get_webhooks(), [])

    @patch("ship_station.ShipStation.build_path_url")
    def test_url_build_webhook_list(self, mock_url):
        ship_station = get_ship_station_instance()
        expected_build_url = "https://ssapi.shipstation.com/webhooks/"
        mock_url.return_value = expected_build_url

        self.assertEqual(expected_build_url, ship_station.build_path_url("webhook"))

    @patch("ship_station.ShipStation.build_path_url")
    def test_invalid_url_webhook_list(self, mock_url):
        ship_station = get_ship_station_instance()
        invalid_build_url = "https://api.shipstation.com/"
        mock_url.return_value = invalid_build_url

        self.assertFalse(ship_station.get_webhooks())

    @patch("ship_station.requests")
    def test_failed_request_get_webhook_list(self, mock_request):
        ship_station = get_ship_station_instance()

        expected_json = {"webhooks": []}
        mock_res = MagicMock()
        mock_res.status_code.return_value = 404
        mock_res.json.return_value = expected_json
        mock_res.ok = False
        mock_request.get.return_value = mock_res
        recieved_res = ship_station.get_webhooks()
        self.assertEqual(recieved_res, expected_json["webhooks"])

    @patch("ship_station.requests")
    def test_delete_webhook(self, mock_request):
        ship_station = get_ship_station_instance()
        webhook_id = "12345"

        mock_res = MagicMock()
        mock_res.status_code.return_value = 200
        mock_res.ok = True
        mock_request.delete.return_value = mock_res
        self.assertTrue(ship_station.delete_webhook(webhook_id))

    @patch("ship_station.requests")
    def test_failed_request_delete_webhook(self, mock_request):
        ship_station = get_ship_station_instance()
        webhook_id = "12345"

        mock_res = MagicMock()
        mock_res.status_code.return_value = 404
        mock_res.ok = False
        mock_request.delete.return_value = mock_res
        self.assertFalse(ship_station.delete_webhook(webhook_id))

    def test_overloaded_delete_webhook(self):
        ship_station = get_ship_station_instance()
        webhook_id = "12345"
        ship_station.request_remaining = 0

        self.assertFalse(ship_station.delete_webhook(webhook_id))

    @patch("ship_station.ShipStation.build_path_url")
    def test_url_build_delete_webhook(self, mock_url):
        ship_station = get_ship_station_instance()
        expected_build_url = "https://ssapi.shipstation.com/webhooks/"
        mock_url.return_value = expected_build_url
        self.assertEqual(
            expected_build_url, ship_station.build_path_url("webhook_delete")
        )

    @patch("ship_station.ShipStation.build_path_url")
    def test_invalid_url_delete_webhook(self, mock_url):
        ship_station = get_ship_station_instance()
        invalid_build_url = "https://api.shipstation.com/"
        mock_url.return_value = invalid_build_url
        webhook_id = "12345"

        self.assertFalse(ship_station.delete_webhook(webhook_id))

    def test_timeout_delete_webhook(self):
        ship_station = get_ship_station_instance()
        webhook_id = "12345"

        self.assertFalse(ship_station.delete_webhook(webhook_id))


if __name__ == "__main__":
    unittest.main()
