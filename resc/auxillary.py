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


def show_bar_info(jsondata):
    cocktails = jsondata['items']
    print("this is info", cocktails)


def show_error(response):
    print("responded with an error: ", response.status_code)