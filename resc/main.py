import sys
import auxillary
import requests
from flask import Flask, Response, jsonify

PORT = 5001
BASE_URL = f"http://localhost:{PORT}"
API_URL = f"{BASE_URL}/api/"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 35


app = Flask(__name__)

@app.route('/auxillary/<int:ranking>/')
def get_ranking(ranking=1):

    value_list = auxillary.get_bars()
   
    if int(ranking) < len(value_list):
        return jsonify(value_list[int(ranking)-1])
    else:
         return Response(f"There is not enough drinks ({len(value_list)}) in to fullfill your thirst", 416)


if __name__ == "__main__":
    #if you have distinct testing enviroment, this may come handy
    if len(sys.argv) == 3:
        try:
            BASE_URL = "http://"+sys.argv[1].strip()+":"
            PORT = int(sys.argv[2])
            print(BASE_URL, PORT)
        except ValueError as e:
            print("Failed to read user specified input!")
            sys.exit(-1)

    api_entrypoint = requests.get(auxillary.BASE_URL + '/api/', timeout=TIMEOUT)
    app.run(host="localhost", port=PORT)
