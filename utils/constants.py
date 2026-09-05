"""Application-wide constants."""

READING_STATUSES = ("Unread", "Reading", "Read")
WISHLIST_PRIORITIES = ("Low", "Medium", "High")
WISHLIST_STATUSES = ("Planned", "Ordered", "Purchased", "Cancelled")
LOAN_STATUSES = ("Lent", "Returned", "Overdue")
ALLOWED_COVER_FORMATS = {"PNG", "JPEG", "WEBP"}
MAX_COVER_UPLOAD_BYTES = 5 * 1024 * 1024
