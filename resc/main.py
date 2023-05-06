import sys
from flask import Flask, Response, jsonify

PORT = 5001
BASE_URL = f"http://localhost:{PORT}"
API_URL = f"{BASE_URL}/api/"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 35


if __name__ == "__main__":
    if len(sys.argv) == 3:
        try:
            BASE_URL = "http://"+sys.argv[1].strip()+":"
            PORT = int(sys.argv[2])
            print(BASE_URL, PORT)
        except ValueError as e:
            print("Failed to read user specified input!")
            sys.exit(-1)

