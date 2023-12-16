import json
import sys
import time
from datetime import datetime

import requests
import urllib3.exceptions as urlexcepts
from bs4 import BeautifulSoup
from dateutil import parser

sys.path.append("..")
try:
    from .. import base
except ImportError:
    import base

ifgw_config = {}
with open("./IFGW/client.json") as f:
    ifgw_config = json.load(f)

if ifgw_config["url"][-1] != "/":
    ifgw_config["url"] = ifgw_config["url"]+"/"
cl_headers = ifgw_config["headers"]

sc = base.ScraperClient(base.get_prox_url(), download_headers=cl_headers)

def download_results_page(url: str, name: str):
    res = sc.load_url(url)
    if res is None:
        quit()

    soup = BeautifulSoup(res.text, features="html.parser")
    page_articles = []
    for h3_node in soup.find_all("h3", {"class", "g1-gamma g1-gamma-1st entry-title"}):
        page_articles.append(h3_node.findChild("a", recursive=True).get("href"))

    for art in page_articles:
        try:
            download_article(art, name)
        except Exception as e:
            print(f"skipping {art} due to {e}")

def download_article(url: str, name: str):
    folder = name.replace("-", " ")
    res = sc.load_url(url)
    if res is None:
        quit()
    soup = BeautifulSoup(res.text, features="html.parser")
    video = soup.find("video")
    upload_timestamp = parser.parse(soup.find("time").get("datetime"))

    if video is not None:
        vid_src: str = video.findChild("source").get("src")
        for bad_cdn in ["cdn03", "cdn02", "cdn01", "cdn07"]:
            if bad_cdn in vid_src:
                vid_src = vid_src.replace(bad_cdn, "cdn04")
        sc.download_file(vid_src, folder+"/videos", posted_date=upload_timestamp)
        pass

    images = soup.select("img.alignnone.size-full")
    for img in images:
        sc.download_file(complete_url(img.get("data-src")), folder+"/images", posted_date=upload_timestamp)

def complete_url(u: str) -> str:
    if not u.startswith("/"):
        return u
    return ifgw_config["url"] + u

def binary_search_len(page_fmt: str, cat:str=None):
    now = 10
    found = [0, None]
    if cat is not None:
        print(f"Binary searching for {cat}")
    while found[1] is None or abs(found[0]-found[1]) != 1:
        res = requests.get(page_fmt.format(page=now), headers=sc.headers)
        if res.status_code == 404:
            found[1] = now
        elif res.status_code >= 400:
            print(res.status_code)
            raise Exception(res.text)
        elif res.status_code < 400:
            found[0] = now
        if found[1] is None:
            now*=2
            continue
        now = round((found[0]+found[1])/2)
    if cat is not None:
        print(f"Done binary searching for {cat}, up to page {found[0]}")

    return [page_fmt.format(page=i) for i in range(found[1])]
    
def download_category(resource: str, link: str):
    urls = binary_search_len(link.format(page="{page}", cate=resource), resource)
    for u in urls:
        try:
            download_results_page(u, resource)
        except Exception as e:
            print(e)
            print(type(e))

srch = ifgw_config["url"] + "/page/{page}/?s={cate}"
ct = ifgw_config["url"] + "/category/{cate}/page/{page}/"
def main(resource_name: str, resource_type: str):
    try:
        download_category(resource_name, ct if resource_type == "category" else srch)
    except BaseException as e:
        print(e)
        print(type(e))
    finally:
        sc.destroy_sess()

