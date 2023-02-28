from dataaccess.DB import DB
from dataaccess.mongo_db import MongoDB
from instance.config import MONGO_CONNECTION, MONGO_DB, MONGO_USER, MONGO_PASSWORD

mongo_db = MongoDB(MONGO_CONNECTION, MONGO_DB, MONGO_USER, MONGO_PASSWORD)
DB.get_instance().set_db_type(mongo_db)

result = DB.get_instance().get_linked_in_data_by_username('davide-vanoni')
