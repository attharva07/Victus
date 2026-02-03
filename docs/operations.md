# Victus Local Operations (Phase 1)

## Run the local launcher
```bash
python -m apps.local.launcher
```

The server binds to `127.0.0.1:8000` by default.

## Data directory
Victus stores data in a stable external directory:
- Windows: `%APPDATA%/Victus/`
- Linux/macOS: `~/.victus/`

You can override this with `VICTUS_DATA_DIR` for development/testing.

## Reset auth safely
1. Stop the local server.
2. Delete the auth file in the data directory: `auth.json`.
3. Restart the server to regenerate credentials.

The initial admin password defaults to `admin` unless `VICTUS_ADMIN_PASSWORD` is set in the environment.
