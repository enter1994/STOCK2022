import requests
from investpy.utils.extra import random_user_agent
from tessa.rate_limiter import rate_limit

import datetime
from bs4 import BeautifulSoup

from tqdm import tqdm

def crawling(writer):

    for i in tqdm(range(1, 3000)):
        url = f"https://www.investing.com/equities/tesla-motors-commentary/{i}"
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


if __name__ == "__main__":
    with open("output.csv", "w") as out_file:
        crawling(writer=out_file)
