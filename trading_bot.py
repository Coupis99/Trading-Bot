from binance.client import Client
from binance import ThreadedWebsocketManager
from datetime import datetime, timedelta
import pandas as pd
from time import sleep

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
    dt = datetime.now() - timedelta(hours = 500)
    timestamp = int(datetime.timestamp(dt)) * 1000
    print(dt)
    print(timestamp)

    # request historical candle (or klines) data
    bars = client.get_historical_klines("BTCUSDT", '30m', timestamp, limit=500)
    # stop websocket
    bsm.stop()
    for line in bars:
        del line[6:]

    df = pd.DataFrame(bars, columns=["DateTime", "Open", "High", "Low", "Close", "Volume"])
    for i in range(len(df)):
        df.loc[i, "DateTime"] = datetime.fromtimestamp(df.loc[i, "DateTime"]/1000)

    print(df)
    
    break
    
