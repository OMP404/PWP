"""
An Auxillary API for the Oulu Bars API, purpose of this work is to prove the workings of Oulu Bars API and to show one of its usecases.
"""

import json
from operator import itemgetter
import requests

PORT = 5000
BASE_URL = f"http://localhost:{PORT}"
API_URL = f"{BASE_URL}/api/"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 5

list_of_drinks = []


def get_bars():
    bars = requests.get(f"{API_URL}bars/", timeout=TIMEOUT)
    if bars.status_code != 200:
        print("Unfortunately it seems to be that there is no bars to go :(")
    else:
        jsondata = json.loads(bars.text)
        get_bar_information(jsondata)
    return list_of_drinks


def get_bar_information(jsondata):
    if len(jsondata["items"]) != 0:
        print("You are in luck! There seems to be bars available! Fetching drinks")
    for bar in jsondata["items"]:
        # print(bar)
        fetch_bar_catalogue(bar["@controls"]["self"]["href"])
    sort_by_price()


def fetch_bar_catalogue(location):
    print("fetching from: {}", location)
    catalogue_json = requests.get(f"{BASE_URL}{location}cocktails/", timeout=TIMEOUT)
    if catalogue_json.status_code == 200:
        bar_catalog = json.loads(catalogue_json.text)
        update_to_list_of_drinks(bar_catalog["items"])
    else:
        show_error(catalogue_json)
    catalogue_json = requests.get(f"{BASE_URL}{location}tapdrinks/", timeout=TIMEOUT)
    if catalogue_json.status_code == 200:
        bar_catalog = json.loads(catalogue_json.text)
        update_to_list_of_drinks(bar_catalog["items"])
    else:
        show_error(catalogue_json)


def update_to_list_of_drinks(bar_catalogue):
    list_of_drinks.extend(bar_catalogue)


def sort_by_price():
    list_of_drinks.sort(key=itemgetter("price", "bar_name"))


def show_bar_info(jsondata):
    cocktails = jsondata["items"]
    print("this is info", cocktails)


def show_error(response):
    print("responded with an error: ", response.status_code)
