Act as a Senior Python Full-Stack Developer, Streamlit specialist, database architect, and UX designer.

Create a complete, modular, secure, and user-friendly web application named:

Personal AI Library Manager

The application must allow a user to maintain a personal book collection, search books, edit records, delete records, generate reports, track lent books, manage wishlists, upload book covers, and use optional AI-powered features.

==============================
1. RECOMMENDED TECHNOLOGY STACK
==============================

Use the following technologies:

- Programming language: Python 3.11+
- Web framework: Streamlit
- Database ORM: SQLAlchemy
- Default database: SQLite
- Future database support: MySQL
- Data processing: Pandas
- Interactive charts: Plotly
- Excel export: openpyxl
- Fuzzy search: RapidFuzz
- Image processing: Pillow
- Environment variables: python-dotenv
- AI integration: provider-independent design supporting Azure OpenAI, OpenAI, or Ollama
- Optional natural-language database queries: LangChain, but only if it adds clear value
- Testing: pytest

Use SQLite as the default because this is initially a personal, locally hosted application. Design the database configuration so it can later be changed to MySQL through an environment variable without rewriting the application.

Do not hard-code passwords, API keys, connection strings, or secrets.

==============================
2. PROJECT STRUCTURE
==============================

Create the project using this structure:

personal_ai_library_manager/
├── app.py
├── config.py
├── database.py
├── models.py
├── repositories/
│   ├── __init__.py
│   ├── book_repository.py
│   ├── loan_repository.py
│   ├── wishlist_repository.py
│   ├── collection_repository.py
│   └── ai_summary_repository.py
├── services/
│   ├── __init__.py
│   ├── book_service.py
│   ├── report_service.py
│   ├── loan_service.py
│   ├── wishlist_service.py
│   ├── search_service.py
│   ├── export_service.py
│   ├── image_service.py
│   ├── ai_service.py
│   └── backup_service.py
├── pages/
│   ├── dashboard.py
│   ├── add_book.py
│   ├── view_books.py
│   ├── search_books.py
│   ├── edit_book.py
│   ├── delete_book.py
│   ├── reports.py
│   ├── wishlist.py
│   ├── loans.py
│   ├── collections.py
│   ├── ai_assistant.py
│   └── settings.py
├── utils/
│   ├── __init__.py
│   ├── validators.py
│   ├── formatters.py
│   ├── constants.py
│   └── theme.py
├── tests/
│   ├── test_book_service.py
│   ├── test_search_service.py
│   ├── test_loan_service.py
│   └── test_validators.py
├── data/
│   └── .gitkeep
├── uploads/
│   └── book_covers/
│       └── .gitkeep
├── backups/
│   └── .gitkeep
├── .streamlit/
│   └── config.toml
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── Dockerfile
└── docker-compose.yml

Apply separation of concerns:

- Pages must contain UI logic only.
- Repositories must contain database access logic.
- Services must contain business logic.
- Models must contain SQLAlchemy database models.
- Validators must perform reusable input validation.
- AI-provider code must be isolated in ai_service.py.
- Database connections must be managed safely and closed correctly.

==============================
3. DATABASE DESIGN
==============================

Create SQLAlchemy models for the following tables.

BOOKS TABLE

Fields:

- id: integer primary key, auto-increment
- book_name: string, required
- author: string, required
- category: string, optional
- price: decimal, required, non-negative
- purchase_date: date, optional
- publisher: string, optional
- isbn: string, optional and unique when supplied
- language: string, optional
- rating: integer between 1 and 5, optional
- reading_status: enum with values Unread, Reading, Read
- personal_review: text, optional
- notes: text, optional
- cover_image_path: string, optional
- is_favourite: boolean, default false
- created_at: timestamp
- updated_at: timestamp

TAGS TABLE

Fields:

- id
- name, unique and required

BOOK_TAGS TABLE

Fields:

- book_id
- tag_id

Use this as a many-to-many mapping table.

COLLECTIONS TABLE

Fields:

- id
- name, unique and required
- description
- created_at
- updated_at

BOOK_COLLECTIONS TABLE

Fields:

- book_id
- collection_id

Use this as a many-to-many mapping table.

WISHLIST TABLE

Fields:

- id
- book_name
- author
- category
- expected_price
- priority with values Low, Medium, High
- expected_purchase_date
- notes
- status with values Planned, Purchased, Cancelled
- created_at
- updated_at

LOANS TABLE

Fields:

- id
- book_id, foreign key to books
- borrower_name
- borrower_contact
- borrowed_date
- expected_return_date
- actual_return_date
- status with values Lent, Returned, Overdue
- notes
- created_at
- updated_at

AI_SUMMARIES TABLE

Fields:

- id
- book_id, foreign key to books
- provider
- model_name
- summary
- key_learnings
- recommended_audience
- difficulty_level
- generated_at
- source_basis
- content_hash

AI_CHAT_HISTORY TABLE

Fields:

- id
- session_id
- user_question
- assistant_answer
- created_at

APP_SETTINGS TABLE

Fields:

- id
- setting_key, unique
- setting_value
- updated_at

Create all tables automatically when the application starts for the first time.

Use Decimal or a database-safe numeric type for monetary values instead of relying only on floating-point calculations.

==============================
4. NAVIGATION AND USER INTERFACE
==============================

Create a clean Streamlit sidebar navigation menu with:

- Dashboard
- Add Book
- View Books
- Search Books
- Edit Book
- Delete Book
- Reports
- Wishlist
- Borrowed/Lent Books
- Tags and Collections
- AI Library Assistant
- Settings and Backup

Use:

- st.set_page_config()
- st.session_state
- st.form()
- st.columns()
- st.metric()
- st.tabs()
- st.dataframe()
- st.plotly_chart()
- st.file_uploader()
- st.download_button()
- st.dialog() or an equivalent confirmation workflow where supported
- st.toast(), st.success(), st.warning(), and st.error() appropriately

Requirements:

- Use a wide layout.
- Keep forms structured and easy to understand.
- Add tooltips or help text for complicated fields.
- Use Indian Rupee formatting, such as ₹1,250.00.
- Avoid unsafe HTML where standard Streamlit components are sufficient.
- Ensure that reruns do not duplicate database inserts.
- Prevent accidental data loss.
- Use unique widget keys.
- Use friendly empty-state messages when no records are available.

==============================
5. DASHBOARD
==============================

Display the following metrics:

- Total number of books
- Total amount invested
- Number of unique authors
- Number of unique categories
- Books currently being read
- Books completed
- Books in the wishlist
- Books currently lent
- Number of overdue loans
- Average book rating

Display:

- Latest five books added
- Favourite books
- Recently purchased books
- Recently returned books
- Books due for return soon

Create Plotly charts for:

- Number of books by author
- Number of books by category
- Books purchased by month
- Books purchased by year
- Monthly investment
- Yearly investment
- Price distribution
- Rating distribution
- Reading-status distribution
- Books by language

All dashboard values and charts must come from database queries and must update after CRUD operations.

MODERN SAAS DASHBOARD DESIGN

The dashboard must feel like a premium 2026 personal-library SaaS workspace, not a basic admin screen.

- Use a clean responsive grid with deliberate spacing, balanced density, rounded cards, soft shadows, and subtle hover transitions.
- Add a welcome hero that greets the signed-in user, displays the current date and a live library summary, and includes a book-themed graphic or relevant visual treatment.
- Present KPI cards for total books, total investment, unique authors, unique categories, active loans, overdue loans, and books due within seven days. Each card must have a distinct semantic icon or visual marker, concise context, and accessible contrast.
- Include analytics for books by category, books purchased by month, top authors, and investment trend. Use Plotly charts backed by real data, and retain transparent chart backgrounds so they work in both themes.
- Include a quick-actions section. Actions must navigate to existing workflows such as Add Book, Borrowed/Lent Books, View Books, Tags and Collections, and Reports; do not display inactive decorative controls.
- Include recent activity panels for recently added books, currently lent books, and recent returns, with helpful empty states.
- Include smart insights derived from live records: most expensive book, favourite author, most common category, and unread books.
- Use Poppins or Inter with clear type hierarchy. Use a professional library palette led by teal, blue-green, warm amber, and restrained alert red.
- Support mobile and tablet layouts. Cards must reflow without overlap or clipped text. At tablet widths, account for the visible Streamlit sidebar.
- Support Streamlit light and dark modes. Custom card foregrounds and backgrounds must remain readable in both modes; do not assume the browser colour-scheme media query matches Streamlit's manual theme setting.
- Prefer native Streamlit elements for interactive controls and keep custom HTML/CSS limited to presentation surfaces that Streamlit cannot style natively.

==============================
6. ADD BOOK
==============================

Create an Add Book form containing:

- Book name
- Author
- Category or genre
- Price
- Purchase date
- Publisher
- ISBN
- Language
- Rating from 1 to 5
- Reading status
- Personal review
- Notes
- Favourite checkbox
- Tags
- Collections
- Book-cover image upload

Validations:

- Book name is required.
- Author is required.
- Price cannot be negative.
- Rating must be between 1 and 5.
- Purchase date cannot be an invalid date.
- ISBN must be unique when supplied.
- Uploaded image must be PNG, JPG, JPEG, or WEBP.
- Validate the image content instead of trusting only its file extension.
- Use a file-size limit configured in constants.py.
- Generate a safe unique file name for uploaded images.

Display a preview of the uploaded cover before saving.

After insertion:

- Display a success message.
- Clear or safely reset the form.
- Display the generated book ID.
- Prevent duplicate insertion during a Streamlit rerun.

Include optional duplicate-book detection based on normalised book name, author, and ISBN. Warn the user before adding a probable duplicate.

==============================
7. VIEW BOOKS
==============================

Display all books in an interactive table.

Provide:

- Sorting
- Pagination or page-size controls
- Column selection
- Search box
- Filters
- Reset filters button
- Book-cover thumbnail where practical
- Book-detail view
- Empty-state message

Allow filtering by:

- Book name
- Author
- Category
- Publisher
- Language
- Reading status
- Rating
- Favourite status
- Tag
- Collection
- Purchase-date range
- Price range

Allow the user to select a row and view complete book details, including the cover image, review, notes, tags, collections, and active loan status.

==============================
8. SEARCH BOOKS
==============================

Implement normal and fuzzy search.

Normal search must support:

- Exact match
- Starts with
- Contains

Search across:

- Book name
- Author
- Category
- Publisher
- ISBN
- Notes
- Personal review
- Tags
- Collections

Use RapidFuzz for fuzzy search.

Requirements:

- Add an enable/disable fuzzy-search option.
- Add an adjustable similarity threshold.
- Return the match score.
- Rank matches by relevance.
- Ensure searches such as Pulakesh, Pulakeshi, and Pulkesi can return similar matching records when the configured threshold allows it.
- Combine text search with author, category, date, price, rating, tag, collection, language, and reading-status filters.
- Make matching case-insensitive.
- Normalise leading and trailing spaces.

Avoid loading the entire database unnecessarily where database-side filtering can be used.

==============================
9. EDIT BOOK
==============================

Allow the user to find and select a book using:

- Searchable book title
- Author
- ISBN
- Book ID

Load the existing record into an edit form.

Allow all editable fields to be modified, including:

- Book details
- Rating
- Reading status
- Favourite status
- Review
- Notes
- Tags
- Collections
- Cover image

Requirements:

- Apply the same validation used while adding a book.
- Show a clear Save Changes button.
- Update updated_at.
- Show a success message.
- Refresh displayed data.
- Allow replacement or removal of the existing cover.
- Remove an old cover file only when it is no longer required and the database update succeeds.
- Use a transaction to avoid partial updates.

==============================
10. DELETE BOOK
==============================

Allow a book to be selected by ID, title, author, or ISBN.

Before deletion:

- Display the full selected book details.
- Show whether the book has active loan records.
- Require explicit confirmation.
- Use a two-step confirmation workflow.
- Do not perform deletion based only on selecting an item.
- Disable or block deletion when an active loan exists, unless the loan is first resolved.

After a successful delete:

- Remove related tag and collection mappings safely.
- Handle related AI summaries and chat references according to the defined cascade policy.
- Delete the associated cover image safely where applicable.
- Show a success message.
- Refresh the application data.

Add a clearly documented cascade or restrict policy for related records.

==============================
11. REPORTS
==============================

Create a Reports page with the following tabs.

AUTHOR REPORT

Display:

- Author name
- Number of books
- Total amount invested
- Average price
- Average rating
- Percentage read

Charts:

- Books by author
- Investment by author

PRICE REPORT

Display:

- Total investment
- Highest-priced book
- Lowest-priced book
- Average price
- Median price
- Monthly investment
- Yearly investment

CATEGORY REPORT

Display:

- Number of books per category
- Total investment per category
- Average rating per category
- Reading completion by category

PURCHASE-TREND REPORT

Display:

- Books purchased by month
- Books purchased by year
- Spending by month
- Spending by year

RATING REPORT

Display:

- Top-rated books
- Rating distribution
- Highest-rated authors
- Favourite books
- Books without ratings

READING REPORT

Display:

- Read books
- Unread books
- Currently reading books
- Reading completion percentage
- Books read by category
- Books read by author

LOAN REPORT

Display:

- Active loans
- Returned books
- Overdue books
- Upcoming return dates
- Most frequently lent books

CUSTOM REPORT

Provide combined filters:

- Book name
- Author
- Category
- Publisher
- Language
- Reading status
- Rating
- Tag
- Collection
- Date range
- Price range
- Loan status

Display filtered results in:

- Table format
- Summary metrics
- Appropriate Plotly charts

LIBRARY INSIGHTS AND ANALYTICS DESIGN

The Reports page must feel like a premium Library Insights and Analytics centre, not a basic count report. It must use the existing Streamlit application architecture and real database data. Do not introduce Android, Jetpack Compose, or Material Design dependencies into this Python project.

- Start with a responsive summary dashboard of modern metric cards for total books, total investment, total authors, categories, currently lent books, returned books, overdue books, and favourite category. Each card must use a meaningful Material icon, accessible semantic colour, concise context, and native Streamlit presentation where possible.
- Provide advanced report filters for date range, category, author, price range, tags, collections (libraries), and borrower. Apply filters consistently to every metric, chart, data table, and export. Use database-side filtering where practical and avoid exposing borrower contact details.
- Financial analytics must show total investment, monthly and yearly spending, average book price, most expensive book, cheapest book, category spending, and a chronological spending trend. Include Plotly line, monthly bar, and category donut or pie charts with transparent backgrounds.
- Collection growth analytics must show books added by month and year, library growth trend, author discovery trend, category expansion trend, and clear growth indicators derived only from stored timestamps.
- Author analytics must show top authors by book count, recently discovered authors when dates are available, favourite author derived from actual favourites and ratings, author distribution, and a horizontal ranking chart.
- Category analytics must show the largest and smallest categories, books per category, category ranking, and the fastest-growing category only when historical data supports that conclusion. Use donut or pie charts and concise ranking surfaces.
- Lending analytics must show total loans, currently lent books, returned books, overdue books, frequent borrowers, average completed-loan duration, loan-status distribution, and a borrowing timeline when data is available. Never display borrower contact information in reports.
- Include a Library Intelligence section with cards for largest collection category, total collection value, books added this month, most purchased author, fastest-growing category when supported, average book cost, collection growth score, and a top-ten valuable-books table. These are data-backed insights and must explain insufficient data instead of inventing conclusions.
- Include a Personal Reading Journey section with the first recorded purchase, latest purchase, books purchased each year, collection growth timeline, author discovery timeline, and category diversification score. Present timelines through interactive Plotly charts and data-driven milestones.
- Retain practical CSV and Excel exports for the filtered report data. Treat PDF export, printing, and native sharing as separately documented optional integrations; do not add mandatory dependencies or inactive controls for them.
- If multiple libraries are introduced later, support individual-library, combined-library, and comparison views through the collection/library model. Do not fabricate a separate library entity until the data model supports it.
- Use the same premium visual language as the dashboard: Poppins or Inter, teal and blue-green primary surfaces, warm amber accents, restrained alert red, balanced density, responsive cards, smooth but subtle transitions, and readable light and dark theme treatment. Prefer native Streamlit controls and keep custom CSS limited to presentation gaps.

==============================
12. EXPORT FEATURES
==============================

Allow users to download:

- All book records as CSV
- All book records as Excel
- Filtered report results as CSV
- Filtered report results as Excel
- Loan reports as CSV and Excel
- Wishlist as CSV and Excel

Excel requirements:

- Meaningful worksheet names
- Bold headers
- Auto-adjusted column widths
- Currency and date formatting
- Separate sheets for books, loans, wishlist, tags, collections, and summary where appropriate

Add PDF export only as a separately documented optional module. Do not make PDF libraries mandatory for the core application.

Ensure exports handle empty datasets gracefully.

==============================
13. BOOK-COVER MANAGEMENT
==============================

Allow book-cover images in:

- PNG
- JPG
- JPEG
- WEBP

Requirements:

- Display image preview before saving.
- Generate safe unique file names.
- Store only the relative path in the database.
- Add a configurable upload-size limit.
- Validate image content using Pillow.
- Generate thumbnail versions when useful.
- Display a placeholder image when a cover is unavailable.
- Handle missing files gracefully.
- Prevent path traversal.
- Do not expose arbitrary local file paths.

Keep the image service ready for future cloud-storage integration.

==============================
14. REVIEWS, RATINGS, AND NOTES
==============================

Allow the user to:

- Set a 1-to-5 rating.
- Mark a book as favourite.
- Add a personal review.
- Add reading notes.
- Change reading status.
- Update the review later.

Provide:

- Top-rated books report
- Lowest-rated books report
- Rating distribution
- Favourite-books view
- Books without ratings
- Highest-rated authors

Do not treat an absent rating as zero.

==============================
15. BORROWED AND LENT BOOK TRACKING
==============================

Create a complete loan-management page.

Allow the user to:

- Select a book to lend.
- Enter borrower name.
- Enter optional contact details.
- Select borrowed date.
- Select expected return date.
- Add loan notes.
- Mark the book as returned.
- Record actual return date.
- View loan history.

Statuses:

- Lent
- Returned
- Overdue

Rules:

- A book with an active loan cannot be lent again.
- A returned book becomes available.
- Overdue status must be calculated from expected return date and actual return status.
- Do not permanently overwrite historical loan records.
- Warn the user about overdue books.
- Validate that expected return date is not earlier than borrowed date.
- Validate that actual return date is not earlier than borrowed date.

Dashboard widgets:

- Active loans
- Overdue books
- Books due soon

==============================
16. TAGS AND COLLECTIONS
==============================

Allow users to create reusable tags such as:

- History
- Kannada Literature
- Technology
- Artificial Intelligence
- Test Automation
- Leadership
- Fiction
- Self-help

Allow users to create collections such as:

- Chalukya History
- AI and Machine Learning
- Test Automation
- Leadership Books
- Books to Read This Year

Features:

- Add tags
- Rename tags
- Delete unused tags
- Assign multiple tags to a book
- Remove tags from a book
- Add collections
- Edit collections
- Delete empty collections
- Assign a book to multiple collections
- Filter books by tags and collections
- Display tag and collection summaries

Prevent deletion of a tag or collection that is in use unless the user explicitly confirms how the mappings should be handled.

==============================
17. READING WISHLIST
==============================

Create a wishlist page.

Fields:

- Book name
- Author
- Category
- Expected price
- Priority
- Expected purchase date
- Notes
- Status

Allow:

- Add wishlist item
- Search wishlist
- Filter by priority and status
- Edit wishlist item
- Delete wishlist item
- Mark as purchased

When marked as purchased:

- Open or populate an Add Book form.
- Transfer relevant wishlist values.
- Allow the user to verify price and purchase date.
- Save the new book and update the wishlist status in one transaction.
- Do not silently create incomplete book records.

Provide wishlist reports by priority, category, expected month, and status.

==============================
18. THEME AND DARK MODE
==============================

Support:

- Light theme
- Dark theme
- System/default theme where practical

Use Streamlit theme configuration in .streamlit/config.toml.

Requirements:

- Store the preference in session state or app settings.
- Ensure text and charts remain readable in all themes.
- Avoid excessive custom CSS.
- If a runtime theme switch cannot be applied without reloading, explain this clearly in README.md and provide the supported implementation.

==============================
19. AI BOOK SUMMARY GENERATOR
==============================

Create an optional AI summary feature.

The application must continue to work when AI is not configured.

Support a provider abstraction for:

- Azure OpenAI
- OpenAI
- Ollama running locally

The application must not assume access to copyrighted book text.

Generate summaries only from content supplied or authorised by the user, such as:

- Personal notes
- Personal review
- User-entered description
- User-uploaded authorised text extract
- Public-domain content
- User-provided metadata

Do not invent a summary based only on a title.

If there is insufficient source content, clearly tell the user to provide notes, a description, or an authorised extract.

Generated output can include:

- Concise summary
- Key learnings
- Themes
- Reading difficulty
- Recommended audience

Do not generate or reproduce copyrighted quotes from books.

Cache AI results in AI_SUMMARIES using:

- Book ID
- Provider
- Model name
- Source basis
- Content hash
- Generated date

Allow the user to regenerate a summary explicitly.

==============================
20. AI BOOK RECOMMENDATIONS
==============================

Create a recommendation feature based primarily on books already stored in the user's own library.

Use:

- Category
- Author
- Tags
- Collections
- Language
- Reading status
- Rating
- Favourite status

Provide:

- Similar books already owned
- Suggested next book to read
- Highly rated unread books
- Books from favourite categories
- Books from favourite authors

Clearly label recommendations as suggestions.

Do not invent external book records.

If an external books API is added later:

- Place it behind a separate service.
- Make it optional.
- Show the external source.
- Handle unavailable API responses.
- Do not fabricate book metadata.

==============================
21. NATURAL-LANGUAGE SEARCH
==============================

Add an optional natural-language search interface supporting questions such as:

- Show all books by S. L. Bhyrappa.
- Show books purchased in 2025.
- Show books costing more than ₹500.
- Show unread Kannada history books.
- Which author has the most books in my collection?
- Show overdue lent books.
- Suggest my next highly rated unread book.

Security requirement:

Do not allow the AI model to generate and execute unrestricted SQL directly.

Use one of these safer approaches:

1. Convert the user question into a validated structured filter object, or
2. Map the request to a fixed set of approved query operations.

Only allow read-only operations from the AI assistant.

Display:

- Interpreted filters
- Result count
- Result table
- Helpful message when the request cannot be interpreted

Do not expose database internals, credentials, or arbitrary file-system access.

==============================
22. BOOK KNOWLEDGE ASSISTANT
==============================

Add a Streamlit chat interface that answers questions using the user's stored library data.

Examples:

- Which Kannada history books do I own?
- Which author has the most books in my collection?
- Show books purchased above ₹1,000.
- Which books are currently lent?
- What books are overdue?
- Which books have I not read?
- Suggest the next book based on my ratings.
- Show my total investment by year.

Requirements:

- Limit answers to data available in the application's database.
- Clearly state when no matching data exists.
- Display the matching records that support the answer.
- Use validated read-only query operations.
- Do not modify or delete records through chat.
- Do not infer facts that are not stored.
- Allow chat history to be cleared.
- Make persistent chat history optional.
- Protect personally identifiable borrower data from appearing unnecessarily in assistant responses.

If an LLM is unavailable, provide a rule-based fallback for common questions.

==============================
23. OCR BOOK-COVER SCANNER
==============================

Implement OCR as an optional feature.

Allow the user to upload a book-cover or title-page image.

Attempt to extract:

- Book title
- Author
- ISBN

Requirements:

- Display extracted values for review.
- Never insert OCR results automatically.
- Let the user correct all values before saving.
- Display a confidence warning when results may be inaccurate.
- Put OCR integration behind an OCR service interface.
- Keep OCR dependencies optional where possible.
- Handle unsupported or unreadable images gracefully.

==============================
24. SMART READING INSIGHTS
==============================

Generate personalised insights from database records, including:

- Most-owned categories
- Favourite authors based on ratings and favourites
- Highly rated unread books
- Average purchase price
- Monthly and yearly investment
- Reading completion rate
- Most-used tags
- Largest collections
- Books awaiting rating
- Books lent frequently

Every insight must be based on actual stored data.

When insufficient data exists, display an explanatory empty state instead of generating an unsupported conclusion.

==============================
25. BACKUP AND RESTORE
==============================

Create a Settings and Backup page.

Support:

- Downloading a SQLite database backup
- Creating timestamped local backups
- Viewing available local backups
- Restoring from a selected valid backup
- Exporting all logical data to Excel
- Importing validated book records from a CSV or Excel template

Restore requirements:

- Require explicit confirmation.
- Create a safety backup before restore.
- Validate the uploaded database before replacing the active database.
- Prevent restore during an active write transaction.
- Display clear success or failure messages.

Import requirements:

- Provide a downloadable template.
- Validate required columns.
- Show a preview.
- Show validation failures by row.
- Detect probable duplicates.
- Require explicit submission before importing.

==============================
26. LOGGING AND ERROR HANDLING
==============================

Use Python logging.

Log:

- Application startup
- Database initialisation
- Book creation
- Book update
- Book deletion
- Loan creation and return
- Import and export events
- Backup and restore events
- AI provider errors
- Unexpected exceptions

Do not log:

- API keys
- Passwords
- Full database connection secrets
- Sensitive borrower contact details
- Uploaded text content unless explicitly required

Display user-friendly errors in the UI and detailed diagnostic information only in logs.

Use transactions for multi-step operations.

==============================
27. SECURITY AND PRIVACY
==============================

Implement:

- Parameterised queries through SQLAlchemy
- Input validation
- Safe uploaded-file handling
- File-size restrictions
- Restricted image formats
- Image-content verification
- Environment variables for secrets
- Safe relative file paths
- Read-only AI query operations
- No unrestricted command execution
- No unrestricted SQL execution
- No secret values displayed in the UI
- Clear handling of borrower contact details
- Safe error messages that do not expose stack traces to end users

Create .env.example containing placeholders only:

DATABASE_URL=sqlite:///data/library.db
AI_PROVIDER=none
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=
OPENAI_API_KEY=
OPENAI_MODEL=
OLLAMA_BASE_URL=
OLLAMA_MODEL=

==============================
28. DATABASE CONFIGURATION
==============================

Use DATABASE_URL from environment variables.

Default:

sqlite:///data/library.db

Document a MySQL example in README.md, but do not include real credentials.

Example format:

mysql+pymysql://username:password@hostname/database_name

Ensure database-specific behaviour is isolated so migration from SQLite to MySQL is straightforward.

Use database migrations if Alembic is added. If Alembic is not implemented in the initial version, clearly document schema-upgrade limitations.

==============================
29. TESTING REQUIREMENTS
==============================

Add pytest tests for:

- Adding a valid book
- Rejecting an empty book name
- Rejecting an empty author
- Rejecting a negative price
- Rejecting an invalid rating
- Duplicate ISBN handling
- Editing a book
- Deleting a book
- Preventing deletion with an active loan
- Fuzzy search
- Returning a lent book
- Overdue-loan calculation
- Wishlist conversion to purchased book
- CSV import validation
- Structured natural-language query validation

Use a separate temporary test database.

Do not run tests against the user's production database.

==============================
30. REQUIREMENTS.TXT
==============================

Create a minimal, compatible requirements.txt containing appropriate packages such as:

- streamlit
- sqlalchemy
- pandas
- plotly
- openpyxl
- rapidfuzz
- pillow
- python-dotenv
- pymysql
- pytest

Add AI, OCR, PDF, and LangChain dependencies only if the corresponding feature is implemented and enabled.

Avoid unnecessary packages.

==============================
31. STREAMLIT CLOUD AND DEPLOYMENT
==============================

Prepare the application for:

- Local execution
- Streamlit Community Cloud
- Docker
- Future Azure deployment

Generate:

- requirements.txt
- README.md
- .gitignore
- Dockerfile
- docker-compose.yml
- .env.example
- .streamlit/config.toml

Do not claim true one-click deployment if external resources, secrets, persistent storage, or database setup are still required.

In README.md, document:

- Python setup
- Virtual-environment creation
- Dependency installation
- Local application launch
- Database configuration
- AI-provider configuration
- Ollama configuration
- Optional MySQL configuration
- Streamlit Cloud deployment considerations
- Docker commands
- Backup instructions
- Known limitations

Local launch command:

streamlit run app.py

Explain that local SQLite files and uploaded images may require persistent storage planning when deployed to a cloud environment.

==============================
32. README CONTENT
==============================

The README must contain:

- Application overview
- Feature list
- Architecture
- Project structure
- Installation instructions
- Environment-variable configuration
- Running locally
- Running tests
- Docker instructions
- Streamlit deployment guidance
- Database backup and restore
- MySQL migration guidance
- AI feature setup
- Privacy and security notes
- Troubleshooting
- Known limitations
- Screenshots section with placeholders
- Future enhancements

==============================
33. CODE QUALITY
==============================

Apply these standards:

- PEP 8
- Type hints
- Docstrings
- Small and testable functions
- Reusable validation
- Repository and service layers
- Centralised constants
- Transactions for related database changes
- Clear exception handling
- Minimal duplication
- No hard-coded secrets
- No incomplete placeholder functions in the core CRUD workflow
- No hidden global mutable database session
- No unsafe raw SQL
- No deprecated Streamlit APIs where current alternatives exist

Use comments to explain important decisions, not obvious syntax.

==============================
34. IMPLEMENTATION SEQUENCE
==============================

Build the application in phases so that each phase remains runnable.

Phase 1:
- Project structure
- Configuration
- Database models
- Database initialisation
- Add book
- View books
- Edit book
- Delete book
- Basic search
- Basic dashboard

Phase 2:
- Reports
- CSV and Excel export
- Validation improvements
- Tags
- Collections
- Wishlist

Phase 3:
- Loans
- Book-cover upload
- Ratings
- Reviews
- Reading status
- Dashboard enhancements
- Backup and restore

Phase 4:
- Fuzzy search