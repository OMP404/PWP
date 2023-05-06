# Bar API auxillary Client

This simple Python API for the Oulu Bars API is meant to show the usability and productivity of our Bar API

## Installation

To install depencencies:

```bash
pip install -r requirements.txt
```

## Usage

Make sure the API server is running with a working database before proceeding or at least know where its currently hosted.
You don't have to host it yourself, as this aux API is meant to use the main BAR API to show its capabilities.

Simply run python file **main.py**

```bash
python main.py
```

you can specify address and port by:

```bash
python main.py address port
```

after running this service you can GET request for example http://ip:port/topdrinks/1 to get the best tip for evening refreshments.
