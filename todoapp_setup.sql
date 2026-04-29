USE todoapp;

CREATE TABLE IF NOT EXISTS users (
	userID INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    password VARCHAR(255),
    email VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS tasks (
	taskID INT AUTO_INCREMENT,
    userID INT NOT NULL,
    task_name VARCHAR(255),
    due_date DATETIME,
    date_created DATETIME,
    last_reminder_date DATETIME,
    reminder_freq_day TINYINT,
    reminder_freq_hour TINYINT,
    tags VARCHAR(255),
    PRIMARY KEY (taskID, userID),
    FOREIGN KEY (userID) REFERENCES users(userID)
);

CREATE TABLE IF NOT EXISTS notes (
	noteID INT AUTO_INCREMENT,
    userID INT NOT NULL,
    date_time DATETIME,
    note_title VARCHAR(255),
    contents LONGTEXT,
    PRIMARY KEY (noteID, userID),
    FOREIGN KEY (userID) REFERENCES users(userID)
);

CREATE TABLE IF NOT EXISTS files (
	fileID INT AUTO_INCREMENT,
	userID INT NOT NULL,
	link VARCHAR(255),
	local_file_address VARCHAR(255),
    PRIMARY KEY (fileID, userID),
    FOREIGN KEY (userID) REFERENCES users(userID)
);

CREATE TABLE IF NOT EXISTS premium (
	userID INT NOT NULL PRIMARY KEY,
    account_status CHAR,
    billing_address VARCHAR(255),
    re_bill_date DATETIME,
    payment VARCHAR(255),
    FOREIGN KEY (userID) REFERENCES users(userID)
);

CREATE TABLE IF NOT EXISTS task_notes (
    userID INT NOT NULL,
    taskID INT NOT NULL,
    noteID INT NOT NULL,
    PRIMARY KEY (taskID, noteID),
    
    -- foreign key for task-note user connection
    CONSTRAINT fk_tn_user 
		FOREIGN KEY (userID) REFERENCES users(userID),
        
    -- link to composite key in tasks 
    CONSTRAINT fk_tn_task 
        FOREIGN KEY (taskID, userID) REFERENCES tasks(taskID, userID)
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    -- link to composite key in notes
    CONSTRAINT fk_tn_note 
        FOREIGN KEY (noteID, userID) REFERENCES notes(noteID, userID)
        ON DELETE CASCADE ON UPDATE CASCADE
);