# Phase 3.1 Bootstrap Decision

## What bootstrap is

Victus Local requires a one-time bootstrap step to establish the admin account and the JWT signing
secret. These values are stored in the existing SQLite database under the OS-stable data directory.
After bootstrap, login and token verification use the stored values instead of defaults.

## How to run

Run the bootstrap module locally:

```bash
python -m apps.local.bootstrap
```

You will be prompted to create the admin password (minimum 12 characters). On success, the tool
prints the database path so you can confirm where the persistent state lives.

## How to reset safely

Bootstrap is intended to run once per installation. To reset, stop Victus Local and delete the
SQLite database file in the data directory (for example, `victus_local.sqlite3`). This will remove
memories, finance entries, and the bootstrap state. Be sure you have backups before deleting data.
