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
   - http://localhost:8000

## Add SB Admin assets (local)
Download the SB Admin template zip from Start Bootstrap, then copy the following folders into:

`app/static/sb-admin/`

You should end up with something like:
- `app/static/sb-admin/css/`
- `app/static/sb-admin/js/`
- `app/static/sb-admin/vendor/`

If those folders are missing, the app will still run, but styling will look plain.

## Default roles
- **Admin**: full access
- **Manager**: manage staff and rotas
- **Staff**: view-only (can see all rotas)

## Notes
- This is ALPHA: minimal validation, basic UI interactions, and no audit log yet.
- Next iterations can add: swap requests, time-off management, drag-and-drop rota edits, notifications.

