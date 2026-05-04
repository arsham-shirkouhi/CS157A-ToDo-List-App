import os
import dotenv

from dbutils.pooled_db import PooledDB
import pymysql

#load environment variables from local .env file
dotenv.load_dotenv()


class Database:
    def __init__(self):
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=5,
            mincached=2,
            blocking=True,
            ping=1, 
            cursorclass=pymysql.cursors.DictCursor,
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            # REQUIRED FOR AIVEN:
            ssl={'ssl': True}, 
            charset='utf8mb4'
        )

    def query(self, sql, params=None):
        connection = self.pool.connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchall()
        finally:
            connection.close()

    def setup_db(self):
        try:
            connection = self.pool.connection()
            cursor = connection.cursor()

            #create database todoapp
            cursor.execute('CREATE SCHEMA IF NOT EXISTS `todoapp`')

            cursor.execute('USE `todoapp`')

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
            print(cursor.fetchall())
        finally:
            connection.close()
