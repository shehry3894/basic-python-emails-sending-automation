import os
import time
import base64
import pytz
import pickle
import streamlit as st
import pandas as pd

from jinja2 import Environment, select_autoescape
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


# --- Gmail Auth ---
def get_gmail_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build("gmail", "v1", credentials=creds)


# --- Email Creator ---
def format_currency(value):
    try:
        # Convert to float first to handle potential decimal inputs, then round to nearest integer
        # and format with comma as thousands separator, no decimal places
        return f"{int(round(float(value))):,}"
    except (ValueError, TypeError):
        return value  # Return original value if conversion fails


def create_message(sender, to, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["From"] = sender
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


# --- Email Sending Logic ---
def send_emails(main_df, df_indices_to_process, template, service, sender, local_timezone, progress_bar,
                preview_placeholder, subject_template):
    total = len(df_indices_to_process)
    failed_placeholder = st.empty()
    success_placeholder = st.empty()
    info_placeholder = st.empty()
    for i, idx in enumerate(df_indices_to_process):
        row = main_df.loc[idx]

        if row['status'] == 'sent':
            info_placeholder.info(f"⏩ Skipping ({row['email']}) as it's already sent.")
            progress_bar.progress((i + 1) / total)
            time.sleep(0.1)
            continue

        try:
            html_body = template.render(
                email=row["email"],
                amount=row.get("amount")
            )

            subject = subject_template.render(
                email=row["email"],
                amount=row.get("amount")
            )

            message = create_message(sender, row["email"], subject, html_body)
            service.users().messages().send(userId="me", body=message).execute()

            main_df.loc[idx, "status"] = "sent"
            main_df.loc[idx, "timestamp"] = datetime.now(local_timezone).isoformat()
            success_placeholder.write(f"✅ Sent to ({row['email']})")
            preview_placeholder.dataframe(main_df)

        except Exception as e:
            main_df.loc[idx, "status"] = f"failed: {e}"
            main_df.loc[idx, "timestamp"] = datetime.now(local_timezone).isoformat()
            failed_placeholder.error(f"❌ Failed to send to {row['email']}: {e}")
            preview_placeholder.dataframe(main_df)

        progress_bar.progress((i + 1) / total)
        time.sleep(2)  # safe pacing
    return main_df


# --- Streamlit App ---
st.set_page_config(page_title="Email Automation 1.0", layout="centered")
st.title("📧 Email Automation 1.0")

st.write("This app lets you send personalized emails to all employees easily.")

# Upload Email Template
template_file = st.file_uploader("Upload Email Template (HTML)", type=["html"])

# Dummy data for template preview
dummy_data = {
    "email": "john.doe@example.com",
    "amount": 20500
}

if template_file:
    template_file.seek(0)
    template_content_for_preview = template_file.read().decode("utf-8")

    env_preview = Environment(
        loader=None,
        autoescape=select_autoescape(['html', 'xml'])
    )
    env_preview.filters['format_currency'] = format_currency

    # Extract subject and body for preview
    template_lines_preview = template_content_for_preview.split('\n')
    first_line_preview = template_lines_preview[0]

    if first_line_preview.startswith("Subject:"):
        body_template_str_preview = '\n'.join(template_lines_preview[1:])
    else:
        body_template_str_preview = template_content_for_preview

    template_preview = env_preview.from_string(body_template_str_preview)

    st.subheader("Template Preview with Dummy Data")
    try:
        # Render with dummy data
        rendered_html = template_preview.render(**dummy_data)
        st.html(rendered_html)
    except Exception as e:
        st.error(f"Error rendering template with dummy data: {e}")

# Upload CSV
uploaded_file = st.file_uploader("Upload Employee CSV", type=["csv"])

if uploaded_file and template_file:

    df = pd.read_csv(uploaded_file).fillna('')
    # df.drop_duplicates(subset=['email'], keep='first', inplace=True)
    # Add status and timestamp columns if they don't exist
    if "status" not in df.columns:
        df["status"] = ""
    if "timestamp" not in df.columns:
        df["timestamp"] = ""

    st.write("### Preview of Employee Data")

    # Placeholder for the DataFrame display (full df with scrollbar or updated during sending)
    preview_placeholder = st.empty()

    # Display the full DataFrame with a fixed height and scrollbar
    # Calculate height for 10 rows + header (approx 35px per row + 35px for header)
    dataframe_height = min(len(df), 10) * 35 + 35
    preview_placeholder.dataframe(df, height=dataframe_height)

    env = Environment(
        loader=None,  # We are loading from a string, so no file system loader needed
        autoescape=select_autoescape(['html', 'xml'])
    )
    env.filters['format_currency'] = format_currency

    template_file.seek(0)
    template_content = template_file.read().decode("utf-8")
    template_lines = template_content.split('\n')
    first_line = template_lines[0]

    if first_line.startswith("Subject:"):
        subject_template_str = first_line.replace("Subject:", "").strip()
        body_template_str = '\n'.join(template_lines[1:])
    else:
        subject_template_str = "Monthly Update - Medical Expenses Reimbursement"
        body_template_str = template_content

    template = env.from_string(body_template_str)
    subject_template = env.from_string(subject_template_str)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Send Emails"):
            st.info("Connecting to Gmail... Please authorize once if prompted.")
            service = get_gmail_service()
            sender = "me"  # Gmail API will use your logged-in account

            progress = st.progress(0)
            local_timezone = pytz.timezone("Asia/Karachi")

            df = send_emails(df, df.index.tolist(), template, service, sender, local_timezone, progress,
                             preview_placeholder, subject_template)
            df.to_csv(uploaded_file.name, index=False)
            st.success("🎉 All emails processed!")
            preview_placeholder.dataframe(df)

    with col2:
        if df["status"].str.contains("failed").any():
            if st.button("Retry Failed Emails"):
                st.info("Retrying failed emails...")
                service = get_gmail_service()
                sender = "me"

                failed_df = df[df["status"].str.contains("failed", na=False)]
                progress = st.progress(0)
                local_timezone = pytz.timezone("Asia/Karachi")

                df = send_emails(df, failed_df.index.tolist(), template, service, sender, local_timezone, progress,
                                 preview_placeholder, subject_template)
                df.to_csv(uploaded_file.name, index=False)
                st.success("🎉 Retried all failed emails!")
                preview_placeholder.dataframe(df)
