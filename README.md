# SalesStation
Package to make integration between Salesforce and ShipStation easier

## Setup
### Install the package
```shell
pip install git+https://github.com/sincile/SalesStation.git
```
### Import the class
```python
from sales_station.ship_station import ShipStation
```
### Initialize an instance of the class
```python
ss_api_key = getenv("SHIPSTATION_API_KEY", "")
ss_api_secret = getenv("SHIPSTATION_API_SECRET", "")
handler = ShipStation(ss_api_key, ss_api_secret)
```
