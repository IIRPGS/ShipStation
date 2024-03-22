import os
from dotenv import load_dotenv
from ship_station import ShipStation, ShipStationOrderResponse

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))

load_dotenv()

ss_api_key = os.getenv("SHIPSTATION_API_KEY", "")
ss_api_secret = os.getenv("SHIPSTATION_API_SECRET", "")
handler = ShipStation(ss_api_key, ss_api_secret)

auth = handler.authorization_header["Authorization"]
z = handler._ShipStation__remove_basic_in_auth_string(auth)
z = handler._ShipStation__decode_b64_auth_string(z)
print(handler.authorize_request(auth))