import csv
import io
from datetime import datetime

from dataaccess.DB import DB


def export_all_mails() -> tuple[str, bytes]:
    data = DB.get_instance().get_ai_request_response()

    dt = datetime.now()
    str_date = dt.strftime('%Y%m%d_%H%M%S')
    filename = 'data_' + str_date + '.csv'

    fieldnames = data[0].keys() if any(data) else []

    return filename, __generate_csv(fieldnames, data)


def __generate_csv(fieldnames: list[str], data: list[dict]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for item in data:
        writer.writerow(item)
    return output.getvalue().encode('utf-8')
