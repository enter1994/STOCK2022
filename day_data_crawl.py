from random import randint
import time
from time import gmtime, mktime
from datetime import datetime
import yfinance as yf
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

json_path = "/Users/parkdoyeong/Documents/Paper/research-stock-GPT/corporate.json"

# datetime to unixtime
s = time.strptime('2017-07-01', '%Y-%m-%d')
e = time.strptime('2022-06-10', '%Y-%m-%d')
start_1 = int(mktime(s)) + 32400
end_1 = int(mktime(e)) + 32400

def get_hour(tag):
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    
    # 크롤링 할 chart url 불러오기
    req = requests.get(
    json_data[tag]['chart_url'],
    headers = {
        "User-Agent": random_user_agent(),
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "text/html",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    )

    # get chart url
    soup = BeautifulSoup(req.text, 'html.parser')
    url = soup.select_one("#leftColumn > div.tvChartContainer > div:nth-child(1) > iframe").attrs["src"]

    url_parsing = parse.urlparse(url)

    qs = parse.parse_qs(url_parsing.query)
    carrier = qs['carrier'][0]
    symbol = qs['pair_ID'][0]
    t = qs['time'][0]

    url1 = f"https://tvc4.investing.com/{carrier}/{t}/1/1/8/history?symbol={symbol}&resolution=D&from={start_1}&to={end_1}"

    # Crawling
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

    price_1 = json.loads(req1.text)

    # Unixtime to datetime and save file
    for i in range(len(price_1['t'])):
        price_1['t'][i] = datetime.fromtimestamp(price_1['t'][i])

    Df_price = pd.DataFrame({
        'Time' : price_1['t'],
        'Opened' : price_1['o'],
        'Closed' : price_1['c'],
        'High' : price_1['h'],
        'Low' : price_1['l'],
        'Volume' : price_1['v']
    })

    Df_price.to_csv(f'./day_data/{tag}.csv')

if __name__ == "__main__":
    with open('500_Crawl/corporate.txt', 'r') as f:
        lines = f.readlines()

    for tag in tqdm(lines):
        tag = tag.strip()

        try:
            get_hour(tag)
        except:
            print(tag)
