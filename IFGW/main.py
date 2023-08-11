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
    from clients import base
except ImportError:
    import base

if len(sys.argv) < 2:
    print(sys.argv)
    print("pass category name as argument")
    quit()

cl_headers = {}
with open("./IFGW/client.json") as f:
    cl_headers = json.load(f)["headers"]

proxies = {
    "https": base.get_prox_url()
}

r: requests.Session = requests.session()
r.headers = {"user-agent": "Mozilla/5.0"}

name = sys.argv[1]
folder = name.replace("-", " ")

download_headers = {
    "content-type": "application/json",
    "cookie": base.reload_login()
}

me = requests.get(base.url("/api/v1/me"), headers=download_headers)

if "error" in me.json():
    print(me.json())
    quit()

def prox_retry(url: str, max: int =10):
    rtrs = 0

    while rtrs < max:
        try:
            res = r.get(url, proxies=proxies)
            return res
        except urlexcepts.NewConnectionError:
            rtrs+=1
            time.sleep(0.1)

def download_file(url: str, fold: str, posted_date: str =None, use_proxy: bool=False):
    print(f"downloading {url}")
    data = {
        "fold_path": fold,
        "url": url,
        "headers": cl_headers
    }   

    if posted_date is not None:
        data["upload_date"] = posted_date
    if use_proxy:
        data["proxy_url"] = proxies["https"]

    res = requests.post(base.url("/api/v1/file/download"), json=data, headers=download_headers)
    first_stat = int(str(res.status_code)[0]);
    if first_stat > 3:
        print(res.text)
        print(res.json())

def download_results_page(url: str):
    res = prox_retry(url)
    if int(str(res.status_code)[0]) > 3:
        raise Exception(res.text)
    soup = BeautifulSoup(res.text, features="html.parser")
    page_articles = []
    for h3_node in soup.find_all("h3", {"class", "g1-gamma g1-gamma-1st entry-title"}):
        page_articles.append(h3_node.findChild("a", recursive=True).get("href"))

    for art in page_articles:
        try:
            download_article(art)
        except Exception as e:
            print(f"skipping {art} due to {e}")

def download_article(url: str):
    print(url)
    res = prox_retry(url)
    if int(str(res.status_code)[0]) > 3:
        raise Exception(res.text)
    soup = BeautifulSoup(res.text, features="html.parser")
    video = soup.find("video")
    datetime = parser.parse(soup.find("time").get("datetime")).strftime("%Y-%m-%dT%H:%M:%S")

    if video is not None:
        vid_src: str = video.findChild("source").get("src")
        for bad_cdn in ["cdn03", "cdn02", "cdn01"]:
            if bad_cdn in vid_src:
                vid_src = vid_src.replace(bad_cdn, "cdn04")
        download_file(vid_src, folder+"/videos", posted_date=datetime)
        pass

    images = soup.select("img.alignnone.size-full")
    for img in images:
        download_file(img.get("data-src"), folder+"/images", posted_date=datetime)
        pass

def binary_search_len(page_fmt: str, cat:str=None):
    now = 10
    found = [0, None]
    if cat is not None:
        print(f"Binary searching for {cat}")
    while found[1] is None or abs(found[0]-found[1]) != 1:
        res = prox_retry(page_fmt.format(page=now))
        if res.status_code == 404:
            found[1] = now
        elif res.status_code >= 400:
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
    
srch = "https://influencersgonewild.com/page/{page}/?s={cate}"
ct = "https://influencersgonewild.com/category/{cate}/page/{page}/"
def download_category(cat: str):
    urls = binary_search_len(ct.format(page="{page}", cate=cat), cat)
    for u in urls:
        try:
            download_results_page(u)
        except Exception as e:
            print(e)
            print(type(e))

try:
    download_category(name)
except BaseException as e:
    print(e)
    print(type(e))
finally:
    base.destroy_sess(download_headers["cookie"])
