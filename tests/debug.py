import os
from dotenv import load_dotenv
from ship_station.ship_station import ShipStation
from ship_station.order_response import ShipStationOrderResponse

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))

load_dotenv()

# Script used as a playground for testing functionality

ss_api_key = os.getenv("SHIPSTATION_API_KEY", "")
ss_api_secret = os.getenv("SHIPSTATION_API_SECRET", "")
handler = ShipStation(ss_api_key, ss_api_secret)

