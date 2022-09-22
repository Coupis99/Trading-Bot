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

#get average true range of last known row
def get_atr(data, period):
    cum_sum = 0
    for idx in range(len(data) - period, len(data)):
        cum_sum += max(abs(float(data.iloc[idx]["High"]) - float(data.iloc[idx]["Low"])), abs(float(data.iloc[idx]["High"]) - float(data.iloc[idx-1]["Close"])),
                       abs(float(data.iloc[idx-1]["Close"]) - float(data.iloc[idx]["Low"])))
    return cum_sum / period

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
def mm(close_t1, p_high, p_low, at):
    RRR = 2
    HH = 2
    res = {}
    size = 0
    cur_price = get_cur_last_price(symbol)
    if (abs(cur_price - p_high) > (HH * abs(cur_price - p_low))) and (cur_price - p_low > (at / 3)):
        order_type = "BUY"
        sl = p_low - (abs(cur_price - p_low) * 0.01)
        tp = cur_price + (RRR * abs(cur_price - p_low))
        size = pos_size(tp, close_t1)
        res["DateTime"] = str(datetime.now())
        res["Symbol"] = symbol
        res["OrderType"] = order_type
        res["StopLoss"] = round(sl, 2)
        res["TakeProfit"] = round(tp, 2)
        res["PositionSize"] = round(float(size[0]), 2)
        res["AdjustedSize"] = str(size[1])
        res["CurrentPrice"] = str(cur_price)
        res["PredictedHigh"] = str(p_high)
        res["PredictedLow"] = str(p_low)
    elif ((HH * abs(cur_price - p_high) < abs(cur_price - p_low))) and (p_high - cur_price > (at / 3)):
        order_type = "SELL"
        sl = p_high + (abs(cur_price - p_high) * 0.01)
        tp = cur_price - (RRR * abs(cur_price - p_high))
        size = pos_size(tp, close_t1)
        res["DateTime"] = str(datetime.now())
        res["Symbol"] = symbol
        res["OrderType"] = order_type
        res["StopLoss"] = round(sl, 2)
        res["TakeProfit"] = round(tp, 2)
        res["PositionSize"] = round(float(size[0]), 2)
        res["AdjustedSize"] = str(size[1])
        res["CurrentPrice"] = str(cur_price)
        res["PredictedHigh"] = str(p_high)
        res["PredictedLow"] = str(p_low)
    else:
        print("no possible trade found")
    return res

#position size
def pos_size(tp, close_t1):
    adjusted = False
    bal = float(client.futures_account_balance()[1]["balance"])
    reward = bal * 0.1
    cur_price = get_cur_last_price(symbol)
    pos_size = (reward * cur_price) / (abs(cur_price - tp))
    if pos_size > 24 * bal:
        pos_size = 23 * bal
        adjusted = True
    return [float(float(pos_size) / float(cur_price)), adjusted]

def place_order(type, sl, tp, size, p):
    force_end = ""
    er = None
    if type == "BUY":
        order_id = 0
        try:
            buy_limit = client.futures_create_order(
                symbol=symbol,
                side='BUY',
                type='LIMIT',
                quantity=size, 
                timeInForce='GTC',
                price = p,
                positionSide="BOTH",
                reduceOnly = False)
            order_id = buy_limit["orderId"]
            print("order placed")
        except BinanceAPIException as e:
            #error handling goes here
            print(e)
            sleep(3)
            client.futures_cancel_all_open_orders(symbol = symbol) # if the order went through
            print("canceling all open orders")
            er = e
        except BinanceOrderException as e:
            #error handling goes here
            print(e)
            sleep(3)
            client.futures_cancel_all_open_orders(symbol = symbol) # if the order went through
            print("canceling all open orders")
            er = e
            
        wait_minute = 0
        if int(datetime.now().strftime("%M")) < 30:
            wait_minute = 25
        else:
            wait_minute = 55
        while True:
            status = client.futures_get_order(symbol = symbol, orderId = order_id)["status"]

            if status == "FILLED":
                print(str(datetime.now())+ " - order filled")
                try:
                    sl_sell_market = client.futures_create_order(
                                    symbol = symbol,
                                    side = "SELL",
                                    type = "STOP",
                                    quantity = size,
                                    stopPrice=sl, 
                                    price=sl,
                                    reduceOnly=True, 
                                    positionSide="BOTH",
                                    timeInForce='GTE_GTC')
                    tp_sell_market = client.futures_create_order(
                                    symbol = symbol,
                                    side = "SELL",
                                    type = "TAKE_PROFIT",
                                    stopPrice=tp, 
                                    price=tp,
                                    reduceOnly=True, 
                                    quantity = size,
                                    positionSide="BOTH",
                                    timeInForce='GTE_GTC')
                except:
                    er = "failed to append stoploss or takeprofit to order"
                    print(er) 
                    print("\n closing the filled order")  
                    close_market = client.futures_create_order(symbol=symbol,
                                                                side = "SELL",
                                                                type = "Market",
                                                                quantity = size)   
                break
            elif int(datetime.now().strftime("%M")) == wait_minute:
                print(str(datetime.now())+ " - order did not filled - canceling the open order")
                client.futures_cancel_all_open_orders(symbol = symbol)
                return "not filled"
            else:
                print(str(datetime.now()) + " - " +"waiting for filling the order")
                sleep(10)
    else:
        order_id = 0
        try:
            sell_limit = client.futures_create_order(
                symbol=symbol,
                side='SELL',
                type='LIMIT',
                quantity=size, 
                timeInForce='GTC',
                price = p,
                positionSide="BOTH",
                reduceOnly = False)
            order_id = sell_limit["orderId"]
            print("order placed")
        except BinanceAPIException as e:
            #error handling goes here
            print(e)
            sleep(3)
            client.futures_cancel_all_open_orders(symbol = symbol) # if the order went through
            print("canceling all open orders")
            er = e
        except BinanceOrderException as e:
            #error handling goes here
            print(e)
            sleep(3)
            client.futures_cancel_all_open_orders(symbol = symbol) # if the order went through
            print("canceling all open orders")
            er = e
            
        wait_minute = 0
        if int(datetime.now().strftime("%M")) < 30:
            wait_minute = 25
        else:
            wait_minute = 55
        while True:
            status = client.futures_get_order(symbol = symbol, orderId = order_id)["status"]

            if status == "FILLED":
                print(str(datetime.now())+ " - order filled")
                try:
                    sl_sell_market = client.futures_create_order(
                                    symbol = symbol,
                                    side = "BUY",
                                    type = "STOP",
                                    quantity = size,
                                    stopPrice=sl,
                                    price = sl, 
                                    reduceOnly=True, 
                                    positionSide="BOTH",
                                    timeInForce='GTE_GTC')
                    tp_sell_market = client.futures_create_order(
                                    symbol = symbol,
                                    side = "BUY",
                                    type = "TAKE_PROFIT",
                                    stopPrice=tp,
                                    price=tp, 
                                    reduceOnly=True, 
                                    quantity = size,
                                    positionSide="BOTH",
                                    timeInForce='GTE_GTC')
                except:
                    er = "failed to append stoploss or takeprofit to order"
                    print(er) 
                    print("\n closing the filled order")  
                    close_market = client.futures_create_order(symbol=symbol,
                                                                side = "BUY",
                                                                type = "Market",
                                                                quantity = size)   
                break
            elif int(datetime.now().strftime("%M")) == wait_minute:
                print(str(datetime.now())+ " - order did not filled - canceling the open order")
                client.futures_cancel_all_open_orders(symbol = symbol)
                return "not filled"
            else:
                print(str(datetime.now()) + " - " +"waiting for filling the order")
                sleep(10)
    return str(er) + " - " + force_end
#focusing only on BTCUSDT
symbol = 'LTCUSDT'

#init and start the WebSocket
bsm = ThreadedWebsocketManager()
bsm.start()

#main cycle
while True:

    #wait until all positions are closed
    while len(client.futures_get_open_orders()) > 0:
        #do nothing
        print(datetime.now())
        print("waiting for closing all open orders..")
        sleep(29)

    print("all open orders closed")

    #wait until xx:00 or xx:30
    while (int(datetime.now().strftime("%M")) != 30) and ((int(datetime.now().strftime("%M")) != 0)):
        #do nothing
        print(datetime.now())
        print("waiting for the end of half an hour")
        sleep(29)

    print("Let the fun begin")

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

    atr = get_atr(df, 14)
    print("ATR: " + str(atr))
    
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

    order = mm(close_t1, pred_high, pred_low, atr)

    #write to a file
    if (order != {}):
        print(order)
        order["BalanceBeforeTrade"] = float(client.futures_account_balance()[1]["balance"])
        cur_price = get_cur_last_price(symbol)
        order["BalanceAfterSucTrade"] = order["BalanceBeforeTrade"] + (abs(order["TakeProfit"] - cur_price) * order["PositionSize"])
        order["BalanceGrowthPct"] = str(((order["BalanceAfterSucTrade"]/order["BalanceBeforeTrade"]) - 1) * 100) + "%"
        order["BalanceAfterUnsucTrade"] = order["BalanceBeforeTrade"] - (abs(order["StopLoss"] - cur_price) * order["PositionSize"])
        order["BalanceDropPct"] = str((1 - (order["BalanceAfterUnsucTrade"] / order["BalanceBeforeTrade"])) * 100) + "%"
        e = place_order(order["OrderType"], order["StopLoss"], order["TakeProfit"], order["PositionSize"], order["CurrentPrice"])
        if e == "not filled":
            print("order not filled - not writing to a file")
        else:
            order["Error"] = str(e)
            print("writing to a file")
            js = json.dumps(order, indent=4)
            f = open("trade_log.txt", "a")
            f.write("\n")
            f.write(js)
            f.close()
    
    print("sleeping")
    sleep(60)
    
bsm.stop()  
  