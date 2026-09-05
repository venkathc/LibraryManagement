# Gmail Return Reminders

The Lending Desk can email a borrower reminder when their saved loan contact contains an email address.

1. Enable two-step verification for the Gmail account that will send reminders.
2. Create a Google [App Password](https://myaccount.google.com/apppasswords) for Mail.
3. Add these values to the project's ignored `.env` file:

```env
GMAIL_ADDRESS=your-gmail-address@gmail.com
GMAIL_APP_PASSWORD=your-16-character-google-app-password
```

Restart Streamlit after changing `.env`. Gmail App Passwords are 16 characters and are different from the normal Gmail sign-in password. Do not place either value in source code or commit `.env`.