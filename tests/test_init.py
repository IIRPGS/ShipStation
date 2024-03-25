from ship_station.ship_station import ShipStation, ShipStationMeta
import unittest
from copy import deepcopy


class TestShipStationInit(unittest.TestCase):
    def test_init(self):
        ss_api_key = "Fake Key"
        ss_api_secret = "Fake Secret"
        ship_station = ShipStation(ss_api_key, ss_api_secret)
        self.assertTrue(isinstance(ship_station, ShipStationMeta))

        self.assertEqual(ship_station.api_key, ss_api_key)
        self.assertEqual(ship_station.api_secret, ss_api_secret)

    def test_authorize_request(self):
        ss_api_key = "Fake Key"
        ss_api_secret = "Fake Secret"
        ship_station = ShipStation(ss_api_key, ss_api_secret)
        self.assertIn("Authorization", ship_station.authorization_header.keys())

        auth_header = deepcopy(ship_station.authorization_header["Authorization"])
        ship_station._ShipStation__build_authorization_header()
        new_header = ship_station.authorization_header["Authorization"]

        self.assertEqual(auth_header, new_header)
        self.assertFalse(
            "Basic"
            in ship_station._ShipStation__remove_basic_in_auth_string(auth_header)
        )
        self.assertTrue(ship_station.authorize_request(auth_header))
        self.assertTrue(ship_station.authorize_request(new_header))

    def test_api_limits(self):
        ss_api_key = "Fake Key"
        ss_api_secret = "Fake Secret"
        ship_station = ShipStation(ss_api_key, ss_api_secret)

        self.assertFalse(ship_station.api_limit_at_max())

        no_request_number = 0
        self.assertTrue(
            ship_station._ShipStation__update_api_limits(
                no_request_number, no_request_number
            )
        )


if __name__ == "__main__":
    unittest.main()
