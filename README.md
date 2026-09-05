# Personal AI Library Manager

A local Streamlit workspace for maintaining one or more personal book collections. It supports catalogue management, search, reporting, lending, wishlists, backups, and optional email reminders while keeping its SQLite data on the local machine.

## Current features

- **Library workspace:** select an active library, save a default library, and keep books, dashboard metrics, reports, lending, and edit-book results scoped to that library.
- **Access control:** global Administrator, User, and Guest accounts, with Owner, Admin, and Member roles for each library membership.
- **Catalogue:** add, edit, view, filter, search, bulk-manage, and delete books; manage cover images, favourites, reading states, reviews, notes, tags, and collections.
- **Search:** exact, starts-with, contains, and RapidFuzz matching with thresholds, filters, match scores, saved searches, and recent searches.
- **Dashboard:** active-library KPIs, quick actions, recent activity, lending status, Books by category, Borrowing activity, Loan health, and optional collection insights.
- **Reports:** report builder plus overview and optional insights; Book, Member, Loan, Analytics, Library, Wishlist, and Financial report categories; scoped filters and CSV/Excel downloads.
- **Wishlist:** Planned, Ordered, Purchased, and Cancelled states; priorities, filters, exports, and conversion into an active-library book.
- **Lending Desk:** lend and return books, view active/overdue/returned history, extend due dates with an audit trail, view borrower history, and export loan data.
- **Tags and collections:** reusable tags with colour and descriptions, plus collection management and assignment.
- **Data safety:** SQLite initialisation and additive migrations, validated cover uploads, duplicate checks, local backup and restore, and CSV/Excel export.
- **About page:** application and developer details for Venkatesh Kumar HC, AI Engineer at Telstra India Ltd.

## Sign in and user roles

The web application requires sign-in before access. The initial administrator account is:

- Username: `admin`
- Password: `admin123`

Administrators can open **User management** to create users, edit usernames and roles, reset passwords, and delete non-administrator accounts. Passwords are stored as salted PBKDF2 hashes.

- **Administrator**: full application access, including user management and deleting books.
- **User**: all standard library features except deleting books.
- **Guest**: read-only access to Dashboard, View Books, Search Books, Reports, and About this app.

The sign-in username field lists existing accounts. The sidebar provides **Switch user**, which can be cancelled to return to the current session, and **Sign out**, which clears the session.

## Active libraries and roles

The selected library is the active workspace. Book listings, search, editing, lending, dashboard values, and reports are based on that selection. Users can choose a default library in Settings. Administrators have application-wide administration; library memberships determine Owner, Admin, or Member access within a library.

## Dashboard and images

- The dashboard displays active-library collection and lending KPIs, recent activity, default charts, and optional collection insights.
- The Book images control accepts PNG, JPG, JPEG, or WEBP files.
- The first uploaded image is used as the book's primary cover for existing views; every uploaded image is retained with the book.
- Editing a book displays its current images and allows additional images to be uploaded.

## Reports, wishlist, and lending

Reports use the active library and provide a report builder, KPI overview, and an optional Insights view. Filtered book, loan, and wishlist data can be downloaded as CSV or Excel.

The wishlist supports Planned, Ordered, Purchased, and Cancelled states. Marking an item as purchased opens a verified conversion flow that creates the book in the selected library.

The Lending Desk prevents simultaneous loans of the same book, calculates overdue items from due dates, retains returned-loan history, and records every due-date extension. Borrower contact information is kept out of reports. The borrower directory is currently derived from historical loan records rather than a separately persisted borrower profile.

## Run locally

```bash
cd LibraryManagement-web
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
source .venv/bin/activate
.venv/bin/python -m streamlit run app.py
```

The default database is `data/library.db`. To use another SQLAlchemy-compatible database later, set `DATABASE_URL` in `.env`; credentials are never committed to the project.

## Gmail return reminders

The Lending Desk can email a borrower reminder when their loan contact includes an email address. Follow [GMAIL_SETUP.md](GMAIL_SETUP.md) to configure a Gmail App Password in the ignored local `.env` file. The reminder service first attempts Gmail SSL on port 465, then STARTTLS on port 587. Managed networks may block both SMTP ports; being able to access Gmail in a browser does not indicate that SMTP is available.

## Installable macOS app

Build a standalone macOS application from the project root:

```bash
./build_macos_app.sh
```

Open `dist/Personal AI Library Manager.app` and drag it to Applications to install it. The app stores its database, uploaded covers, and backups in `~/Library/Application Support/Personal AI Library Manager`, so application updates do not overwrite your library data.

## Move to Another System

Copy the complete project folder, including `data/library.db` and `uploads/book_covers`, to preserve the catalogue and uploaded images. Do not copy `.venv`; create a new virtual environment on the destination system and run the commands in [Run locally](#run-locally).

## Test

```bash
.venv/bin/python -m pytest -q
```

The current suite contains 19 passing tests. Tests use an isolated temporary database and do not run against the local library database.

## Current limitations

- AI summaries, natural-language assistant workflows, OCR, and external metadata lookup are not currently implemented.
- PDF export, print integration, SMS/WhatsApp delivery, calendar scheduling, and a reminder delivery audit log are not currently implemented.
- Gmail reminders require local configuration and outbound SMTP access; an HTTPS email provider can be added when SMTP is unavailable.
