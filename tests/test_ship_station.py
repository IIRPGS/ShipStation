from ship_station import ShipStation, ShipStationMeta
from unittest.mock import patch
import unittest
from validators import url


class TestShipStationMeta(unittest.TestCase):
    def test_init(self):
        ss_api_key = "Fake Key"
        ss_api_secret = "Fake Secret"
        ship_station = ShipStation(ss_api_key, ss_api_secret)
        self.assertTrue(isinstance(ship_station, ShipStationMeta))

        self.assertEqual(ship_station.api_key, ss_api_key)
        self.assertEqual(ship_station.api_secret, ss_api_secret)

        self.assertIn("Authorization", ship_station.authorization_header.keys())
        self.assertIsNot(ship_station.authorization_header["Authorization"], "Basic ")

        auth_header = ship_station.authorization_header["Authorization"]
        print(auth_header)


if __name__ == "__main__":
    unittest.main()
