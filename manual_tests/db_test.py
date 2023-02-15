from db import DB
from instance.config import MONGO_HOST, MONGO_PORT, MONGO_DB

mydict = {
    "brand": "Ford",
    "model": "Mustang",
    "year": 1964
}

db = DB(MONGO_HOST, MONGO_PORT, MONGO_DB)
db.add_session(mydict, mydict, "abc", "def")
