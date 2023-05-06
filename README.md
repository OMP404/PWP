# PWP SPRING 2023
# PROJECT NAME
# Group information
* Student 1. Saku Antikainen santikai19@student.oulu.fi
* Student 2. Olli Paananen opaanane19@student.oulu.fi
* Student 3. Joose Yrjänäinen jyrjanai18@student.oulu.fi

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__

# Running the project

Project is developed, ran and tested on python versions 3.9 and above. Please consider using it or newer.
Usage of pyenv & venv is suggested, albeit not mandatory.

The project requirements are as follows
| Module          	| Version 	|
|-----------------	|---------	|
| Flask           	| 2.1.3   	|
| flask_restful   	| 0.3.9   	|
| flask_sqalchemy 	| 2.5.1   	|
| flasgger        	| 0.9.5   	|
| jsonschema      	| 4.17.3  	|
| SQLAlchemy      	| 1.4.39  	|
| Werkzeug        	| 2.2.3   	|
|                 	|         	|

## Initial steps
    1. clone project
    2. navigate to the project directory
## Install and dependencies
    3. Required dependencies for this project are in the requirements.txt -file, you can install them by running:
```pip install -r requirements.txt```
    
    4. running the flask project
```flask run```
    
    after the starup-process the development server can be found at http://127.0.0.1:5000/

## Starting

### Client requirements:

The client requirements are as follows

| Module        	| Version 	|
|---------------	|---------	|
| customtkinter 	| 5.0.3   	|
| requests      	| 2.28.1  	|

    5. to run the client, please
```cd client```

```bash python3 main.py```

    After the startup, you can reach API at ```localhost:5000``` 
## Running tests

## Misc. & documentation

    By default, the documentation of projectwork can be found at
```localhost:5000/apidocs/```
