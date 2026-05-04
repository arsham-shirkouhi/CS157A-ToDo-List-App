from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from database import Database


class AppDatabase(Database):
    def execute_write(self, sql: str, params: Optional[tuple] = None) -> int:
        conn = self.pool.connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                conn.commit()
                lid = cur.lastrowid
                return int(lid) if lid else cur.rowcount
        finally:
            conn.close()


def _now_sql() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --- Users ---


def get_user_by_id(db: AppDatabase, user_id: int) -> Optional[dict[str, Any]]:
    rows = db.query(
        "SELECT `userID`, `name`, `email` FROM users WHERE `userID` = %s",
        (user_id,),
    )
    return rows[0] if rows else None


def get_premium(db: AppDatabase, user_id: int) -> Optional[dict[str, Any]]:
    rows = db.query(
        "SELECT `userID`, `account_status`, `billing_address`, `re_bill_date`, `payment`, `amount` "
        "FROM premium WHERE `userID` = %s",
        (user_id,),
    )
    return rows[0] if rows else None


def insert_default_premium_for_user(db: AppDatabase, user_id: int) -> int:
    """
    Create one `premium` row for a new user. Defaults only (no billing UI).
    `payment` holds payment method; free tier uses placeholder values.
    """
    return db.execute_write(
        """
        INSERT INTO premium (`userID`, `account_status`, `billing_address`, `re_bill_date`, `payment`, `amount`)
        VALUES (%s, 'N', '', NULL, 'none', 0.00)
        ON DUPLICATE KEY UPDATE `userID` = `userID`
        """,
        (user_id,),
    )


def upsert_premium(
    db: AppDatabase,
    user_id: int,
    account_status: str,
    billing_address: str = "",
    re_bill_date: Optional[str] = None,
    payment: str = "",
    amount: float = 0.0,
) -> int:
    sql = """
        INSERT INTO premium (`userID`, `account_status`, `billing_address`, `re_bill_date`, `payment`, `amount`)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            `account_status` = VALUES(`account_status`),
            `billing_address` = VALUES(`billing_address`),
            `re_bill_date` = VALUES(`re_bill_date`),
            `payment` = VALUES(`payment`),
            `amount` = VALUES(`amount`)
    """
    status_char = (account_status or "N")[:1]
    return db.execute_write(
        sql,
        (user_id, status_char, billing_address, re_bill_date, payment, amount),
    )


# --- Tasks ---


def list_tasks(db: AppDatabase, user_id: int) -> list[dict[str, Any]]:
    return db.query(
        "SELECT `taskID`, `userID`, `task_name`, `status`, `due_date`, `date_created`, `last_reminder_date`, "
        "`reminder_freq_day`, `reminder_freq_hour`, `tags` FROM tasks WHERE `userID` = %s "
        "ORDER BY `date_created` DESC",
        (user_id,),
    )


def create_task(
    db: AppDatabase,
    user_id: int,
    task_name: str,
    due_date: Optional[str] = None,
    tags: Optional[str] = None,
    reminder_freq_day: Optional[int] = None,
    reminder_freq_hour: Optional[int] = None,
    status: str = "A",
) -> int:
    """``status`` is a single CHAR, e.g. ``A`` active, ``C`` completed (your app can define meanings)."""
    sql = """
        INSERT INTO tasks (`userID`, `task_name`, `status`, `due_date`, `date_created`, `last_reminder_date`,
            `reminder_freq_day`, `reminder_freq_hour`, `tags`)
        VALUES (%s, %s, %s, %s, %s, NULL, %s, %s, %s)
    """
    st = (status or "A")[:1]
    return db.execute_write(
        sql,
        (user_id, task_name, st, due_date, _now_sql(), reminder_freq_day, reminder_freq_hour, tags),
    )


def update_task(
    db: AppDatabase,
    user_id: int,
    task_id: int,
    task_name: Optional[str] = None,
    due_date: Optional[str] = None,
    tags: Optional[str] = None,
    last_reminder_date: Optional[str] = None,
    reminder_freq_day: Optional[int] = None,
    reminder_freq_hour: Optional[int] = None,
    status: Optional[str] = None,
) -> int:
    fields: list[str] = []
    values: list[Any] = []
    if task_name is not None:
        fields.append("`task_name` = %s")
        values.append(task_name)
    if status is not None:
        fields.append("`status` = %s")
        values.append((status or "A")[:1])
    if due_date is not None:
        fields.append("`due_date` = %s")
        values.append(due_date)
    if tags is not None:
        fields.append("`tags` = %s")
        values.append(tags)
    if last_reminder_date is not None:
        fields.append("`last_reminder_date` = %s")
        values.append(last_reminder_date)
    if reminder_freq_day is not None:
        fields.append("`reminder_freq_day` = %s")
        values.append(reminder_freq_day)
    if reminder_freq_hour is not None:
        fields.append("`reminder_freq_hour` = %s")
        values.append(reminder_freq_hour)
    if not fields:
        return 0
    values.extend([task_id, user_id])
    sql = f"UPDATE tasks SET {', '.join(fields)} WHERE `taskID` = %s AND `userID` = %s"
    return db.execute_write(sql, tuple(values))


def delete_task(db: AppDatabase, user_id: int, task_id: int) -> int:
    db.execute_write(
        "DELETE FROM task_notes WHERE `taskID` = %s AND `userID` = %s",
        (task_id, user_id),
    )
    db.execute_write(
        "DELETE FROM task_files WHERE `taskID` = %s AND `userID` = %s",
        (task_id, user_id),
    )
    return db.execute_write(
        "DELETE FROM tasks WHERE `taskID` = %s AND `userID` = %s",
        (task_id, user_id),
    )


# --- Notes ---


def list_notes(db: AppDatabase, user_id: int) -> list[dict[str, Any]]:
    return db.query(
        "SELECT `noteID`, `userID`, `date_time`, `note_title`, `contents` FROM notes "
        "WHERE `userID` = %s ORDER BY `date_time` DESC",
        (user_id,),
    )


def create_note(db: AppDatabase, user_id: int, note_title: str, contents: str) -> int:
    sql = """
        INSERT INTO notes (`userID`, `date_time`, `note_title`, `contents`)
        VALUES (%s, %s, %s, %s)
    """
    return db.execute_write(sql, (user_id, _now_sql(), note_title, contents))


def update_note(
    db: AppDatabase,
    user_id: int,
    note_id: int,
    note_title: Optional[str] = None,
    contents: Optional[str] = None,
) -> int:
    fields: list[str] = []
    values: list[Any] = []
    if note_title is not None:
        fields.append("`note_title` = %s")
        values.append(note_title)
    if contents is not None:
        fields.append("`contents` = %s")
        values.append(contents)
    if not fields:
        return 0
    values.extend([note_id, user_id])
    sql = f"UPDATE notes SET {', '.join(fields)} WHERE `noteID` = %s AND `userID` = %s"
    return db.execute_write(sql, tuple(values))


def delete_note(db: AppDatabase, user_id: int, note_id: int) -> int:
    db.execute_write(
        "DELETE FROM task_notes WHERE `noteID` = %s AND `userID` = %s",
        (note_id, user_id),
    )
    return db.execute_write(
        "DELETE FROM notes WHERE `noteID` = %s AND `userID` = %s",
        (note_id, user_id),
    )


# --- Files ---


def list_files(db: AppDatabase, user_id: int) -> list[dict[str, Any]]:
    return db.query(
        "SELECT `fileID`, `userID`, `link`, `local_file_address` FROM files WHERE `userID` = %s",
        (user_id,),
    )


def _read_bytes_from_local_reference(local_file_address: str) -> Optional[bytes]:
    """Load file bytes from a path stored in `local_file_address` (absolute or relative to cwd)."""
    raw = (local_file_address or "").strip()
    if not raw:
        return None
    p = Path(raw)
    if not p.is_file():
        p = Path.cwd() / raw
    if not p.is_file():
        return None
    return p.read_bytes()


def _maybe_create_note_from_pdf(db: AppDatabase, user_id: int, local_file_address: str) -> None:
    path_str = (local_file_address or "").strip()
    if not path_str.lower().endswith(".pdf"):
        return
    pdf_bytes = _read_bytes_from_local_reference(path_str)
    if not pdf_bytes:
        return
    title = f"Notes from {Path(path_str).name}"
    ok, body = pdf_bytes_to_study_notes(pdf_bytes)
    if not ok:
        body = (
            f"(PDF conversion did not produce AI notes. Reason: {body})\n\n"
            "You can still open the original file using the stored path or link."
        )
    create_note(db, user_id, title[:255], body)


def create_file_record(db: AppDatabase, user_id: int, link: str, local_file_address: str) -> int:
    sql = """
        INSERT INTO files (`userID`, `link`, `local_file_address`)
        VALUES (%s, %s, %s)
    """
    path_str = (local_file_address or "").strip()
    file_id = db.execute_write(sql, (user_id, link, local_file_address))
    _maybe_create_note_from_pdf(db, user_id, path_str)
    return file_id


def delete_file_record(db: AppDatabase, user_id: int, file_id: int) -> int:
    db.execute_write(
        "DELETE FROM task_files WHERE `fileID` = %s AND `userID` = %s",
        (file_id, user_id),
    )
    return db.execute_write(
        "DELETE FROM files WHERE `fileID` = %s AND `userID` = %s",
        (file_id, user_id),
    )


# --- Task–note links (many-to-many for this schema) ---


def link_task_to_note(db: AppDatabase, user_id: int, task_id: int, note_id: int) -> int:
    sql = """
        INSERT INTO task_notes (`userID`, `taskID`, `noteID`)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE `userID` = VALUES(`userID`)
    """
    return db.execute_write(sql, (user_id, task_id, note_id))


def unlink_task_from_note(db: AppDatabase, user_id: int, task_id: int, note_id: int) -> int:
    return db.execute_write(
        "DELETE FROM task_notes WHERE `userID` = %s AND `taskID` = %s AND `noteID` = %s",
        (user_id, task_id, note_id),
    )


def notes_for_task(db: AppDatabase, user_id: int, task_id: int) -> list[dict[str, Any]]:
    sql = """
        SELECT n.`noteID`, n.`userID`, n.`date_time`, n.`note_title`, n.`contents`
        FROM notes n
        INNER JOIN task_notes tn ON n.`noteID` = tn.`noteID` AND n.`userID` = tn.`userID`
        WHERE tn.`userID` = %s AND tn.`taskID` = %s
    """
    return db.query(sql, (user_id, task_id))


def tasks_for_note(db: AppDatabase, user_id: int, note_id: int) -> list[dict[str, Any]]:
    sql = """
        SELECT t.`taskID`, t.`userID`, t.`task_name`, t.`status`, t.`due_date`, t.`date_created`, t.`tags`
        FROM tasks t
        INNER JOIN task_notes tn ON t.`taskID` = tn.`taskID` AND t.`userID` = tn.`userID`
        WHERE tn.`userID` = %s AND tn.`noteID` = %s
    """
    return db.query(sql, (user_id, note_id))


# --- Task–file links (`task_files`) ---


def link_task_to_file(db: AppDatabase, user_id: int, task_id: int, file_id: int) -> int:
    sql = """
        INSERT INTO task_files (`userID`, `taskID`, `fileID`)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE `userID` = VALUES(`userID`)
    """
    return db.execute_write(sql, (user_id, task_id, file_id))


def unlink_task_from_file(db: AppDatabase, user_id: int, task_id: int, file_id: int) -> int:
    return db.execute_write(
        "DELETE FROM task_files WHERE `userID` = %s AND `taskID` = %s AND `fileID` = %s",
        (user_id, task_id, file_id),
    )


def files_for_task(db: AppDatabase, user_id: int, task_id: int) -> list[dict[str, Any]]:
    sql = """
        SELECT f.`fileID`, f.`userID`, f.`link`, f.`local_file_address`
        FROM files f
        INNER JOIN task_files tf ON f.`fileID` = tf.`fileID` AND f.`userID` = tf.`userID`
        WHERE tf.`userID` = %s AND tf.`taskID` = %s
    """
    return db.query(sql, (user_id, task_id))


def tasks_for_file(db: AppDatabase, user_id: int, file_id: int) -> list[dict[str, Any]]:
    sql = """
        SELECT t.`taskID`, t.`userID`, t.`task_name`, t.`status`, t.`due_date`, t.`date_created`, t.`tags`
        FROM tasks t
        INNER JOIN task_files tf ON t.`taskID` = tf.`taskID` AND t.`userID` = tf.`userID`
        WHERE tf.`userID` = %s AND tf.`fileID` = %s
    """
    return db.query(sql, (user_id, file_id))


# --- PDF → note text ---


def _extract_pdf_text(pdf_bytes: bytes) -> tuple[bool, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        return False, "Install the pypdf package to read PDF text locally."

    from io import BytesIO

    reader = PdfReader(BytesIO(pdf_bytes))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    text = "\n".join(parts).strip()
    if not text:
        return False, "No extractable text found in this PDF."
    return True, text


def _format_plain_text_as_markdown_notes(raw_text: str) -> str:
    """
    Turn extracted PDF text into simple markdown notes using only the standard library.
    """
    text = raw_text.strip()
    if not text:
        return "_No extractable text to format._"

    parts = [
        "# Notes from PDF",
        "",
        "_Extracted locally (open source: [pypdf](https://github.com/py-pdf/pypdf))._",
        "_Optional: set `OPENAI_API_KEY` to also try an AI pass after extraction._",
        "",
    ]

    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    if not blocks:
        blocks = [text]

    for i, block in enumerate(blocks[:150], start=1):
        parts.append(f"## Part {i}")
        parts.append("")
        parts.append(block[:12_000])
        parts.append("")

    body = "\n".join(parts).strip()
    if len(body) > 100_000:
        body = body[:99_997] + "\n\n…"
    return body


def _openai_summarize_to_notes(raw_text: str) -> tuple[bool, str]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return False, "OpenAI not configured (no OPENAI_API_KEY)."

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You help students turn messy PDF text into clear class notes. "
                    "Output structured markdown: short title, bullet key points, optional glossary."
                ),
            },
            {"role": "user", "content": raw_text[:100_000]},
        ],
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return False, f"OpenAI API error: {e.code} {err_body[:500]}"
    except OSError as e:
        return False, f"Network error calling OpenAI: {e}"

    try:
        return True, payload["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        return False, "Unexpected response from OpenAI."


def pdf_bytes_to_study_notes(pdf_bytes: bytes) -> tuple[bool, str]:
    """
    Extract text with pypdf (BSD-style OSS), then either:
    - format as markdown locally (no API key), or
    - if ``OPENAI_API_KEY`` is set, try OpenAI first and fall back to local formatting on failure.

    Returns (success, message_or_note_body).
    """
    ok, text_or_err = _extract_pdf_text(pdf_bytes)
    if not ok:
        return False, text_or_err

    if os.getenv("OPENAI_API_KEY"):
        ai_ok, ai_out = _openai_summarize_to_notes(text_or_err)
        if ai_ok:
            return True, ai_out

    return True, _format_plain_text_as_markdown_notes(text_or_err)
