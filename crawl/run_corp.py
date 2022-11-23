import requests
from investpy.utils.extra import random_user_agent
from tessa.rate_limiter import rate_limit

import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm

def getInvesting(ticker):

    target_address = 'https://www.google.com/search?q='+ticker+'+investing'
    html = requests.get(target_address)
    soup = BeautifulSoup(html.text, 'html.parser')
    posts = soup.select('.kCrYT a ')
    #for chooes first herf 
    href = str(posts[0].attrs['href'])
    #then href is 'https:/www.investing/equities/stock&~~~~~~ 
    #so 1.find  start-index : index('equities') , end-index : index('&')
    # and slicing href[start : end]
    start = href.find('equities')
    end = href.find('&')
    # print(href[start:end])

    return "https://www.investing.com/" + href[start:end]

def crawling(corp, writer):
    i = 0
    pbar = tqdm()
    
    while True:
        i += 1
        
        pbar.update(1)
        
        url = getInvesting(corp) + '/' + str(i)
        
        head = {
            "User-Agent": random_user_agent(),
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "text/html",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        rate_limit("investing")
        req = requests.get(url, headers=head)
        soup = BeautifulSoup(req.text, 'html.parser')
        items = soup.select_one("#comments > ul")
        link = soup.find_all('link', rel='canonical')
        
        if link[0]['href'] == getInvesting(corp):
            break
        
        
        tolerance = 100
        while items is None and tolerance > 0:
            with open("error.html", "w") as f:
                f.write(req.text)
            
            rate_limit("investing")
            req = requests.get(url, headers=head)
            soup = BeautifulSoup(req.text, 'html.parser')
            items = soup.select_one("#comments > ul")
            tolerance -= 1
        
        if tolerance == 0:
            print("end: ", datetime.datetime.now())
            break
        
        request_date = datetime.datetime.strptime(req.headers["Date"],
                                                  "%a, %d %b %Y %H:%M:%S GMT")

        for item in items:
            comment = item.select_one("div.comment_content__AvzPV").text
            comment_date = item.select_one("span[data-test='comment-date']").text

            if comment_date.endswith("minute ago"):
                delta = int(comment_date.replace("minute ago", ""))
                comment_date = request_date - datetime.timedelta(minutes=delta)
                comment_date = comment_date.strftime("%b %d, %Y, %H:%M")
            elif comment_date.endswith("minutes ago"):
                delta = int(comment_date.replace("minutes ago", ""))
                comment_date = request_date - datetime.timedelta(minutes=delta)
                comment_date = comment_date.strftime("%b %d, %Y, %H:%M")
            elif comment_date.endswith("hour ago"):
                delta = int(comment_date.replace("hour ago", ""))
                comment_date = request_date - datetime.timedelta(minutes=delta)
                comment_date = comment_date.strftime("%b %d, %Y, %H:%M")
            elif comment_date.endswith("hours ago"):
                delta = int(comment_date.replace("hours ago", ""))
                comment_date = request_date - datetime.timedelta(minutes=delta)
                comment_date = comment_date.strftime("%b %d, %Y, %H:%M")
                
            line = f"{comment}\t{comment_date}\n"
                
            writer.write(line)
           
    pbar.close()

if __name__ == "__main__":
    
    f = open(f'corporate.txt', 'r')

    while True:
        corp = f.readline()
        corp = str(corp)
        
        if not corp: break
    
        with open(f"{corp}.csv", "w") as out_file:
            crawling(corp, writer=out_file)