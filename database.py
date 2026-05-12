import os
import dotenv

from dbutils.pooled_db import PooledDB
import pymysql
import pymysql.err

# load_dotenv(override=True): shell exports (e.g. DB_NAME=todoapp) must not beat .env
dotenv.load_dotenv(override=True)


# DB name from env, else defaultdb. No I/O; cannot error.
def _db_name() -> str:
    n = (os.getenv("DB_NAME") or "").strip().strip("'\"")
    return n if n else "defaultdb"


class Database:
    # Open PyMySQL pool. Errors: unknown DB (1049) -> RuntimeError with hint; other OperationalError re-raised.
    def __init__(self):
        try:
            self.pool = PooledDB(
                creator=pymysql,
                maxconnections=5,
                mincached=2,
                blocking=True,
                ping=1,
                cursorclass=pymysql.cursors.DictCursor,
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=_db_name(),
                # REQUIRED FOR AIVEN:
                ssl={"ssl": True},
                charset="utf8mb4",
            )
        except pymysql.err.OperationalError as e:
            if e.args and e.args[0] == 1049:
                raise RuntimeError(
                    "MySQL database from DB_NAME does not exist. On Aiven set DB_NAME=defaultdb "
                    "(the service database), not todoapp."
                ) from e
            raise

    # Run SELECT-style SQL; returns rows. Connection always closed in finally; DB errors propagate.
    def query(self, sql, params=None):
        connection = self.pool.connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchall()
        finally:
            connection.close()

    # Create/upgrade tables if missing. Connection closed in finally; DDL/SQL errors propagate.
    def setup_db(self):
        try:
            connection = self.pool.connection()
            cursor = connection.cursor()

            # Tables are created in DB_NAME (pool is already connected to that database).

            #creating users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `users` (
                    `userID` INT AUTO_INCREMENT PRIMARY KEY,
                    `name` VARCHAR(255),
                    `password` VARCHAR(255),
                    `email` VARCHAR(255)
                )
            """)

            #creating tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `tasks` (
                    `taskID` INT AUTO_INCREMENT,
                    `userID` INT NOT NULL,
                    `task_name` VARCHAR(255),
                    `status` CHAR,
                    `due_date` DATETIME,
                    `date_created` DATETIME,
                    `last_reminder_date` DATETIME,
                    `reminder_freq_day` TINYINT,
                    `reminder_freq_hour` TINYINT,
                    `tags` VARCHAR(255),
                    PRIMARY KEY (`taskID`, `userID`),
                    FOREIGN KEY (`userID`) REFERENCES `users`(`userID`)
                )
            """)

            #creating notes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `notes` (
                    `noteID` INT AUTO_INCREMENT,
                    `userID` INT NOT NULL,
                    `date_time` DATETIME,
                    `note_title` VARCHAR(255),
                    `contents` LONGTEXT,
                    PRIMARY KEY (`noteID`, `userID`),
                    FOREIGN KEY (`userID`) REFERENCES `users`(`userID`)
                )
            """)

            #creating files table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS `files` (
                `fileID` INT AUTO_INCREMENT,
                `userID` INT NOT NULL,
                `link` VARCHAR(255),
                `local_file_address` VARCHAR(255),
                PRIMARY KEY (`fileID`, `userID`),
                FOREIGN KEY (`userID`) REFERENCES `users`(`userID`)
            )  
            """)

            # Creating premium table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS `premium` (
                `userID` INT NOT NULL PRIMARY KEY,
                `account_status` CHAR,
                `billing_address` VARCHAR(255),
                `re_bill_date` DATETIME,
                `payment` VARCHAR(255),
                `amount` DECIMAL(10, 2),
                FOREIGN KEY (`userID`) REFERENCES `users`(`userID`)
            )
            """)

            # Old installs / todoapp_setup.sql created premium without amount; IF NOT EXISTS does not add columns.
            cursor.execute(
                """
                SELECT COUNT(*) AS cnt FROM information_schema.columns
                WHERE table_schema = DATABASE() AND table_name = 'premium' AND column_name = 'amount'
                """
            )
            row = cursor.fetchone() or {}
            # Pool uses DictCursor: rows are dicts, not tuples — do not use fetchone()[0].
            n = row.get("cnt")
            if n is None and row:
                n = next(iter(row.values()))
            if int(n or 1) == 0:
                cursor.execute(
                    "ALTER TABLE `premium` ADD COLUMN `amount` DECIMAL(10, 2) NOT NULL DEFAULT 0.00"
                )
                connection.commit()

            # Creating task note table, using constraints to link the composite keys
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS `task_notes` (
                `userID` INT NOT NULL,
                `taskID` INT NOT NULL,
                `noteID` INT NOT NULL,
                PRIMARY KEY (`taskID`, `noteID`),
                
                CONSTRAINT `fk_tn_user` 
                    FOREIGN KEY (`userID`) REFERENCES `users`(`userID`),
                    
                CONSTRAINT `fk_tn_task` 
                    FOREIGN KEY (`taskID`, `userID`) REFERENCES `tasks`(`taskID`, `userID`)
                    ON DELETE CASCADE ON UPDATE CASCADE,
                    
                CONSTRAINT `fk_tn_note` 
                    FOREIGN KEY (`noteID`, `userID`) REFERENCES `notes`(`noteID`, `userID`)
                    ON DELETE CASCADE ON UPDATE CASCADE
            )
            """)

            # Creating task file table, using constraints to link the composite keys

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS `task_files` (
                `userID` INT NOT NULL,
                `taskID` INT NOT NULL,
                `fileID` INT NOT NULL,
                PRIMARY KEY (`taskID`, `fileID`),
                
                CONSTRAINT `fk_tf_user` 
                    FOREIGN KEY (`userID`) REFERENCES `users`(`userID`),
                    
                CONSTRAINT `fk_tf_task` 
                    FOREIGN KEY (`taskID`, `userID`) REFERENCES `tasks`(`taskID`, `userID`)
                    ON DELETE CASCADE ON UPDATE CASCADE,
                    
                CONSTRAINT `fk_tf_file` 
                    FOREIGN KEY (`fileID`, `userID`) REFERENCES `files`(`fileID`, `userID`)
                    ON DELETE CASCADE ON UPDATE CASCADE
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS `note_files` (
                `userID` INT NOT NULL,
                `noteID` INT NOT NULL,
                `fileID` INT NOT NULL,
                PRIMARY KEY (`noteID`, `fileID`),
                CONSTRAINT `fk_nf_user` FOREIGN KEY (`userID`) REFERENCES `users`(`userID`),
                CONSTRAINT `fk_nf_note` FOREIGN KEY (`noteID`, `userID`) REFERENCES `notes`(`noteID`, `userID`)
                    ON DELETE CASCADE ON UPDATE CASCADE,
                CONSTRAINT `fk_nf_file` FOREIGN KEY (`fileID`, `userID`) REFERENCES `files`(`fileID`, `userID`)
                    ON DELETE CASCADE ON UPDATE CASCADE
            )
            """)
            print(cursor.fetchall())
        finally:
            connection.close()
