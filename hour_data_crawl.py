from random import randint
import time
from time import gmtime, mktime
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from investpy.stocks import (
    get_stock_recent_data, get_stock_countries, get_stock_company_profile, get_stock_historical_data
)
from investpy.utils.extra import random_user_agent

import json
import pandas as pd
from urllib import parse
import csv
from tqdm import tqdm

# Error Corporate
li = ['BALL', 'BBWI', 'BRKB', 'BFB', 'CARR', 'CDAY', 'CEG', 'CTRA', 'HWM', 'J', 'LIN', 'LUMN', 'META','MRNA', 'OGN', 'OTIS', 'PARA', 'PAYC', 'RTX', 'TT', 'TFC', 'VTRS', 'VICI', 'WBD', 'WTW']

# Read full corporate name
stocks_path = "/Users/parkdoyeong/miniforge3/envs/crawling/lib/python3.8/site-packages/investpy/resources/stocks.csv"
df = pd.read_csv(stocks_path)
df = df[df["country"] == "united states"]

# date to unix time
s = time.strptime('2017-07-01', '%Y-%m-%d')
e = time.strptime('2020-03-15', '%Y-%m-%d')

start_1 = int(mktime(s)) + 32400
end_1 = int(mktime(e)) + 32400

s = time.strptime('2020-01-03', '%Y-%m-%d')
e = time.strptime('2022-06-11', '%Y-%m-%d')

start_2 = int(mktime(s)) + 32400
end_2 = int(mktime(e)) + 32400

def get_hour(tag):

    name = df[df["symbol"] == tag]["tag"].values[0]
    
    req = requests.get(
        f"https://www.investing.com/equities/{name}-chart",
        headers = {
            "User-Agent": random_user_agent(),
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "text/html",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    )
    
    soup = BeautifulSoup(req.text, 'html.parser')
    url = soup.select_one("#leftColumn > div.tvChartContainer > div:nth-child(1) > iframe").attrs["src"]
    # print(url)
    url_parsing = parse.urlparse(url)
    
    qs = parse.parse_qs(url_parsing.query)
    carrier = qs['carrier'][0]
    symbol = qs['pair_ID'][0]
    t = qs['time'][0]
    # t = "1655695721"
    
    url1 = f"https://tvc4.investing.com/{carrier}/{t}/1/1/8/history?symbol={symbol}&resolution=60&from={start_1}&to={end_1}"
    url2 = f"https://tvc4.investing.com/{carrier}/{t}/1/1/8/history?symbol={symbol}&resolution=60&from={start_2}&to={end_2}"

    req1 = requests.get(
        url1,
        headers = {
            "User-Agent": random_user_agent(),
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "text/html",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    )

    req2 = requests.get(
        url2,
        headers = {
            "User-Agent": random_user_agent(),
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "text/html",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    )
    
    price_1 = json.loads(req1.text)
    price_2 = json.loads(req2.text)

    for i in range(len(price_1['t'])):
        price_1['t'][i] = datetime.fromtimestamp(price_1['t'][i] - 46800)

    for i in range(len(price_2['t'])):
        price_2['t'][i] = datetime.fromtimestamp(price_2['t'][i] - 46800)

    price_hour = price_1['t']
    
    Df_price = pd.DataFrame({
        'Time' : price_1['t'] + price_2['t'],
        'Opened' : price_1['o'] + price_2['o'],
        'Closed' : price_1['c'] + price_2['c'],
        'High' : price_1['h'] + price_2['h'],
        'Low' : price_1['l'] + price_2['l'],
        # 'Volume' : price_1['vo'] + price_2['vo']
    })
    
    # Modify path
    Df_price.to_csv(f'./hour_data/{tag}.csv')

# path
S&P500_path = "500_Crawl/corporate.txt"

if __name__ == "__main__":
    with open(S&P500_path, "r") as f:
        lines = f.readlines()
        
    for tag in tqdm(lines):
        tag = tag.strip()

        try:
            get_hour(tag)

        except:
            print(tag)