# Email Sending Automation

This project is a Streamlit application that sends personalized emails to a list of employees from a CSV file. It uses the Gmail API for sending emails and Google OAuth 2.0 for authentication.

## ⚙️ Prerequisites

Before you begin, ensure you have the following:

- A Google Cloud Project.
- `credentials.json` file obtained from Google Cloud Console.

### Step-by-Step: Get `credentials.json` from Google Cloud

1.  **Create a Google Cloud Project**
    - Go to the [Google Cloud Console](https://console.cloud.google.com/).
    - Log in with your Gmail or Workspace account.
    - Click the project dropdown and select **New Project**.
    - Give it a name (e.g., `Employee Email Sender`) and click **Create**.

2.  **Enable the Gmail API**
    - In the top search bar, type "Gmail API".
    - Click on "Gmail API" and then click **Enable**.
    - You can also enable it directly from this link: [https://console.cloud.google.com/apis/api/gmail.googleapis.com/metrics](https://console.cloud.google.com/apis/api/gmail.googleapis.com/metrics)

3.  **Create OAuth 2.0 Credentials**
    - Go to **APIs & Services > Credentials**.
    - Click **+ Create Credentials > OAuth client ID**.
    - If you haven’t already configured a consent screen:
        - It will ask you to set up the OAuth consent screen first.
        - Choose **External**, fill in basic info (app name, your email, etc.).
        - Add scope: `.../auth/gmail.send` (optional, can be added automatically).
        - Save and continue until finished.
    - Now create OAuth Client ID:
        - Application type → **Desktop App**
        - Name it (e.g., `Gmail Python App`)
        - Click **Create**.
        - A dialog will appear — click **Download JSON**.
        - Save it as `credentials.json` in your project folder (the same directory as your script).

4.  **Authorize Your App**
    - The first time you run the Streamlit app:
        - It will open a browser window asking you to log in.
        - Log in with your Gmail account.
        - Allow access to "send emails".
        - It will create a token file (e.g., `token.json`) so you don’t have to log in every time.

## 📦 Installation

### Python

This project requires Python 3.12 or higher. If you don't have Python installed, you can download it from [python.org](https://www.python.org/downloads/).

### uv

This project uses `uv` for dependency management. You can install `uv` with the following command:

```bash
pip install uv
```

If you don't have `pip` installed, you can follow the instructions [here](https://pip.pypa.io/en/stable/installation/).

## 🚀 Running the App

1.  **Install dependencies:**
    ```bash
    uv sync
    ```

2.  **Run the Streamlit app:**
    ```bash
    uv run streamlit run app.py
    ```

## 📋 Usage

1.  Add your email template in `email_template.html`.
2.  Create a CSV file named `employees.csv` with headers: `name`, `email`, `amount`.
3.  Run the application.
4.  Press the "Send Emails" button.

## ✨ Features

- Sends personalized emails to a list of recipients from a CSV file.
- Uses a customizable HTML email template.
- Logs the status of sent emails into a CSV file.
- Simple and easy-to-use web interface built with Streamlit.
