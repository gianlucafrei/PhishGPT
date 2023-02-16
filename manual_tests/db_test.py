from db import DB
from instance.config import MONGO_CONNECTION, MONGO_DB, MONGO_USER, MONGO_PASSWORD

mydict = {
    "brand": "Ford",
    "model": "Mustang",
    "year": 1964
}

db = DB(MONGO_CONNECTION, MONGO_DB, MONGO_USER, MONGO_PASSWORD)
db.add_phish(mydict, False, mydict, mydict, "def")
