import sqlite3
from enum import IntEnum

_db_path = None


class UserState(IntEnum):
    """The states the user can be in"""

    idle = 1
    send_timezone = 2


class User:
    """The class to represent users of this bot"""

    def __init__(
        self, telegram_id: int, state: UserState, timezone: str, analyzes: int
    ):
        self.telegram_id = telegram_id
        self.state = state
        self.timezone = timezone
        self.analyzes = analyzes

    def _create(self):
        """Add the user to the db"""
        query = "INSERT INTO users VALUES (?, ?, ?, ?)"
        conn = sqlite3.connect(_db_path)
        cur = conn.cursor()
        cur.execute(
            query,
            (self.telegram_id, int(self.state), self.timezone, self.analyzes),
        )
        conn.commit()
        conn.close()

    def update(self):
        """Update the user to the db"""
        query = (
            "UPDATE users SET state=?, timezone=?, analyzes=? "
            "WHERE telegram_id=?"
        )
        conn = sqlite3.connect(_db_path)
        cur = conn.cursor()
        cur.execute(
            query,
            (int(self.state), self.timezone, self.analyzes, self.telegram_id,),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def load(telegram_id: int):
        """Load a user with the specified telegegramid from the DB"""
        query = "SELECT * FROM users WHERE telegram_id = ?"
        conn = sqlite3.connect(_db_path)
        cur = conn.cursor()
        cur.execute(query, (telegram_id,))
        result = cur.fetchone()
        conn.close()

        # The user is not yet in the database
        if result is None:
            user = User(telegram_id, UserState.idle, "UTC", 0)
            user._create()
            return user

        return User(result[0], result[1], result[2], result[3])

    @staticmethod
    def statistics() -> (int, int):
        """Create statistics about the bots usage"""
        user_query = "SELECT COUNT(*) FROM users"
        analyzes_query = "SELECT SUM(analyzes) FROM users"
        conn = sqlite3.connect(_db_path)
        cur = conn.cursor()
        users = cur.execute(user_query).fetchone()[0]
        analyzes = cur.execute(analyzes_query).fetchone()[0]
        conn.close()
        return users, analyzes


def __init__(db_path: str):
    global _db_path
    _db_path = db_path
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query = (
        "CREATE TABLE IF NOT EXISTS users "
        "(telegram_id INTEGER NOT NULL PRIMARY KEY, state INTEGER, "
        "timezone TEXT, analyzes INTEGER)"
    )
    cur.execute(query)
    conn.commit()
    conn.close()

