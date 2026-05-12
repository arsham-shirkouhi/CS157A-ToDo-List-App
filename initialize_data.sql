USE defaultdb;

-- 1. Populate users 
INSERT INTO users (name, password, email) VALUES
('Alice Smith', '$2y$10$eImiTXuWVxfM37uY4JANjOL.o84bhO9H9.SshWckEWTn07G6Sj.Hy', 'alice@example.com'),
('Bob Johnson', '$2y$10$K9hx.O7W6E4L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'bob@example.com'),
('Charlie Brown', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'charlie@example.com'),
('Diana Prince', '$2y$10$8K1p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'diana@example.com'),
('Edward Norton', '$2y$10$5J2p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'edward@example.com'),
('Fiona Gallagher', '$2y$10$Q1p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'fiona@example.com'),
('George Miller', '$2y$10$W1p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'george@example.com'),
('Hannah Abbott', '$2y$10$E1p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'hannah@example.com'),
('Ian Wright', '$2y$10$R1p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'ian@example.com'),
('Julia Roberts', '$2y$10$T1p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'julia@example.com'),
('Kevin Hart', '$2y$10$Y1p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'kevin@example.com'),
('Laura Palmer', '$2y$10$U1p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'laura@example.com'),
('Mike Wazowski', '$2y$10$I1p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'mike@example.com'),
('Nina Simone', '$2y$10$O1p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'nina@example.com'),
('Oscar Wilde', '$2y$10$P1p/9lP.9L7B7u/i49GOI2CIsT.S9G3F1p3Hk0VjU.D8M.7W6.2', 'oscar@example.com');

-- 2. Populate tasks
INSERT INTO tasks (userID, task_name, due_date, date_created, last_reminder_date, reminder_freq_day, reminder_freq_hour, tags) VALUES
(1, 'Finish UX Wireframes', '2026-05-20 09:00:00', NOW(), NOW(), 1, 0, 'design'),
(1, 'Email Stakeholders', '2026-05-21 10:00:00', NOW(), NOW(), 0, 4, 'admin'),
(2, 'Weekly Grocery Run', '2026-05-15 17:00:00', NOW(), NOW(), 7, 0, 'personal'),
(3, 'Brake Inspection', '2026-05-18 08:30:00', NOW(), NOW(), 0, 0, 'auto'),
(4, 'Morning Cardio', '2026-05-12 06:00:00', NOW(), NOW(), 1, 0, 'fitness'),
(5, 'Annual Physical', '2026-06-10 11:15:00', NOW(), NOW(), 30, 0, 'health'),
(6, 'Budget Review', '2026-05-25 16:00:00', NOW(), NOW(), 0, 2, 'finance'),
(7, 'Flight to Paris', '2026-07-15 21:00:00', NOW(), NOW(), 0, 0, 'travel'),
(8, 'Physics Lab Report', '2026-05-14 23:59:00', NOW(), NOW(), 0, 1, 'school'),
(9, 'Water Garden', '2026-05-13 07:00:00', NOW(), NOW(), 2, 0, 'home'),
(10, 'Pay Electricity', '2026-05-30 09:00:00', NOW(), NOW(), 0, 0, 'bills'),
(11, 'Sort Mail', '2026-05-12 18:00:00', NOW(), NOW(), 0, 0, 'chore'),
(12, 'Client Onboarding', '2026-05-14 14:00:00', NOW(), NOW(), 0, 0, 'work'),
(13, 'Blog Post: AI Trends', '2026-05-22 12:00:00', NOW(), NOW(), 1, 0, 'content'),
(14, 'Optimize LinkedIN', '2026-05-19 10:00:00', NOW(), NOW(), 0, 0, 'career');

-- 3. Populate notes
INSERT INTO notes (userID, date_time, note_title, contents) VALUES
(1, NOW(), 'Design Feedback', 'Stakeholders want more blue in the header.'),
(1, NOW(), 'Meeting Notes', 'Discussed the timeline for Q3.'),
(2, NOW(), 'Shopping List', 'Almond milk, kale, salmon.'),
(3, NOW(), 'Mechanic Quote', 'Estimated $400 for new pads and rotors.'),
(4, NOW(), 'Diet Plan', 'High protein, low carb for 2 weeks.'),
(6, NOW(), 'Tax Documents', 'Remember to include the remote work deduction.'),
(7, NOW(), 'Itinerary', 'Day 1: Louvre, Day 2: Eiffel Tower.'),
(8, NOW(), 'Physics Formulas', 'F=ma, E=mc^2, p=mv.'),
(9, NOW(), 'Plant Schedule', 'Fertilize the roses every second week.'),
(10, NOW(), 'Utility Tracking', 'Usage is up by 15% this month.'),
(12, NOW(), 'Client Bio', 'Prefers email communication over Slack.'),
(13, NOW(), 'Headline Ideas', 'The Future of Neural Networks in 2026.'),
(14, NOW(), 'Resume Keywords', 'Docker, Kubernetes, AWS, SQL.'),
(15, NOW(), 'Daily Journal', 'Feeling productive and focused today.'),
(1, NOW(), 'Quick Reminder', 'Call the bank regarding the transfer.');

-- 4. Populate files 
INSERT INTO files (userID, link, local_file_address) VALUES
(1, 'http://s3.com/u1/wireframe.png', '/local/u1/wireframe.png'),
(1, 'http://s3.com/u1/feedback.pdf', '/local/u1/feedback.pdf'),
(3, 'http://s3.com/u3/invoice.pdf', '/local/u3/invoice.pdf'),
(6, 'http://s3.com/u6/spreadsheet.csv', '/local/u6/spreadsheet.csv'),
(7, 'http://s3.com/u7/boarding_pass.pdf', '/local/u7/boarding_pass.pdf'),
(8, 'http://s3.com/u8/lab_data.xlsx', '/local/u8/lab_data.xlsx'),
(12, 'http://s3.com/u12/contract.pdf', '/local/u12/contract.pdf'),
(13, 'http://s3.com/u13/cover_image.jpg', '/local/u13/cover_image.jpg'),
(14, 'http://s3.com/u14/resume_final.pdf', '/local/u14/resume_final.pdf'),
(1, 'http://s3.com/u1/spec_doc.pdf', '/local/u1/spec_doc.pdf'),
(2, 'http://s3.com/u2/receipt.jpg', '/local/u2/receipt.jpg'),
(4, 'http://s3.com/u4/gym_waiver.pdf', '/local/u4/gym_waiver.pdf'),
(5, 'http://s3.com/u5/blood_work.pdf', '/local/u5/blood_work.pdf'),
(9, 'http://s3.com/u9/garden_layout.jpg', '/local/u9/garden_layout.jpg'),
(10, 'http://s3.com/u10/bill_copy.pdf', '/local/u10/bill_copy.pdf');

-- 5. Populate premium
INSERT INTO premium (userID, account_status, billing_address, re_bill_date, payment, amount) VALUES
(1, 'A', '123 Main St', '2026-06-01', 'Credit Card', 5.99),
(2, 'A', '456 Oak Ave', '2026-06-15', 'PayPal', 5.99),
(3, 'A', '789 Pine Rd', '2026-05-20', 'Debit Card', 5.99),
(4, 'A', '101 Maple Ln', '2026-06-12', 'Credit Card', 5.99),
(5, 'A', '202 Birch Blvd', '2026-06-25', 'Credit Card', 5.99),
(6, 'A', '303 Cedar Ct', '2026-06-30', 'PayPal', 5.99),
(7, 'A', '404 Elm St', '2026-05-01', 'Credit Card', 5.99),
(8, 'A', '505 Spruce Wy', '2026-06-18', 'Debit Card', 5.99),
(9, 'A', '606 Willow Dr', '2026-06-17', 'Credit Card', 5.99),
(10, 'A', '707 Ash Ave', '2026-07-01', 'PayPal', 5.99),
(11, 'A', '808 Cherry Ln', '2026-06-13', 'Debit Card', 5.99),
(12, 'A', '909 Walnut St', '2026-06-14', 'Credit Card', 5.99),
(13, 'A', '111 Poplar Dr', '2026-06-22', 'PayPal', 5.99),
(14, 'A', '222 Aspen Rd', '2026-05-28', 'Credit Card', 5.99),
(15, 'A', '333 Beech St', '2026-06-16', 'Credit Card', 5.99);

-- 6. Populate task_notes 
INSERT INTO task_notes (userID, taskID, noteID) VALUES
(1, 1, 1), (1, 1, 2), (2, 3, 3), (3, 4, 4), (4, 5, 5), (6, 7, 6), (7, 8, 7),
(8, 9, 8), (9, 10, 9), (10, 11, 10), (12, 13, 11), (13, 14, 12),
(14, 15, 13), (1, 1, 15); -- User 1 multi-link

-- 7. Populate task_files 
INSERT INTO task_files (userID, taskID, fileID) VALUES
(1, 1, 1), (1, 1, 2), (1, 1, 10), (3, 4, 3), (6, 7, 4), 
(7, 8, 5), (8, 9, 6), (12, 13, 7), (13, 14, 8), (14, 15, 9),
(2, 3, 11), (4, 5, 12), (5, 6, 13), (9, 10, 14), (10, 11, 15);

-- 8. Populate note_files 
INSERT INTO note_files (userID, noteID, fileID) VALUES
(1, 1, 1), (1, 1, 2), -- Note 1 has two files
(1, 2, 10), (3, 4, 3), (6, 6, 4), (7, 7, 5), (8, 8, 6),
(12, 11, 7), (13, 12, 8), (14, 13, 9), (2, 3, 11), (4, 5, 12),
(5, 5, 13), (9, 9, 14), (10, 10, 15);