import sqlite3

class Database:
    def __init__(self) -> None:
        self.database_file_path = 'DATABASE_FILE_PATH'

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_file_path)

    def cursor(self, *, connect: sqlite3.Connection) -> sqlite3.Cursor:
        return connect.cursor()

    #保存して閉じる
    def save(self, *, connect: sqlite3.Connection) -> None:
        connect.commit()
        connect.close()

    #閉じるだけ　保存しない　編集してない時に使う
    def close(self, *, connect: sqlite3.Connection) -> None:
        connect.close()

class PlayerAttendanceDatabase(Database):
    def __init__(self) -> None:
        self.database_file_path = 'player_attendance.db'
        self.create_table()

    def create_table(self) -> None:
        connect = self.connect()
        cursor = self.cursor(connect=connect)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_attendance(
                Team TEXT,
                first_game TEXT,
                second_game TEXT,
                date TEXT,
                UNIQUE(Team, date)
            )
        ''')
        self.save(connect=connect)

    def register(self, *, Team: str, first_game: str, second_game: str, date: str) -> None:
        connect = self.connect()
        cursor = self.cursor(connect=connect)
        cursor.execute('''
            INSERT OR REPLACE INTO player_attendance(Team, first_game, second_game, date)
            VALUES(?, ?, ?, ?)
        ''', (Team, first_game, second_game, date))
        self.save(connect=connect)

    def get_today(self, *, Team: str, date: str) -> tuple:
        connect = self.connect()
        cursor = self.cursor(connect=connect)
        cursor.execute('''
            SELECT first_game, second_game
            FROM player_attendance
            WHERE Team = ? AND date = ?
        ''', (Team, date))
        return cursor.fetchone()

    def get_team_all_register(self, *, Team: str) -> list:
        """
        Args:
            Team (str): チーム名
        Returns:
            list: チームの全登録情報
        """
        connect = self.connect()
        cursor = self.cursor(connect=connect)
        cursor.execute('''
            SELECT *
            FROM player_attendance
            WHERE Team = ?
        ''', (Team,))
        return cursor.fetchall()