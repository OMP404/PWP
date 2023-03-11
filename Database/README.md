The Python version is 3.8

The database is SQLite version 3.39.2

The database can be created with the app.py file using the following commands in the same directory as the file :

```
from app import db
from app import app
ctx = app.app_context()
ctx.push()
db.create_all()
ctx.pop()
```
The database was managed and populated using the SQLite DB Browser https://sqlitebrowser.org/ Version 3.12.2

In the "Execute SQL" tab, use the following commands to first create the bar item:

```
INSERT INTO Bar("name", "address") 
VALUES ('<the name of the bar>', '<physical address of the bar>');
```

After that you can start adding drinks from the restaurants menu witht the following commands:

```
INSERT INTO Tapdrink("bar_name", "drink_type","drink_name","drink_size", "price") 
VALUES ('<the name of the bar>', '<the type of the drink>', '<the name of the drink>', '<the size of the drink in liters>', <the price of the drink>);
```

```
INSERT INTO Cocktail("bar_name", "coktail_name", "price") 
VALUES ('<the name of the bar>', '<the name of the cocktail>',  <the price of the drink>);
```

