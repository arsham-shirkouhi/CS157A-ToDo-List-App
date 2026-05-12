# CS157A To-Do List App

## Project Overview
This project is a Flask-based to-do list web application connected to a MySQL-compatible database. Users can create accounts, log in, manage tasks, write notes, attach files or links, and view profile information.

The app runs locally at `http://127.0.0.1:5667`.

## Dependencies and Required Software
- Python 3.10 or newer
- `pip`
- A MySQL-compatible database
- Flask
- python-dotenv
- PyMySQL
- DBUtils
- bcrypt
- pypdf
- flask-login
- flask-wtf

Install the Python packages with:

```bash
pip install -r requirements.txt
```

## Instructions for Setting Up and Running the Project
1. Open a terminal in the project folder:

```bash
cd CS157A-ToDo-List-App
```

2. Create and activate a virtual environment if you want to keep dependencies separate.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add:

```env
DB_HOST=your_database_host
DB_PORT=your_database_port
DB_USER=your_database_username
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
APP_SECRET_KEY=your_flask_secret_key
```

5. Start the application:

```bash
python main.py
```

6. Open the app in your browser:

```
http://127.0.0.1:5667
```

## Additional Configuration Steps Needed to Connect to the Database
- The app reads `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and `APP_SECRET_KEY` from the `.env` file.
- On startup, the app automatically creates missing tables by calling `setup_db()`.
- A `todoapp_setup.sql` file is included if you want to create the tables manually.
- The database connection uses SSL in the code, which matches hosted MySQL services such as Aiven.
- If you are using Aiven, `DB_NAME` is usually `defaultdb` unless your database was configured differently.
- If you run `todoapp_setup.sql` manually, make sure its `USE` statement matches the same database name as `DB_NAME`.