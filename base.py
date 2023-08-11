import json

import requests

prod = True
config = {}
with open("./config.json") as f:
    config = json.load(f)
if "proxy_username" not in config or "proxy_password" not in config or "proxy_url" not in config:
    raise Exception("config must have proxy_url, proxy_username, and proxy_password")

def url(path: str):
    if path[0] == "/":
        path = path[1:]
    if prod:
      return "http://74.96.144.80:88/"+path
    return "http://localhost:88/"+path

requests.post(url("/api/v1/signup"), json={"username": config["username"], "password": config["password"]})

def req(url: str, json=None, headers=None, method: str="get") -> requests.Response:
    res = requests.request(method, url, json=json, headers=headers)
    if int(str(res.status_code)[0]) > 3:
        raise requests.exceptions.HTTPError(res.text)
    return res

def get_config():
    return config

def get_prox_url():
    return config["proxy_url"].format(username=config["proxy_username"], password=config["proxy_password"])

def destroy_sess(sess: str):
    try:
        req(url("/api/v1/session"), headers={"content-type": "application/json", "cookie": sess}, method="delete")
    except Exception as e:
        print(e)
        pass

def reload_login() -> str:
    res = req(url("/api/v1/login"), headers={"content-type": "application/json"}, json={
        "username": config["username"],
        "password": config["password"]
    }, method="post")

    if int(str(res.status_code)[0]) > 3:
        print(res.text)
        destroy_sess("sid="+res.cookies["sid"])
        quit()
    return "sid="+res.cookies["sid"]


def create_shoot(url: str):
    pass
