from dotenv import load_dotenv
from os import getenv
from helpers.ShipStation import ShipStation
import requests


load_dotenv()

ss_api_key = getenv("SHIPSTATION_API_KEY", "")
ss_api_secret = getenv("SHIPSTATION_API_SECRET", "")
handler = ShipStation(ss_api_key, ss_api_secret)
