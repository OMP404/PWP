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
