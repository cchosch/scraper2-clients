import json
import datetime

import requests

prod = True
config = {}
with open("./config.json") as f:
    config = json.load(f)
if "proxy_username" not in config or "proxy_password" not in config or "proxy_url" not in config:
    raise Exception("config must have proxy_url, proxy_username, and proxy_password")

def fix_url(path: str):
    if path[0] == "/":
        path = path[1:]
    if prod:
      return "http://74.96.144.80:88/"+path
    return "http://localhost:88/"+path

requests.post(fix_url("/api/v1/signup"), json={"username": config["username"], "password": config["password"]})

def req(url: str, json=None, headers=None, method: str="get") -> requests.Response:
    res = requests.request(method, url, json=json, headers=headers)
    if int(str(res.status_code)[0]) > 3:
        raise requests.exceptions.HTTPError(res.text)
    return res

def get_config():
    return config

def get_prox_url():
    return config["proxy_url"].format(username=config["proxy_username"], password=config["proxy_password"])



def create_shoot(url: str):
    pass

class ScraperClient:
    def __init__(self, proxy: str=None, scraping_headers=None, download_headers=None) -> None:
        self.download_headers = download_headers
        self.headers = {"user-agent": "Mozilla/5.0"} if scraping_headers is None else scraping_headers
        self.proxy = proxy
        self.sess = None
        self.reload_login()

    def destroy_sess(self):
        if self.sess is None:
            return

        try:
            req(fix_url("/api/v1/session"), headers={"content-type": "application/json", "cookie": self.sess_cook()}, method="delete")
        except Exception as e:
            print(e)
            pass

    def reload_login(self) -> bool:
        try:
            self.destroy_sess()

            res = req(fix_url("/api/v1/login"), headers={"content-type": "application/json"}, json={
                "username": config["username"],
                "password": config["password"]
            }, method="post")

            if int(str(res.status_code)[0]) > 3:
                self.sess = None
                print(res.text)
                return False

            self.sess = res.cookies["sid"]
            return True
        except Exception as e:
            print(e)
            return False
    
    def load_webpage(self, url: str, use_proxy: bool=False) -> requests.Response | None:
        try:
            res =  requests.get(url, proxies=({
                "all": self.proxy 
            } if use_proxy else None), headers=self.headers)
            if res.status_code >= 400:
                print(res.text)
                return None
            return res
        except Exception as e:
            print(e)
            return None
    
    def sess_cook(self) -> str:
        if self.sess is None:
            return ""
        return f"sid={self.sess}"

    def download_file(self, url: str, fold: str, posted_date: datetime.datetime = None, use_proxy: bool=False):
        if self.sess is None:
            if not self.reload_login():
                print(f"Session inactive, tried to reload and that didn't work, not downloading {url}")
        print(f"downloading {url}")
        data = {
            "fold_path": fold,
            "url": url,
        }

        if self.download_headers:
            data["headers"] = self.download_headers

        if posted_date is not None:
            data["upload_date"] = posted_date.strftime("%Y-%m-%dT%H:%M:%S")
        if use_proxy:
            data["proxy_url"] = self.proxy

        res = requests.post(fix_url("/api/v1/file/download"), json=data, headers={
            "cookie": self.sess_cook(),
            "content-type": "application/json"
        })
        first_stat = int(str(res.status_code)[0])
        if first_stat > 3:
            print(res.text)
            print(res.json())
