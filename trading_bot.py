#imports
from binance.client import Client
from binance import ThreadedWebsocketManager
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
    res = ""
    size = 0
    if abs(close_t1 - p_high) > (HH * abs(close_t1 - p_low)):
        order_type = "long"
        sl = p_low
        tp = close_t1 + (2 * abs(close_t1 - p_low))
        size = round(pos_size(tp, close_t1), 2)
        res = str(datetime.now())+ "|" + str(order_type) + "|" + str(size) + "|" + str(sl) + "|" + str(tp)
    elif (HH * abs(close_t1 - p_high) < abs(close_t1 - p_low)):
        order_type = "short"
        sl = p_high
        tp = close_t1 - (2 * abs(close_t1 - p_high))
        size = round(pos_size(tp, close_t1), 2)
        res = str(datetime.now()) + "|" + str(order_type) + "|" + str(size) + "|" + str(sl) + "|" + str(tp)
    else:
        print("není to ani jedno")
    return res

#position size
def pos_size(tp, close_t1):
    bal = float(client.futures_account_balance()[1]["balance"])
    reward = bal * 0.1
    pos_size = (reward * close_t1) / (abs(close_t1 - tp))
    key = f"https://testnet.binancefuture.com/fapi/v1/ticker/24hr?symbol={symbol}"
    data = requests.get(key)  
    data = data.json()
    cur_price = float(data["lastPrice"])
    return float(pos_size) / float(cur_price)

#focusing only on BTCUSDT
symbol = 'BTCUSDT'

#init and start the WebSocket
bsm = ThreadedWebsocketManager()
bsm.start()

#test list
test_lst = []
#main cycle
while True:

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

    print(dt)
    print(timestamp)

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
    
    print(pred_val_str)

    #convert response from bytes to string 
    pred_val_str = pred_val_str.decode()

    print(pred_val_str)

    #convert pred_val_str into a list with predicted values
    pred_val_lst = pred_val_str.split("|")

    print(pred_val_lst)

    #init predicted variables
    pred_high = float(pred_val_lst[0])
    pred_low = float(pred_val_lst[1])
    pred_close = float(pred_val_lst[2])
    close_t1 = float(df.loc[len(df) - 1, "Close"])

    order = mm(close_t1, pred_high, pred_low)
    print(order)
    if (order != ""):
        test_lst.append(order)

    print(test_lst)
    print(close_t1)
    print("sleeping")
    sleep(60)
    

bsm.stop()  
  