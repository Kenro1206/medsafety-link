import json
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from core.config_manager import SETTINGS_PATH
from core.time_utils import now_jst_iso

_initialized_paths = set()
_initialization_lock = threading.Lock()


def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_queue_path():
    configured = os.getenv("WEBHOOK_QUEUE_PATH", "").strip()
    if configured:
        return configured
    return os.path.join(os.path.dirname(SETTINGS_PATH) or ".", "webhook_queue.sqlite3")


def _connect():
    path = get_queue_path()
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    connection = sqlite3.connect(path, timeout=1)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=1000")
    return connection


@contextmanager
def _database():
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_queue():
    path = get_queue_path()
    if path in _initialized_paths:
        return
    with _initialization_lock:
        if path in _initialized_paths:
            return
        with _database() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS webhook_events (
                    event_id TEXT PRIMARY KEY,
                    destination TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    available_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_error TEXT NOT NULL DEFAULT ''
                )
                """
            )
            stale_before = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
            connection.execute(
                "UPDATE webhook_events SET status='pending' WHERE status='processing' AND updated_at < ?",
                (stale_before,),
            )
            retention_before = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(timespec="seconds")
            connection.execute(
                "DELETE FROM webhook_events WHERE status='done' AND updated_at < ?",
                (retention_before,),
            )
        _initialized_paths.add(path)


def _event_id(event):
    supplied = str(event.get("webhookEventId", "")).strip()
    if supplied:
        return supplied
    serialized = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "legacy-" + sha256(serialized.encode("utf-8")).hexdigest()


def enqueue_events(body):
    initialize_queue()
    destination = str(body.get("destination", ""))
    received_at = now_jst_iso()
    queue_time = _utc_now_iso()
    inserted = 0
    duplicate = 0
    with _database() as connection:
        for event in body.get("events", []):
            event_id = _event_id(event)
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO webhook_events
                    (event_id, destination, event_json, received_at, available_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    destination,
                    json.dumps(event, ensure_ascii=False, separators=(",", ":")),
                    received_at,
                    queue_time,
                    queue_time,
                ),
            )
            if cursor.rowcount:
                inserted += 1
            else:
                duplicate += 1
    return {"inserted": inserted, "duplicate": duplicate}


def claim_next():
    initialize_queue()
    now = _utc_now_iso()
    connection = _connect()
    try:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT * FROM webhook_events
            WHERE status='pending' AND available_at <= ?
            ORDER BY received_at, event_id
            LIMIT 1
            """,
            (now,),
        ).fetchone()
        if row is None:
            connection.commit()
            return None
        connection.execute(
            """
            UPDATE webhook_events
            SET status='processing', attempts=attempts+1, updated_at=?
            WHERE event_id=?
            """,
            (now, row["event_id"]),
        )
        connection.commit()
        item = dict(row)
        item["event"] = json.loads(item.pop("event_json"))
        return item
    finally:
        connection.close()


def mark_done(event_id):
    with _database() as connection:
        connection.execute(
            "UPDATE webhook_events SET status='done', updated_at=?, last_error='' WHERE event_id=?",
            (_utc_now_iso(), event_id),
        )


def mark_retry(event_id, error, attempts):
    delay = min(300, max(2, 2 ** min(int(attempts or 1), 8)))
    available_at = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat(timespec="seconds")
    with _database() as connection:
        connection.execute(
            """
            UPDATE webhook_events
            SET status='pending', available_at=?, updated_at=?, last_error=?
            WHERE event_id=?
            """,
            (available_at, _utc_now_iso(), str(type(error).__name__), event_id),
        )


def queue_status_counts():
    initialize_queue()
    with _database() as connection:
        rows = connection.execute(
            "SELECT status, COUNT(*) AS count FROM webhook_events GROUP BY status"
        ).fetchall()
    return {row["status"]: row["count"] for row in rows}


def start_worker(process_event):
    initialize_queue()

    def run():
        while True:
            item = claim_next()
            if item is None:
                time.sleep(0.25)
                continue
            try:
                process_event(item["destination"], item["event"], item["received_at"])
                mark_done(item["event_id"])
            except Exception as error:
                mark_retry(item["event_id"], error, int(item.get("attempts", 0)) + 1)
                time.sleep(0.5)

    worker = threading.Thread(target=run, name="webhook-queue-worker", daemon=True)
    worker.start()
    return worker
