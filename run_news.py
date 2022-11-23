import requests
import pathlib
import datetime
from urllib import parse

from bs4 import BeautifulSoup
from tqdm import tqdm
from investpy.search import search_quotes
from investpy.utils.extra import random_user_agent
from rate_limiter import rate_limit

import wandb


def getInvesting(ticker):

    results = search_quotes(ticker, countries=["united states"], n_results=3)

    for result in results:
        if result.pair_type == "stocks":
            return "https://www.investing.com" + result.tag + "-news"


def crawling(company_code="APPL", root_path="./"):

    base_url = getInvesting(company_code)

    wandb.init(
        project="comment-crawling",
        entity="coling2022-interpretation",
        name=company_code,
        config={
            "num_comments": 0,
            "num_pages": 0,
            "base_url": base_url
        }
    )

    num_comments = 0
    out_path = root_path.joinpath(f"{company_code}.csv")

    with open(out_path, "w") as out_file:

        i = 1
        base_url = getInvesting(company_code)
        if base_url == "https://www.investing.com/-news":
            wandb.finish()
            return

        pbar = tqdm()

        while True:
            url = f"{base_url}/{i}"
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

            tolerance = 100
            link = soup.find_all('link', rel='canonical')

            while len(link) == 0 and tolerance > 0:
                with open("error.html", "w") as f:
                    f.write(req.text)
                
                rate_limit("investing")
                req = requests.get(url, headers=head)
                soup = BeautifulSoup(req.text, 'html.parser')
                link = soup.find_all('link', rel='canonical')
                tolerance -= 1
            
            if tolerance == 0:
                print("end: ", datetime.datetime.now())
                wandb.finish(exit_code=1)
                break

            # 종료 조건
            if link[0]['href'] == base_url:
                break

            items = soup.select_one("#comments > ul")

            if items is None:
                break

            request_date = datetime.datetime.strptime(req.headers["Date"],
                                                    "%a, %d %b %Y %H:%M:%S GMT")

            for item in items:
                comment = item.select_one("div.comment_content__AvzPV").text
                comment_date = item.select_one("span[data-test='comment-date']").text
                if comment_date == "Just Now":
                    comment_date = request_date.strftime("%b %d, %Y, %H:%M")
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
                
                out_file.write(line)

            num_comments += len(items)
            wandb.config.update(
                {
                    "num_comments" : num_comments,
                    "num_pages": i
                },
                allow_val_change=True
            )

            i += 1
            pbar.update(1)
        pbar.close()
    
    with open(out_path, "r") as out_file:
        lines = out_file.readlines()
    
    if len(lines) != 0:
        start_date = lines[-1].split("\t")[-1].strip()
        end_date = lines[0].split("\t")[-1].strip()

        wandb.config.update(
            {
                "start_date": start_date,
                "end_date": end_date
            }
        )

    wandb.save(str(out_path))
    wandb.finish(exit_code=0)


def load_finished_companies():
    api = wandb.Api()
    runs = api.runs("coling2022-interpretation/comment-crawling")
    finished_companies = [run.name for run in runs if run.state in ["finished", "running"]]

    return finished_companies


if __name__ == "__main__":
    root = pathlib.Path("comments")
    root.mkdir(parents=True, exist_ok=True)

    with open("corporate.txt", "r") as f:
        companies = f.readlines()
    
    for company in companies:
        company = company.strip()

        finished_companies = load_finished_companies()

        if company in finished_companies:
            continue
        
        crawling(company_code=company, root_path=root)
