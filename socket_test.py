#imports
from sqlite3 import Timestamp
from binance.client import Client
from binance import ThreadedWebsocketManager
from binance.exceptions import BinanceAPIException, BinanceOrderException
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

buy_limit = client.futures_create_order(
        symbol=symbol,
        side='BUY',
        type='LIMIT',
        timeInForce='GTC',
        quantity=0.001,
        price=19397,
        positionSide="BOTH",
        reduceOnly = False)


print(buy_limit)
print("\n")

while True:
        status = client.futures_get_order(symbol = symbol, orderId = buy_limit["orderId"])["status"]
        if status == "FILLED":
                break
        print("jeste neni filled")
        sleep(5)
print("filled")
print("\n")
print(buy_limit)

sl_sell_limit = client.futures_create_order(
                symbol = symbol,
                side = "SELL",
                type = "STOP",
                quantity = 0.1,
                stopPrice=18000,
                price = 18000, 
                reduceOnly=True, 
                positionSide="BOTH",
                timeInForce='GTE_GTC')

tp_sell_limit = client.futures_create_order(
                symbol = symbol,
                side = "SELL",
                type = "TAKE_PROFIT",
                stopPrice=22500,
                price = 22500, 
                reduceOnly=True, 
                quantity = 0.1,
                positionSide="BOTH",
                timeInForce='GTE_GTC')

print("za 10 ukoncuji trade")
sleep(10)
#client.futures_cancel_order(symbol = symbol, orderId = int(buy_limit["orderId"]), timestamp = True, origClientOrderId = str(buy_limit["clientOrderId"]))