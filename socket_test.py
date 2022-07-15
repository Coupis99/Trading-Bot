#imports
from binance.client import Client
from binance import ThreadedWebsocketManager
from datetime import datetime, timedelta
import pandas as pd
from time import sleep


#binance api config - when publishing to github replace the keys with env variables
api_key = "30BgpWV9iVTXSVACnrVPeqtI7wDP18pMaTcGBjSl79DDJq04Kg9eMIBRrBoUkBUw"
api_secret = "F9AAFQXqA44SGbd0zyqJhocaFae2zKgt1QnjNklwnkFAFpt1fximqKnV3BCyEP9I"
client = Client(api_key, api_secret, url='https://fapi.binance.com')

print(client.futures_account_balance())