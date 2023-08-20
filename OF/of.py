import ast
import hashlib
import json
import sys
import time
import urllib.parse
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

config = {}
with open("./OF/client.json") as f:
    config = json.load(f)

if config["url"][-1] != "/":
    config["url"] = config["url"]+"/"
cl_headers = config["headers"]

def api(path: str) -> str:
    return f"{config['url']}api2/v2/"+path

RESPONSE_LIMIT=10
sc = base.ScraperClient(base.get_prox_url(), download_headers=cl_headers)
dyna_rules: dict = json.loads(requests.get("https://raw.githubusercontent.com/deviint/onlyfans-dynamic-rules/main/dynamicRules.json").content)
def sec_from_iso(iso_date: str):
    return str(round(datetime.fromisoformat(iso_date).timestamp()))

def get_data_source(res: dict) -> list[dict]:
    seen = []
    comp = {}
    for vfirst in range(len(res["list"])): # foreach post in list
        if not "media" in res["list"][vfirst].keys():
            continue
        for v in res["list"][vfirst]["media"]: # foreach media in 
            comp = {"source": v["info"]["source"]["source"], "type": v["type"], "date": res["list"][vfirst]["postedAt"], "id": v["id"]}
            if "drm" in v["files"] and "hls" in v["files"]["drm"]["signature"]:
                sig = v["files"]["drm"]["signature"]["hls"]
                comp["hls"] = v["files"]["drm"]["manifest"]["hls"]+"?Policy="+sig["CloudFront-Policy"]+"&Signature="+sig["CloudFront-Signature"]+"&Key-Pair-Id="+sig["CloudFront-Key-Pair-Id"]
            if comp in seen:
                continue
            seen.append(comp)
    return seen

def create_signed_headers(link: str, heads:dict=None) -> dict:
    OF_HEAD: dict = cl_headers if heads is None else heads

    final_time = str(round(time.time()))
    path = urllib.parse.urlparse(link).path
    query = urllib.parse.urlparse(link).query
    path = path if not query else f"{path}?{query}"
    a = [dyna_rules["static_param"], final_time, path, str(OF_HEAD["user-id"])]
    msg = "\n".join(a)
    message = msg.encode("utf-8")
    hash_object = hashlib.sha1(message)
    sha_1_sign = hash_object.hexdigest()
    sha_1_b = sha_1_sign.encode("ascii")
    checksum = (
        sum([sha_1_b[number] for number in dyna_rules["checksum_indexes"]])
        + dyna_rules["checksum_constant"]
    )

    OF_HEAD["sign"] = dyna_rules["format"].format(sha_1_sign, abs(checksum))
    OF_HEAD["time"] = final_time
    
    new_head = {}
    for header in sorted(OF_HEAD.items()):
        new_head[header[0]] = header[1]
    return new_head

def dict_to_urlparams(params: dict={}, override_defualt: bool=False) -> str:
    if override_defualt == True and params == {}:
        return ""
    default_dict = {
        "limit": str(RESPONSE_LIMIT),
        "order": "publish_date_desc",
        "skip_users":"all",
        "counters": "0",
        "format": "infinite"
    }
    if override_defualt == False:
        for param in params.keys():
            default_dict[param] = params[param]
    else:
        default_dict = params
    final = "?"
    for param in default_dict.keys():
        final+=f"{param}={default_dict[param]}&"
    return final[0: len(final)-1]

def get_of_link(url: str) -> requests.Response | None:
    return sc.load_url(url, create_signed_headers(url), True)

def user_from_name(username: str):
    print(f"getting {username}")
    return get_of_link(api(f"users/{username}")).json()

def get_all_media(user: dict):
    new_pub_time = {}
    results = []
    while True:
        url = api(f"users/{user['id']}/posts/medias"+dict_to_urlparams(new_pub_time))
        media_res = get_of_link(url)
        print(url)
        if media_res is None:
            break
        media = media_res.json()
        for data in get_data_source(media):
            if data["source"] is None:
                continue
            results.append(data)

        if not media["hasMore"]:
            break

        new_pub_time = {"beforePublishTime": str(sec_from_iso(media["list"][len(media["list"])-1]["postedAt"]))+".000000"}
    return results

def download_model_media(username: str):
    user = user_from_name(username)
    all_media = get_all_media(user)
    for item in all_media:
        sc.download_headers = create_signed_headers(item["source"])

        sc.download_file(item["source"], username+"/"+item["type"], datetime.fromisoformat(item["date"]), True, name=item["source"].split("/")[-1].split("?")[0])

def main(username: str):
    try:
        download_model_media(username)
    except BaseException as e:
        print(e)
        print(type(e))
    finally:
        sc.destroy_sess()

