from ship_station.ship_station import ShipStation
from ship_station.order_response import ShipStationOrderResponse
import unittest
from unittest.mock import patch, MagicMock
from validators import url

order_build_string = "orders"
update_order_build_string = "order_update"
expected_order_url = "https://ssapi.shipstation.com/orders/"
expected_update_order_url = "https://ssapi.shipstation.com/orders/createorder/"
invalid_order_url = "https://ssapi.shipstation.com/"
invalid_api_url = "https://api.shipstation.com/"
invalid_order_return = ShipStationOrderResponse([])

def get_ship_station_instance(ss_api_key="Fake Key", ss_api_secret="Fake Secret"):
    return ShipStation(ss_api_key, ss_api_secret)


class TestShipStationStores(unittest.TestCase):
    def test_get_order_url_validation(self):
        ship_station = get_ship_station_instance()

        order_url = ship_station.build_path_url(order_build_string)
        self.assertEqual(order_url, expected_order_url)
        self.assertTrue(url(order_url))

    def test_get_order_url_validation_with_ids(self):
        ship_station = get_ship_station_instance()
        order_id = "5678"

        order_url = ship_station.build_path_url(order_build_string, order_id)
        self.assertEqual(order_url, expected_order_url + order_id)
        self.assertTrue(url(order_url))

    @patch("ship_station.ship_station.requests")
    def test_get_order(self, mock_request):
        ship_station = get_ship_station_instance()

        mock_res = MagicMock()

        order_id = "390639144"
        expected_json = get_valid_single_order_json(order_id=int(order_id))
        mock_res.ok = True
        mock_res.status_code = 200
        mock_res.json.return_value = expected_json
        mock_request.get.return_value = mock_res

        order_res = ship_station.get_order(order_id)

        self.assertTrue(isinstance(order_res, ShipStationOrderResponse))
        self.assertTrue(order_id in order_res.order_ids)
        self.assertEqual(expected_json, order_res.orders[order_id])

    @patch("ship_station.ship_station.requests")
    def test_get_order_with_bad_status_code(self, mock_request):
        ship_station = get_ship_station_instance()

        order_id = "12345"
        empty_orders = {}
        mock_res = MagicMock()
        mock_res.status_code.return_value = 404
        mock_res.ok = False
        mock_request.get.return_value = mock_res

        order_res = ship_station.get_order(order_id)
        self.assertTrue(isinstance(order_res, ShipStationOrderResponse))
        self.assertTrue(order_res.is_empty)
        self.assertEqual(order_res.orders, empty_orders)

    @patch("ship_station.ship_station.ShipStation.build_path_url")
    def test_get_order_with_timeout(self, mock_url):
        ship_station = get_ship_station_instance()

        order_id = "12345"
        empty_orders = {}

        mock_url.return_value = invalid_order_url + ":81"

        order_res = ship_station.get_order(order_id)
        self.assertTrue(isinstance(order_res, ShipStationOrderResponse))
        self.assertTrue(order_res.is_empty)
        self.assertEqual(order_res.orders, empty_orders)

    @patch("ship_station.ship_station.ShipStation.build_path_url")
    def test_get_order_with_invalid_url(self, mock_url):
        ship_station = get_ship_station_instance()
        empty_orders = {}
        order_id = "99995"
        mock_url.return_value = invalid_order_url[:-1]

        order_res = ship_station.get_order(order_id)
        self.assertTrue(isinstance(order_res, ShipStationOrderResponse))
        self.assertTrue(order_res.is_empty)
        self.assertEqual(order_res.orders, empty_orders)


def get_valid_single_order_json(order_id: int = 390639144):
    # Single order item, recieved in get_order function
    return {
        "orderId": order_id,
        "orderNumber": "0001234",
        "orderKey": "00045678",
        "orderDate": "2024-03-19T08:09:13.9000000",
        "createDate": "2024-03-19T08:09:14.1100000",
        "modifyDate": "2024-03-19T08:41:07.5930000",
        "paymentDate": None,
        "shipByDate": None,
        "orderStatus": "awaiting_shipment",
        "customerId": 123456789,
        "customerUsername": "asd90wsdf09j1",
        "customerEmail": "jd@does.hoes",
        "billTo": {
            "name": "John Doe",
            "company": "Company Name",
            "street1": None,
            "street2": "",
            "street3": "",
            "city": None,
            "state": None,
            "postalCode": None,
            "country": None,
            "phone": "(123) 234-2345",
            "residential": None,
            "addressVerified": None,
        },
        "shipTo": {
            "name": "John Doe",
            "company": "Company Name",
            "street1": "123 Maple Street",
            "street2": "",
            "street3": "",
            "city": "NYC",
            "state": "NY",
            "postalCode": "12345-1234",
            "country": "US",
            "phone": "(123) 456-6890",
            "residential": True,
            "addressVerified": "Address validated successfully",
        },
        "items": [
            {
                "orderItemId": 635755895,
                "lineItemKey": "0000084006",
                "sku": "278",
                "name": "Test Item",
                "imageUrl": "https://google.com/",
                "weight": {"value": 1.0, "units": "ounces", "WeightUnits": 1},
                "quantity": 1,
                "unitPrice": 3.0,
                "taxAmount": 0.0,
                "shippingAmount": 0.0,
                "warehouseLocation": None,
                "options": [],
                "productId": 17122365,
                "fulfillmentSku": None,
                "adjustment": False,
                "upc": None,
                "createDate": "2024-03-19T08:09:13.9",
                "modifyDate": "2024-03-19T08:09:13.9",
            }
        ],
        "orderTotal": 11.0,
        "amountPaid": 0.0,
        "taxAmount": 0.0,
        "shippingAmount": 0.0,
        "customerNotes": None,
        "internalNotes": "Here are the shipping instructions.",
        "gift": False,
        "giftMessage": None,
        "paymentMethod": None,
        "requestedShippingService": None,
        "carrierCode": "ups_walleted",
        "serviceCode": "ups_ground",
        "packageCode": "package",
        "confirmation": "none",
        "shipDate": None,
        "holdUntilDate": None,
        "weight": {"value": 5.5, "units": "ounces", "WeightUnits": 1},
        "dimensions": None,
        "insuranceOptions": {
            "provider": None,
            "insureShipment": False,
            "insuredValue": 0.0,
        },
        "internationalOptions": {
            "contents": None,
            "customsItems": None,
            "nonDelivery": None,
        },
        "advancedOptions": {
            "warehouseId": 40988765,
            "nonMachinable": False,
            "saturdayDelivery": False,
            "containsAlcohol": False,
            "mergedOrSplit": True,
            "mergedIds": [390645692],
            "parentId": None,
            "storeId": 7098765,
            "customField1": None,
            "customField2": None,
            "customField3": None,
            "source": None,
            "billToParty": "my_other_account",
            "billToAccount": None,
            "billToPostalCode": None,
            "billToCountryCode": None,
            "billToMyOtherAccount": 808071,
        },
        "tagIds": None,
        "userId": None,
        "externallyFulfilled": False,
        "externallyFulfilledBy": None,
        "externallyFulfilledById": None,
        "externallyFulfilledByName": None,
        "labelMessages": None,
    }


if __name__ == "__main__":
    unittest.main()
