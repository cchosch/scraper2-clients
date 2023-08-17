import argparse
import IFGW.ifgw
import functools

parser = argparse.ArgumentParser(description="Scraper2 Downloader CLI")
subparsers = parser.add_subparsers(dest="service")

ifgw_parser = subparsers.add_parser("IFGW", help="Scrape from IFGW")
ifgw_parser.add_argument("resource", help="Name of resource to scrape (e.g. alinity)")
ifgw_parser.add_argument("-t", "--type", required=False, help="Type of resource to scrape", choices=["category", "search"], default="search")

args = parser.parse_args()
config = vars(args)

def format_args(args: dict) -> str:
    return functools.reduce(lambda p, c: f"{p} {c}", map(lambda x: f"{x}={args[x]}", filter(lambda x: x != "service" , args.keys())))

if config["service"] == "IFGW":
    IFGW.ifgw.main(config["resource"], config["type"])
