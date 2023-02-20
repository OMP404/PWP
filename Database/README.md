Python version 3.8
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
