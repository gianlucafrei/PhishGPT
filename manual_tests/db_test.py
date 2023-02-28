from dataaccess import db
from instance.config import MONGO_CONNECTION, MONGO_DB, MONGO_USER, MONGO_PASSWORD

mydict = {
    'brand': 'Ford',
    'model': 'Mustang',
    'year': 1964
}

db.connect(MONGO_CONNECTION, MONGO_DB, MONGO_USER, MONGO_PASSWORD)
# db.add_phish(mydict, False, mydict, mydict, 'def')

db.get_linked_in_data_by_username('davide-vanoni')
