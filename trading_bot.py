from contextlib import redirect_stderr
from binance.client import Client
from binance import ThreadedWebsocketManager
from datetime import datetime, timedelta
import pandas as pd
from time import sleep
import zmq

api_key = "30BgpWV9iVTXSVACnrVPeqtI7wDP18pMaTcGBjSl79DDJq04Kg9eMIBRrBoUkBUw"
api_secret = "F9AAFQXqA44SGbd0zyqJhocaFae2zKgt1QnjNklwnkFAFpt1fximqKnV3BCyEP9I"
client = Client(api_key, api_secret)

symbol = 'BTCUSD'

# init and start the WebSocket
bsm = ThreadedWebsocketManager()
bsm.start()

# get timestamp of earliest date data is available
while True:
    while (int(datetime.now().strftime("%M")) != 30) and ((int(datetime.now().strftime("%M")) != 0)):
        #do nothing
        print(datetime.now())
        print("cekam na konec pulhodiny")
        sleep(29)
    print("muzu zacit")
    dt = datetime.now() - timedelta(hours = 500.5)
    timestamp = int(datetime.timestamp(dt)) * 1000
    print(dt)
    print(timestamp)

    # request historical candle (or klines) data
    bars = client.get_historical_klines("BTCUSDT", '30m', timestamp, limit=500)

    for line in bars:
        del line[6:]
    del bars[-1]

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
    
    print(res_string)
    context = zmq.Context()

    #  Socket to talk to server
    print("Connecting to hello world server…")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")
    socket.send(bytes(res_string, encoding="utf-8"))

    df = pd.DataFrame(bars, columns=["DateTime", "Open", "High", "Low", "Close", "Volume"])
    for i in range(len(df)):
        df.loc[i, "DateTime"] = datetime.fromtimestamp(df.loc[i, "DateTime"]/1000)

    print(df)
    
    break
bsm.stop()   
