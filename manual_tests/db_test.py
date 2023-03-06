import datetime
from dataaccess.DB import DB
from dataaccess.mongo_db import MongoDB
from instance.config import MONGO_CONNECTION, MONGO_DB, MONGO_USER, MONGO_PASSWORD

mongo_db = MongoDB(MONGO_CONNECTION, MONGO_DB, MONGO_USER, MONGO_PASSWORD)
DB.get_instance().set_db_type(mongo_db)

# result = DB.get_instance().get_linked_in_data_by_username('davide-vanoni')

data = {
    'ip_address': '192.168.111.12',
    'user_agent': 'jajsjjss',
    'datetime': datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()
}
DB.get_instance().add_phish_trace("63ef4ba6c6c3ba1b561b87ff", data)
