#imports
from binance.client import Client
from binance import ThreadedWebsocketManager
from datetime import datetime, timedelta
import pandas as pd
from time import sleep
import json
import requests

symbol = "BTCUSDT"
#binance api config - when publishing to github replace the keys with env variables
api_key = "46332cbdcb7721395928c33e952fd7e801f6ed26b5838a5cd02143465b9004c7"
api_secret = "cfea28c13b62df5277e529618a95a98c7b21215670475b8a794e1efdd16478d4"
client = Client(api_key, api_secret, testnet=True)
client.API_URL = "https://testnet.binancefuture.com/fapi"

print(float(client.futures_account_balance()[1]["balance"]))

# defining key/request url
key=f"https://testnet.binancefuture.com/fapi/v1/ticker/24hr?symbol={symbol}"
  
# requesting data from url
data = requests.get(key)  
data = data.json()
print(data["lastPrice"])


