from __future__ import annotations

import base64
import getpass
import secrets

import bcrypt

from core.config import ensure_directories
from core.security.bootstrap_store import is_bootstrapped, set_bootstrap
from core.storage.db import get_db_path


def _prompt_password() -> str:
    while True:
        password = getpass.getpass("Enter admin password (min 12 chars): ")
        confirm = getpass.getpass("Confirm admin password: ")
        if password != confirm:
            print("Passwords do not match. Try again.")
            continue
        if len(password) < 12:
            print("Password too short. Use at least 12 characters.")
            continue
        return password


def main() -> int:
    ensure_directories()
    if is_bootstrapped():
        print("Victus Local is already bootstrapped.")
        return 0

    password = _prompt_password()
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    secret_bytes = secrets.token_bytes(32)
    jwt_secret = base64.urlsafe_b64encode(secret_bytes).decode("utf-8")
    set_bootstrap(password_hash, jwt_secret)
    print(f"Bootstrap complete. Database: {get_db_path()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
