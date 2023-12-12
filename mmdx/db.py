import threading
import sqlite3
from typing import NamedTuple, List, Dict, Optional


class DBConn(NamedTuple):
    conn: sqlite3.Connection
    cursor: sqlite3.Cursor


db_conns: Dict[str, threading.local] = {}


def get_db_connection(db_file: str) -> DBConn:
    # Get or create a thread-local variable for the given database file,
    # and use it to store SQLite db connections
    thread_local_db = db_conns.get(db_file, threading.local())
    # Check if the current thread already has a connection. If not,
    # create a new connection and set it as a thread-local variable
    if not hasattr(thread_local_db, "connection"):
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        thread_local_db.connection = DBConn(conn, cursor)
    return thread_local_db.connection


class LabelsDB:
    def __init__(self, db_file: str):
        self.db_file = db_file
        _, cursor = get_db_connection(db_file)
        self.tables = ["animal", "relevant", "description", "keywords"]
        self.create_tables(cursor)


    def create_tables(self, cursor):
        for table in self.tables:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    image_path TEXT,
                    label TEXT
                );
            """
            )

    def add(self, image_path: str, label: str, table: str):
        conn, cursor = get_db_connection(self.db_file)
        cursor.execute(
            f"INSERT INTO {table} (image_path, label) VALUES (?, ?);",
            (image_path, label),
        )
        conn.commit()

    def remove_records(self, image_path: str, label: str, table: str):
        conn, cursor = get_db_connection(self.db_file)
        cursor.execute(
            f"DELETE FROM {table} WHERE image_path=? AND label=?;",
            (image_path, label),
        )
        conn.commit()

    def get(self,  table: str, image_path: Optional[str] = None) -> List[str]:
        _, cursor = get_db_connection(self.db_file)
        if image_path is None:
            query = f"SELECT DISTINCT label FROM {table}"
            cursor.execute(query)
        else:
            cursor.execute(
                f"SELECT DISTINCT label FROM {table} WHERE image_path=?;",
                (image_path,),
            )
        return [row[0] for row in cursor.fetchall()]

    def counts(self) -> dict[str, int]:
        _, cursor = get_db_connection(self.db_file)
        cursor.execute("SELECT label, COUNT(*) FROM relevant GROUP BY label;")
        counts = {}
        for row in cursor.fetchall():
            counts[row[0]] = row[1]
        return counts

    def get_image_paths(self) -> List[str]:
        _, cursor = get_db_connection(self.db_file)
        cursor.execute("SELECT DISTINCT image_path FROM relevant;")
        return [row[0] for row in cursor.fetchall()]


    def create_zip_labeled_data(self) -> str:
        _, cursor = get_db_connection(self.db_file)
        query = """
            SELECT
                left_table.image_path,
                GROUP_CONCAT(description.label, ", ") AS descriptions,
                GROUP_CONCAT(keywords.label, ", ") AS negative_keywords,
                animal.label AS animal,
                relevant.label AS relevant
            FROM (
                SELECT image_path FROM description
                UNION
                SELECT image_path FROM keywords
                UNION
                SELECT image_path FROM animal
                UNION
                SELECT image_path FROM relevant
            ) AS left_table
            LEFT OUTER JOIN description
            ON left_table.image_path = description.image_path
            LEFT OUTER JOIN keywords
            ON left_table.image_path = keywords.image_path
            LEFT OUTER JOIN animal
            ON left_table.image_path = animal.image_path
            LEFT OUTER JOIN relevant
            ON left_table.image_path = relevant.image_path
            GROUP BY left_table.image_path;
        """
        cursor.execute(query)
        column_names = [column[0] for column in cursor.description]
        result = cursor.fetchall()
        return result, column_names
