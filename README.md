# Personal AI Library Manager

A local Streamlit application for maintaining a personal book catalogue.

## Implemented features

The application provides SQLite configuration, database initialisation, basic add, view, search, edit, delete, and dashboard workflows. Phase 2 adds reusable tags and collections, wishlist management and purchase conversion, catalogue reports, and CSV/Excel downloads. Phase 3 adds validated book-image uploads, lending and return history, loan-aware dashboard metrics, and guarded SQLite backup and restore. Phase 4 adds optional RapidFuzz-powered search with adjustable similarity thresholds and relevance scores.

## Sign in and user roles

The web application requires sign-in before access. The initial administrator account is:

- Username: `admin`
- Password: `admin123`

Administrators can open **User management** to create users, edit usernames and roles, reset passwords, and delete non-administrator accounts. Passwords are stored as salted PBKDF2 hashes.

- **Administrator**: full application access, including user management and deleting books.
- **User**: all standard library features except deleting books.
- **Guest**: read-only access to Dashboard, View Books, Search Books, Reports, and About this app.

The sign-in username field lists existing accounts. The sidebar provides **Switch user**, which can be cancelled to return to the current session, and **Sign out**, which clears the session.

## Dashboard and Images

- The dashboard displays catalogue metrics in a bordered grid, with a pale green library row and pale amber lending row.
- The Book images control accepts multiple PNG, JPG, JPEG, or WEBP files in a single upload.
- The first uploaded image is used as the book's primary cover for existing views; every uploaded image is retained with the book.
- Editing a book displays its current images and allows additional images to be uploaded.

## Run locally

```bash
cd LibraryManagement
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
source .venv/bin/activate
.venv/bin/python -m streamlit run app.py
```

The default database is `data/library.db`. To use another SQLAlchemy-compatible database later, set `DATABASE_URL` in `.env`; credentials are never committed to the project.

## Move to Another System

Copy the complete project folder, including `data/library.db` and `uploads/book_covers`, to preserve the catalogue and uploaded images. Do not copy `.venv`; create a new virtual environment on the destination system and run the commands in [Run locally](#run-locally).

## Test

```bash
pytest
```
