import dotenv

dotenv.load_dotenv(override=True)

import os
from typing import Any, Optional

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect, generate_csrf
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import EqualTo, InputRequired, Length, ValidationError

import application_layer as apl

app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY") or "dev"

db = apl.AppDatabase()
db.setup_db()
csrf = CSRFProtect(app)


# Expose CSRF token to all templates.
@app.context_processor
def _csrf():
    return {"csrf_token_value": generate_csrf()}


# Format DB datetime/date for UI strings; bad types fall back to str().
def _fmt_dt(v: Any) -> str:
    if v is None:
        return ""
    if hasattr(v, "strftime"):
        if getattr(v, "hour", 0) or getattr(v, "minute", 0) or getattr(v, "second", 0):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return v.strftime("%Y-%m-%d")
    return str(v)


# Due date as YYYY-MM-DD only for HTML date inputs.
def _due_ui(v: Any) -> str:
    s = _fmt_dt(v)
    return s.split()[0] if s else ""


# Map reminder label to (day_freq, hour_freq) tuple for DB.
def _rem_from_ui(s: str) -> tuple[Optional[int], Optional[int]]:
    t = (s or "").lower()
    if "daily" in t:
        return 1, None
    if "week" in t:
        return 7, None
    if "urgent" in t:
        return None, 1
    return None, None


# DB reminder columns -> Daily / Weekly / Custom for forms; bad ints ignored via try/except.
def _reminder_form_value(r: dict[str, Any]) -> str:
    rd, rh = r.get("reminder_freq_day"), r.get("reminder_freq_hour")
    if not rd and not rh:
        return "Daily"
    try:
        if int(rd) == 1:
            return "Daily"
        if int(rd) == 7:
            return "Weekly"
    except (TypeError, ValueError):
        pass
    return "Custom"


# One task row for JSON state; DB reads via apl propagate on failure.
def _task_row_ui(uid: int, r: dict[str, Any]) -> dict[str, Any]:
    st = (r.get("status") or "A").strip().upper()
    rd, rh = r.get("reminder_freq_day"), r.get("reminder_freq_hour")
    rem = "Off"
    if rd:
        rem = f"Every {int(rd)} day(s)"
    elif rh:
        rem = f"Every {int(rh)} hour(s)"
    tid = int(r["taskID"])
    nfs = apl.notes_for_task(db, uid, tid)
    ffs = apl.files_for_task(db, uid, tid)
    return {
        "id": str(tid),
        "name": r.get("task_name") or "",
        "dueDate": _due_ui(r.get("due_date")),
        "tag": r.get("tags") or "",
        "reminder": rem,
        "description": "",
        "completed": st == "C",
        "createdAt": _fmt_dt(r.get("date_created")),
        "linkedNoteIds": [str(x["noteID"]) for x in nfs],
        "linkedFileIds": [str(x["fileID"]) for x in ffs],
    }


# One note row for JSON state; DB errors propagate.
def _note_row_ui(uid: int, r: dict[str, Any]) -> dict[str, Any]:
    nid = int(r["noteID"])
    pairs = apl.tasks_for_note(db, uid, nid)
    tid = str(pairs[0]["taskID"]) if pairs else ""
    fl = apl.files_for_note(db, uid, nid)
    return {
        "id": str(nid),
        "title": r.get("note_title") or "",
        "contents": r.get("contents") or "",
        "taskId": tid,
        "createdAt": _fmt_dt(r.get("date_time")),
        "fileIds": [str(x["fileID"]) for x in fl],
    }


# One file row for JSON state; DB errors propagate.
def _file_row_ui(uid: int, r: dict[str, Any]) -> dict[str, Any]:
    fid = int(r["fileID"])
    pairs = apl.tasks_for_file(db, uid, fid)
    tid = str(pairs[0]["taskID"]) if pairs else ""
    nfl = apl.notes_for_file(db, uid, fid)
    nid = str(nfl[0]["noteID"]) if nfl else ""
    loc = (r.get("local_file_address") or "").strip()
    link = (r.get("link") or "").strip()
    label = loc.split("/")[-1] if loc else (link.split("/")[-1] if link else "file")
    return {
        "id": str(fid),
        "name": label,
        "sizeLabel": "",
        "type": "File",
        "taskId": tid,
        "noteId": nid,
        "createdAt": "",
    }


# Full /api/state body; DB errors from list_* / get_* propagate (Flask 500 if uncaught).
def _state_payload(uid: int) -> dict[str, Any]:
    u = apl.get_user_by_id(db, uid)
    pr = apl.get_premium(db, uid)
    plan = "Premium" if pr and str(pr.get("account_status", "")).strip().upper() == "Y" else "Free Plan"
    tasks_raw = apl.list_tasks(db, uid)
    notes_raw = apl.list_notes(db, uid)
    files_raw = apl.list_files(db, uid)
    return {
        "tasks": [_task_row_ui(uid, x) for x in tasks_raw],
        "notes": [_note_row_ui(uid, x) for x in notes_raw],
        "files": [_file_row_ui(uid, x) for x in files_raw],
        "user": {
            "name": (u or {}).get("name") or "",
            "email": (u or {}).get("email") or "",
            "premiumStatus": plan,
        },
    }


class User(UserMixin):
    # Flask-Login user wrapper; no DB.
    def __init__(self, uid: int, name: str, email: str):
        self.id = uid
        self.name = name or ""
        self.email = email or ""


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# Load User from DB by id; missing user -> None (not an error). DB errors propagate.
@login_manager.user_loader
def load_user(user_id):
    row = apl.get_user_by_id(db, int(user_id))
    if not row:
        return None
    return User(int(row["userID"]), str(row["name"] or ""), str(row["email"] or ""))


# Login fields; WTForms handles validation errors on submit.
class LoginForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Length(max=255)])
    password = PasswordField(validators=[InputRequired()])
    submit = SubmitField("Log In")


# Signup fields; validate_email raises ValidationError if email taken (form-level, not HTTP 500).
class RegisterForm(FlaskForm):
    name = StringField(validators=[InputRequired(), Length(max=255)])
    email = StringField(validators=[InputRequired(), Length(max=255)])
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=255)])
    confirm = PasswordField(validators=[InputRequired(), EqualTo("password", message="Passwords must match.")])
    submit = SubmitField("Create Account")

    # Reject duplicate email at form validation time.
    def validate_email(self, field):
        if apl.get_user_by_email(db, field.data):
            raise ValidationError("That email is already registered.")


# Show/login form; bad creds flash danger; DB errors propagate.
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        row = apl.get_user_by_email(db, form.email.data.strip())
        if not row or not apl.check_password(form.password.data, row["password"]):
            flash("Invalid email or password.", "danger")
            return render_template("login.html", form=form)
        login_user(User(int(row["userID"]), row["name"], row["email"]))
        return redirect(url_for("dashboard"))
    return render_template("login.html", form=form)


# Show/register; create_user_account returns (ok, msg) on failure; DB insert errors propagate.
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        ok, msg = apl.create_user_account(db, form.name.data, form.email.data, form.password.data)
        if ok:
            flash("Account created. Log in.", "success")
            return redirect(url_for("login"))
        flash(msg, "danger")
    return render_template("signup.html", form=form)


# End session; no DB.
@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# Public home template; no DB.
@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")


# Dashboard with tasks and notes lists; DB errors propagate.
@app.route("/dashboard")
@login_required
def dashboard():
    tasks = apl.list_tasks(db, current_user.id)
    notes = apl.list_notes(db, current_user.id)
    return render_template("dashboard.html", tasks=tasks, notes=notes)


# Tasks page; DB errors propagate.
@app.route("/tasks")
@login_required
def tasks():
    return render_template("tasks.html", tasks=apl.list_tasks(db, current_user.id))


# Edit one task; missing row abort(404); validation sets err str; DB update errors propagate.
@app.route("/tasks/<int:tid>", methods=["GET", "POST"])
@login_required
def task_detail(tid: int):
    row = apl.get_task(db, current_user.id, tid)
    if row is None:
        abort(404)
    err = None
    if request.method == "POST":
        name = (request.form.get("task_name") or "").strip()
        due = (request.form.get("due_date") or "").strip()
        tag = (request.form.get("tags") or "").strip() or None
        rem = str(request.form.get("task_reminder") or "")
        completed = request.form.get("completed") == "1"
        if not name:
            err = "Name is required."
        elif not due:
            err = "Due date is required."
        if err:
            return render_template(
                "task_detail.html",
                name=request.form.get("task_name") or "",
                due_date=request.form.get("due_date") or "",
                tags=(request.form.get("tags") or "").strip(),
                reminder=rem or "Daily",
                completed=completed,
                created_at=_fmt_dt(row["date_created"]),
                err=err,
            )
        rd, rh = _rem_from_ui(rem.lower())
        apl.update_task(
            db,
            current_user.id,
            tid,
            task_name=name,
            due_date=due,
            tags=tag,
            status="C" if completed else "A",
        )
        apl.set_task_reminders(db, current_user.id, tid, rd, rh)
        return redirect(url_for("task_detail", tid=tid))
    return render_template(
        "task_detail.html",
        name=row["task_name"] or "",
        due_date=_due_ui(row.get("due_date")),
        tags=row.get("tags") or "",
        reminder=_reminder_form_value(row),
        completed=(row.get("status") or "A").strip().upper() == "C",
        created_at=_fmt_dt(row["date_created"]),
        err=err,
    )


# Notes list page; DB errors propagate.
@app.route("/notes")
@login_required
def notes():
    return render_template("notes.html", notes=apl.list_notes(db, current_user.id))


# Edit one note; missing abort(404); empty title re-renders with err; DB errors propagate.
@app.route("/notes/<int:nid>", methods=["GET", "POST"])
@login_required
def note_detail(nid: int):
    row = apl.get_note(db, current_user.id, nid)
    if row is None:
        abort(404)
    err = None
    if request.method == "POST":
        title = (request.form.get("note_title") or "").strip()
        body = request.form.get("contents") or ""
        if not title:
            err = "Title is required."
            return render_template(
                "note_detail.html",
                title=request.form.get("note_title") or "",
                contents=body,
                saved_at=_fmt_dt(row["date_time"]),
                err=err,
            )
        apl.update_note(db, current_user.id, nid, note_title=title, contents=body)
        return redirect(url_for("note_detail", nid=nid))
    return render_template(
        "note_detail.html",
        title=row["note_title"],
        contents=row["contents"],
        saved_at=_fmt_dt(row["date_time"]),
        err=err,
    )


# Files page; DB errors propagate.
@app.route("/files")
@login_required
def files():
    return render_template("files.html", files=apl.list_files(db, current_user.id))


# Profile page; DB errors propagate.
@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", premium=apl.get_premium(db, current_user.id))


# JSON sync payload; DB errors propagate (500 if uncaught).
@app.get("/api/state")
@login_required
def api_state():
    return jsonify(_state_payload(current_user.id))


# Create task; 400 if missing name; DB errors propagate.
@app.post("/api/task")
@login_required
def api_task_post():
    d = request.get_json(silent=True) or {}
    name = (d.get("name") or "").strip()
    if not name:
        return jsonify(err="missing name"), 400
    rd, rh = _rem_from_ui(str(d.get("reminder") or ""))
    st = "C" if d.get("completed") else "A"
    tid = apl.create_task(
        db,
        current_user.id,
        name,
        (d.get("dueDate") or "").strip() or None,
        (d.get("tag") or "").strip() or None,
        rd,
        rh,
        st,
    )
    return jsonify(ok=True, id=int(tid))


# Toggle complete; 400 if body missing completed; DB errors propagate.
@app.put("/api/task/<int:tid>")
@login_required
def api_task_put(tid: int):
    d = request.get_json(silent=True) or {}
    if "completed" not in d:
        return jsonify(err="missing completed"), 400
    apl.update_task(db, current_user.id, tid, status="C" if d.get("completed") else "A")
    return jsonify(ok=True)


# Delete task; DB errors propagate.
@app.delete("/api/task/<int:tid>")
@login_required
def api_task_delete(tid: int):
    apl.delete_task(db, current_user.id, tid)
    return jsonify(ok=True)


# Create note; 400 if no title; bad task_id int ignored (pass); DB errors propagate.
@app.post("/api/note")
@login_required
def api_note_post():
    d = request.get_json(silent=True) or {}
    title = (d.get("title") or "").strip()
    contents = (d.get("contents") or "").strip()
    if not title:
        return jsonify(err="missing title"), 400
    nid = int(apl.create_note(db, current_user.id, title, contents))
    raw = d.get("task_id")
    if raw not in (None, ""):
        try:
            apl.link_task_to_note(db, current_user.id, int(raw), nid)
        except (TypeError, ValueError):
            pass
    return jsonify(ok=True, id=nid)


# Create file + links; bad ids coerced to None/skip via try/except; DB errors propagate.
@app.post("/api/file")
@login_required
def api_file_post():
    d = request.get_json(silent=True) or {}
    link = (d.get("link") or "").strip()
    loc = (d.get("local_file_address") or "").strip()
    note_raw = d.get("note_id")
    note_id = None
    if note_raw not in (None, ""):
        try:
            note_id = int(note_raw)
        except (TypeError, ValueError):
            note_id = None
    fid = int(apl.create_file_record(db, current_user.id, link, loc, note_id))
    raw = d.get("task_id")
    if raw not in (None, ""):
        try:
            apl.link_task_to_file(db, current_user.id, int(raw), fid)
        except (TypeError, ValueError):
            pass
    return jsonify(ok=True, id=fid)


# Delete file record; DB errors propagate.
@app.delete("/api/file/<int:fid>")
@login_required
def api_file_delete(fid: int):
    apl.delete_file_record(db, current_user.id, fid)
    return jsonify(ok=True)


# Update profile fields; DB errors propagate.
@app.post("/api/profile")
@login_required
def api_profile_post():
    d = request.get_json(silent=True) or {}
    pw = (d.get("password") or "").strip()
    apl.update_user_profile(
        db,
        current_user.id,
        (d.get("name") or "").strip(),
        (d.get("email") or "").strip(),
        pw if pw else None,
    )
    return jsonify(ok=True)


# Upsert premium; bad amount -> 0.0 via try/except; DB errors propagate.
@app.post("/api/premium")
@login_required
def api_premium_post():
    d = request.get_json(silent=True) or {}
    try:
        amt = float(d.get("amount", 0) or 0)
    except (TypeError, ValueError):
        amt = 0.0
    apl.upsert_premium(
        db,
        current_user.id,
        str(d.get("account_status", "N"))[:1],
        str(d.get("billing_address", ""))[:255],
        d.get("re_bill_date"),
        str(d.get("payment", ""))[:255],
        amt,
    )
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=True, port=5667, host="127.0.0.1")
