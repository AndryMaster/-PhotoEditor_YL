import datetime as dt
import csv

ER = "<Error>"
MES = "Message"
END = "Closing program"
LOGFILE_PATH = "logfile.csv"


def input_log(type_mes, message):
    with open(LOGFILE_PATH, 'a', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([dt.datetime.now().strftime('%Y-%b-%d %H:%M:%S.%f'), type_mes, message])
        if message == END:
            writer.writerow(['-' * 27, '-' * 7, '-' * 44])  # 80-
