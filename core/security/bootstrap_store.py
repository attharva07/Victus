from __future__ import annotations

from datetime import datetime, timezone

import bcrypt

from core.storage.db import get_connection


def is_bootstrapped() -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT bootstrapped FROM bootstrap_state WHERE id = 1"
        ).fetchone()
    finally:
        conn.close()
    return bool(row["bootstrapped"]) if row else False


def set_bootstrap(admin_hash: str, jwt_secret: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM bootstrap_state")
        conn.execute(
            """
            INSERT INTO bootstrap_state
                (id, bootstrapped, admin_username, admin_password_hash, jwt_secret, created_at)
            VALUES
                (1, 1, ?, ?, ?, ?)
            """,
            ("admin", admin_hash, jwt_secret, now),
        )
        conn.commit()
    finally:
        conn.close()


def get_jwt_secret() -> str:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT jwt_secret FROM bootstrap_state WHERE id = 1 AND bootstrapped = 1"
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise RuntimeError("System is not bootstrapped")
    return str(row["jwt_secret"])


def verify_admin_password(plain: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT admin_password_hash
            FROM bootstrap_state
            WHERE id = 1 AND bootstrapped = 1
            """
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return False
    password_hash = str(row["admin_password_hash"])
    return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))
