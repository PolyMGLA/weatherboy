import sqlite3
from sqlite3 import Error
import logging
import datetime

FORMAT = r'%Y-%m-%d %H:%M:%S'

class UserManager:
    CREATE_DATABASE_QUERY = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  city TEXT NOT NULL,
  timer DATETIME NOT NULL,
  delay INTEGER NOT NULL DEFAULT(1800)
);
"""

    DROP_DATABASE_QUERY = """
DROP TABLE users;
"""
    def __init__(self, dbname) -> None:
        self.conn = self.create_connection(dbname)
        logging.basicConfig(filename="logs.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

    def create_connection(self, path) -> sqlite3.Connection:
        conn = None
        try:
            conn = sqlite3.connect(path)
            print("Connection to SQLite DB successful")
        except Error as e:
            print(f"The error '{e}' occurred")

        return conn

    def execute_query(self, query) -> None:
        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
            self.conn.commit()
            q = query.replace("\n", " ")
            # print("Query executed successfully -", q)
            logging.info(f'Query executed successfully - "{q}"')
        except Error as e:
            # print(query)
            # print(f"The error '{e}' occurred")
            logging.info(f"The error '{e}' occurred in '" + query + "'")

    def execute_read_query(self, query) -> list[any]:
        cursor = self.conn.cursor()
        result = None
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            # print(query)
            # print(f"The error '{e}' occurred")
            return []

    def INIT(self) -> None:
        self.execute_query(self.CREATE_DATABASE_QUERY)
        
    def DROP_ALL(self) -> None:
        self.execute_query(self.DROP_DATABASE_QUERY)

    def RECREATE(self) -> None:
        self.DROP_ALL()
        self.INIT()

    def register(self, tid, city) -> None:
        self.execute_query(f"INSERT INTO users (id, city, timer) VALUES ({tid}, \"{city}\", '{datetime.datetime.now().strftime(FORMAT)}')")
    
    def update_city(self, tid, city) -> None:
        self.execute_query(f"UPDATE users SET city='{city}' WHERE id={tid}")
    
    def update_timer(self, tid, timer = 0) -> None:
        FORMAT = r'%Y-%m-%d %H:%M:%S'
        self.execute_query(f"UPDATE users SET timer='{datetime.datetime.fromtimestamp(datetime.datetime.now().timestamp() + timer).strftime(FORMAT)}' WHERE id={tid}")

    def update_delay(self, tid, delay) -> None:
        self.execute_query(f"UPDATE users SET delay='{delay}' WHERE id={tid}")
    
    def get_userlist(self) -> list[any]:
        return self.execute_read_query("SELECT * FROM users")
    
    def get_city(self, user_id) -> list[any]:
        """
        Получение из базы данных города пользователя tid

        :param user_id: UserID пользователя в боте
        """
        return self.execute_read_query(f"SELECT city FROM users WHERE id={user_id}")[0][0]
