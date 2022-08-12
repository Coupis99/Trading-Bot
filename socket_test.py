#imports
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
        quantity=0.1,
        price=22400,
        positionSide="BOTH",
        reduceOnly = False)

sl_sell_market = client.futures_create_order(
                symbol = symbol,
                side = "SELL",
                type = "STOP_MARKET",
                quantity = 0.1,
                stopPrice=22300, 
                reduceOnly=True, 
                positionSide="BOTH",
                timeInForce='GTE_GTC')
tp_sell_market = client.futures_create_order(
                symbol = symbol,
                side = "SELL",
                type = "TAKE_PROFIT_MARKET",
                stopPrice=22500, 
                reduceOnly=True, 
                quantity = 0.1,
                positionSide="BOTH",
                timeInForce='GTE_GTC')
print("order filled")

print(buy_limit)