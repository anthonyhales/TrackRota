# On Call Tracker – ALPHA Release 1

This is **ALPHA Release 1** of an internal on-call rota manager.

## What’s included
- FastAPI backend + Jinja server-rendered pages
- SQLite database (stored in a Docker volume)
- Login (email + password) with roles: **Admin / Manager / Staff**
- Pages: Dashboard, Staff, Shift Types, Rota (week view), Users, Settings
- SB Admin template integration (you provide assets locally)

## Quick start (Docker)
1. Build + run:
   ```bash
   docker compose up -d --build
   ```

2. (First run) Create an initial admin user by setting environment variables in `docker-compose.yml`:
   - `APP_BOOTSTRAP_ADMIN_EMAIL`
   - `APP_BOOTSTRAP_ADMIN_PASSWORD`

   Then restart the container.

3. Open:
   - http://localhost:8555

## Default roles
- **Admin**: full access
- **Manager**: manage staff and rotas
- **Staff**: view-only (can see all rotas)

## Notes
- This is ALPHA: minimal validation, basic UI interactions, and no audit log yet.
- Next iterations can add: swap requests, time-off management, drag-and-drop rota edits, notifications.

