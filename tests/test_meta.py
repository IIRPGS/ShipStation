from ship_station.ship_station import ShipStationMeta
import unittest
from validators import url


class TestShipStationMeta(unittest.TestCase):
    def test_init(self):
        meta_instance = ShipStationMeta()
        self.assertIsInstance(meta_instance, ShipStationMeta)
        self.assertEqual(meta_instance.host, "ssapi.shipstation.com")
        self.assertEqual(meta_instance.request_remaining, 40)
        self.assertEqual(meta_instance.request_next_cycle_in_seconds, 60)

        self.assertFalse("completed" in meta_instance.order_status_able_to_be_updated)
        self.assertTrue(
            "awaiting_shipment" in meta_instance.order_status_able_to_be_updated
        )

        self.assertIn("X-Rate-Limit-Limit", meta_instance.rate_limit_headers)
        self.assertEqual(len(meta_instance.rate_limit_headers), 3)

        self.assertIn("stores", meta_instance.route_map)
        self.assertFalse("webhook_unsubscribe" in meta_instance.route_map)

        self.assertTrue("userId" in meta_instance.remove_order_keys_before_updating)
        self.assertNotIn("orderId", meta_instance.remove_order_keys_before_updating)

    def test_build_path(self):
        meta_instance = ShipStationMeta()
        self.assertIsInstance(meta_instance, ShipStationMeta)
        base_url = "https://ssapi.shipstation.com"

        self.assertTrue("webhooks" in meta_instance.route_map)

        order_url = meta_instance.build_path_url("orders")
        expected_order_path = "/orders/"
        self.assertEqual(order_url, f"{base_url}{expected_order_path}")

        order_number = "1234"
        order_url_with_params = meta_instance.build_path_url(
            "order_update", order_number
        )
        expected_path = "/orders/createorder/"
        self.assertEqual(
            order_url_with_params,
            f"{base_url}{expected_path}{order_number}",
        )

        invalid_update_key = "hello_world"
        expected_invalid_path = "/hello/world/"
        self.assertEqual(meta_instance.build_path_url(invalid_update_key), base_url)
        self.assertEqual(
            meta_instance.build_path_url(invalid_update_key, expected_invalid_path),
            f"{base_url}{expected_invalid_path}",
        )

        webhook_url = meta_instance.build_path_url("webhooks")
        self.assertTrue(url(webhook_url))

        webhook_path = "/fake/path/"
        webhook_url_with_params = meta_instance.build_path_url(
            "webhook_subscribe", webhook_path
        )
        self.assertTrue(url(webhook_url_with_params))


if __name__ == "__main__":
    unittest.main()
