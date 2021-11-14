import sqlite3
from logfile import input_log, MES, ER


def connecting():
    try:
        connection = sqlite3.connect("database.db")
        connection.cursor()
        return connection
    except Exception as ex:
        input_log(ER, f'DB connecting error: {ex}')


def save_file_path(file_path, redacted=False):
    try:
        connection = connecting()
        cursor = connection.cursor()
        type_exp = file_path.split('.')[-1]
        cursor.execute(f"""INSERT INTO Files(file_path, type_file, date, redacted) 
                           VALUES ('{file_path}', 
                           (SELECT id_type FROM type_file WHERE type = '{type_exp}'),
                           datetime('now', '+3 hours'),
                           {'TRUE' if redacted else 'FALSE'})""")
        connection.commit()
        connection.close()
        input_log(MES, 'DB save path')
    except Exception as ex:
        input_log(ER, f'DB saving error: {ex}')


def get_last_paths(limit=10, where=''):
    try:
        connection = connecting()
        cursor = connection.cursor()
        result = cursor.execute(f"""SELECT file_path, date, redacted FROM Files {where}
                                    ORDER BY date LIMIT {limit}""").fetchall()
        connection.close()
        input_log(MES, 'DB find paths')
        return result
    except Exception as ex:
        input_log(ER, f'DB Find error: {ex}')
        return []


def delete_all_paths():
    try:
        connection = connecting()
        cursor = connection.cursor()
        cursor.execute("""DELETE FROM Files""")
        connection.commit()
        connection.close()
        input_log(MES, 'DB delete all paths')
    except Exception as ex:
        input_log(ER, f'DB Delete error: {ex}')
