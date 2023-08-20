import argparse
import functools

import IFGW.ifgw
import OF.of

parser = argparse.ArgumentParser(description="Scraper2 Downloader CLI")
subparsers = parser.add_subparsers(dest="service")

ifgw_parser = subparsers.add_parser("IFGW", help="Scrape from IFGW")
ifgw_parser.add_argument("resource", help="Name of resource to scrape (e.g. alinity)")
ifgw_parser.add_argument("-t", "--type", required=False, help="Type of resource to scrape", choices=["category", "search"], default="search")

ifgw_parser = subparsers.add_parser("OF", help="Scrape from IFGW")
ifgw_parser.add_argument("username", help="Model's username")

args = parser.parse_args()
config = vars(args)

def format_args(args: dict) -> str:
    return functools.reduce(lambda p, c: f"{p} {c}", map(lambda x: f"{x}={args[x]}", filter(lambda x: x != "service" , args.keys())))

if config["service"] == "IFGW":
    IFGW.ifgw.main(config["resource"], config["type"])

if config["service"] == "OF":
    OF.of.main(config["username"])
