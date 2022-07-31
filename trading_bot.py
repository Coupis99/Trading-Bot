#imports
from binance.client import Client
from binance import ThreadedWebsocketManager
from binance.exceptions import BinanceAPIException, BinanceOrderException
from datetime import datetime, timedelta
import pandas as pd
from time import sleep
import zmq
import json
import requests

#binance api config - when publishing to github replace the keys with env variables
api_key = "46332cbdcb7721395928c33e952fd7e801f6ed26b5838a5cd02143465b9004c7"
api_secret = "cfea28c13b62df5277e529618a95a98c7b21215670475b8a794e1efdd16478d4"
client = Client(api_key, api_secret, testnet=True)
client.API_URL = "https://testnet.binancefuture.com/fapi"

#init ZMQ REQ sockets on port 5555 - this is client
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

#get current last price of given symbol
def get_cur_last_price(smb):
    key = f"https://testnet.binancefuture.com/fapi/v1/ticker/24hr?symbol={smb}"
    data = requests.get(key)  
    data = data.json()
    res = float(data["lastPrice"])
    return res

#converting data into string separated with | and ||
def conv_to_string(data):
    res_string = ""
    for line in range(len(bars)):
        for el in range(len(bars[line])):
            if el == len(bars[line]) - 1:
                res_string = res_string + str(bars[line][el])
            else:
                if el == 0:
                    cl_t = str(datetime.fromtimestamp(int(bars[line][el]/1000)))
                    res_string = res_string + cl_t + "|"
                else:
                    res_string = res_string + str(bars[line][el]) + "|"
        if line != len(bars) - 1:
            res_string = res_string + "||"
    return res_string

#money management
def mm(close_t1, p_high, p_low):
    RRR = 2
    HH = 2
    res = {}
    size = 0
    if (abs(close_t1 - p_high) > (HH * abs(close_t1 - p_low))) and (abs(p_high - p_low) > 80):
        order_type = "BUY"
        sl = p_low
        tp = close_t1 + (2 * abs(close_t1 - p_low))
        size = round(pos_size(tp, close_t1), 2)
        res["DateTime"] = str(datetime.now())
        res["OrderType"] = order_type
        res["StopLoss"] = round(sl, 2)
        res["TakeProfit"] = round(tp, 2)
        res["PositionSize"] = size
    elif ((HH * abs(close_t1 - p_high) < abs(close_t1 - p_low))) and (abs(p_high - p_low) > 80):
        order_type = "SELL"
        sl = p_high
        tp = close_t1 - (2 * abs(close_t1 - p_high))
        size = round(pos_size(tp, close_t1), 2)
        res["DateTime"] = str(datetime.now())
        res["OrderType"] = order_type
        res["StopLoss"] = round(sl, 2)
        res["TakeProfit"] = round(tp, 2)
        res["PositionSize"] = size
    else:
        print("není to ani jedno")
    return res

#position size
def pos_size(tp, close_t1):
    bal = float(client.futures_account_balance()[1]["balance"])
    reward = bal * 0.1
    pos_size = (reward * close_t1) / (abs(close_t1 - tp))
    cur_price = get_cur_last_price(symbol)
    if pos_size > 20 * bal:
        pos_size = 18 * bal
    return float(pos_size) / float(cur_price)

def place_order(type, sl, tp, size):
    if type == "BUY":
        try:
            buy_market = client.futures_create_order(
                symbol=symbol,
                side='BUY',
                type='MARKET',
                quantity=size)
            tp_sell_market = client.futures_create_order(
                symbol = symbol,
                side = "SELL",
                type='TAKE_PROFIT_MARKET',
                stopPrice=tp, 
                closePosition=True, 
                timeInForce='GTE_GTC')
            sl_sell_market = client.futures_create_order(
                symbol = symbol,
                side = "SELL",
                type='STOP_MARKET',
                stopPrice=sl, 
                closePosition=True, 
                timeInForce='GTE_GTC')
            print("order filled")
        except BinanceAPIException as e:
            #error handling goes here
            print(e)
        except BinanceOrderException as e:
            #error handling goes here
            print(e)
    else:
        try:
            sell_market = client.futures_create_order(
                symbol=symbol,
                side='SELL',
                type='MARKET',
                quantity=size)
            tp_buy_market = client.futures_create_order(
                symbol = symbol,
                side = "BUY",
                type='TAKE_PROFIT_MARKET',
                stopPrice=tp, 
                closePosition=True, 
                timeInForce='GTE_GTC')
            sl_buy_market = client.futures_create_order(
                symbol = symbol,
                side = "BUY",
                type='STOP_MARKET',
                stopPrice=sl, 
                closePosition=True, 
                timeInForce='GTE_GTC')
            print("order filled")
        except BinanceAPIException as e:
            #error handling goes here
            print(e)
        except BinanceOrderException as e:
            #error handling goes here
            print(e)

#focusing only on BTCUSDT
symbol = 'BTCUSDT'

#init and start the WebSocket
bsm = ThreadedWebsocketManager()
bsm.start()

#main cycle
while True:

    #wait until all positions are closed
    while len(client.futures_get_open_orders()) > 0:
        #do nothing
        print(datetime.now())
        print("cekam na ukonceni vsech pozic")
        sleep(29)

    print("vsechny pozice ukonceny")

    #wait until xx:00 or xx:30
    while (int(datetime.now().strftime("%M")) != 30) and ((int(datetime.now().strftime("%M")) != 0)):
        #do nothing
        print(datetime.now())
        print("cekam na konec pulhodiny")
        sleep(29)

    print("muzu zacit")

    #finding datetime 1000 half hours back from now
    dt = datetime.now() - timedelta(hours = 500.5) 
    timestamp = int(datetime.timestamp(dt)) * 1000

    #request historical candle (or klines) data
    bars = client.futures_historical_klines(symbol, '30m', timestamp, limit=500)

    #delete unnecessary data
    for line in bars:
        del line[6:]
    del bars[-1]

    #pandas dataframe for comparsion
    df = pd.DataFrame(bars, columns=["DateTime", "Open", "High", "Low", "Close", "Volume"])
    for i in range(len(df)):
        df.loc[i, "DateTime"] = datetime.fromtimestamp(df.loc[i, "DateTime"]/1000)
        
    print(df)
    
    #convert bars to string
    res_string = conv_to_string(bars)

    #send converted string on server (R)
    socket.send(bytes(res_string, encoding="utf-8"))

    #wait for the response - predicted values from NN
    pred_val_str = ""
    while pred_val_str == "":
        print("waiting for the response")
        pred_val_str = socket.recv()
        if pred_val_str != "":
            print("response arrived")
    
    #convert response from bytes to string 
    pred_val_str = pred_val_str.decode()

    #convert pred_val_str into a list with predicted values
    pred_val_lst = pred_val_str.split("|")

    print(pred_val_lst)

    #init predicted variables
    pred_high = float(pred_val_lst[0])
    pred_low = float(pred_val_lst[1])
    pred_close = float(pred_val_lst[2])
    close_t1 = float(df.loc[len(df) - 1, "Close"])

    order = mm(close_t1, pred_high, pred_low)

    #write to a file
    if (order != {}):
        print(order)
        place_order(order["OrderType"], order["StopLoss"], order["TakeProfit"], order["PositionSize"])
        print("zapisuji do souboru")
        js = json.dumps(order, indent=4)
        f = open("trade_log.txt", "a")
        f.write("\n")
        f.write(js)
        f.close()
    
    print("sleeping")
    sleep(60)
    
bsm.stop()  
  