import psycopg2
import logging
from config import dbname, user, password, host, port
def db_connect():
    try:
        connection = psycopg2.connect(
            database=dbname,
            host=host,
            port=port,
            user=user,
            password=password
        )
        return connection
    except Exception as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        return None

def create_tables():
    try:
        connection = db_connect()
        if connection is None:
            logging.error("Подключение к базе данных не удалось.")
            return
        
        cursor = connection.cursor()
        
        # Создание таблицы users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                tg_id BIGINT UNIQUE NOT NULL,
                username TEXT
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(tg_id),
                title TEXT NOT NULL,
                deadline DATE NOT NULL,
                status TEXT DEFAULT 'pending'
            );
            CREATE TABLE IF NOT EXISTS habits (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(tg_id),
                title TEXT NOT NULL,
                frequency TEXT NOT NULL,
                streak INT DEFAULT 0
            );
        """)

        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        logging.error(f"Ошибка при создании таблиц: {e}")

def execute_query(query, params=None):
    """
    Выполняет SQL-запрос, переданный в параметре query.

    :param query: Строка SQL-запроса.
    :param params: Кортеж с параметрами для подстановки в запрос.
    :return: Результаты запроса (для SELECT) или None.
    """
    try:
        connection = db_connect()
        if connection is None:
            logging.error("Не удалось подключиться к базе данных.")
            return None
        
        cursor = connection.cursor()

        # Выполняем запрос
        cursor.execute(query, params)

        # Если это SELECT-запрос, возвращаем результат
        if query.strip().lower().startswith("select"):
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            return results
        
        # Для остальных запросов фиксируем изменения
        connection.commit()
        cursor.close()
        connection.close()
        return None

    except Exception as e:
        logging.error(f"Ошибка при выполнении запроса: {e}")
        return None