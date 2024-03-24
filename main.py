from __future__ import print_function
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import email

from nomic import atlas
from aiconfig import AIConfigRuntime, InferenceOptions
import asyncio
import re
import json
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tqdm import tqdm
from datetime import datetime
import pytz
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from datetime import datetime
import pytz

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import email

# If modifying these SCOPES, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def remove_text_in_quotes(input_string):
    """
    Removes text within angle brackets, including the brackets themselves.

    Parameters:
    input_string (str): The string containing text within angle brackets.

    Returns:
    str: The string with text within angle brackets removed.
    """
    # Remove text within angle brackets
    cleaned_str = re.sub(r"<[^>]*>", "", input_string)
    # Remove double quotes
    cleaned_str = re.sub(r"\"", "", cleaned_str)
    return cleaned_str.strip()


def get_emails():
    email_details = get_email_details_from_senders_cached()
    email_details = clean_emails_helper(email_details)
    for mail in email_details:
        # email["id"] = time.time() + random.randint(0, 1000)
        mail["name"] = remove_text_in_quotes(mail["sender_name"])
        # mail["summaries"] = {
        #     "tldr": "TLDR",
        #     "points": "Points",
        # }
        mail["themes"] = [
            "Theme 1",
            "Theme 2",
            "Theme 3",
            "Theme 4",
            "Theme 5",
        ]
    return email_details


def get_gmail_service():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def parse_to_iso_format_extended(date_str):
    """
    Parses a date string that may include extra content, formatted as
    'Day, DD Mon YYYY HH:MM:SS ±HHMM (TZ)', and returns an ISO 8601 format
    date string. It is more flexible with input variations.

    Parameters:
    date_str (str): The date string, potentially including extra content.

    Returns:
    str: The date in ISO 8601 format.
    """
    # Attempt to parse the date string ignoring potential trailing content
    try:
        # Directly parsing without considering extra content like (UTC)
        parsed_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        # Attempt to parse by ignoring anything after the timezone offset
        parsed_date = datetime.strptime(date_str[:-6], "%a, %d %b %Y %H:%M:%S %z")

    # Convert to UTC (optional)
    utc_date = parsed_date.astimezone(pytz.utc)

    # Format as ISO 8601
    iso_format_date = utc_date.strftime("%Y-%m-%dT%H:%M:%S")

    return iso_format_date


def format_date(iso_date_str):
    """
    Parses an ISO 8601 format date string and returns a string formatted as
    'Day, DD Mon YYYY HH:MM:SS ±HHMM'.

    Parameters:
    iso_date_str (str): The ISO 8601 format date string.

    Returns:
    str: The formatted date string.
    """
    # Parse the ISO 8601 date string
    parsed_date = datetime.fromisoformat(iso_date_str)

    # Convert to UTC and format
    utc_date = parsed_date.astimezone(pytz.utc)
    formatted_date = utc_date.strftime("%a, %d %b %Y %H:%M:%S %z")

    return formatted_date


def get_header_value(headers, name):
    """Helper function to retrieve value from the email headers"""
    for header in headers:
        if header["name"] == name:
            return header["value"]
    return None


def get_email_details_from_senders(sender_emails):
    """
    Retrieves details including the subject, body, and a link to the email
    for all emails sent from a list of predefined senders.

    Parameters:
    sender_emails (list): A list of sender email addresses.

    Returns:
    list: A list of dictionaries with details for each email.
    """
    service = get_gmail_service()
    emails_details = []

    for sender in tqdm(sender_emails):
        tqdm.write(f"Fetching emails from {sender}")
        query = f"from:{sender}"
        response = service.users().messages().list(userId="me", q=query).execute()

        if "messages" in response:
            for message in tqdm(response["messages"]):
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message["id"], format="full")
                    .execute()
                )

                headers = msg["payload"]["headers"]
                subject = next(
                    header["value"] for header in headers if header["name"] == "Subject"
                )
                from_header = get_header_value(headers, "From")
                date_sent = get_header_value(headers, "Date")
                read_status = "UNREAD" not in msg["labelIds"]

                email_details = {
                    "id": msg["id"],
                    "sender": sender,
                    "name": from_header,
                    "subject": subject,
                    "date": parse_to_iso_format_extended(date_sent),
                    "read": read_status,
                    "link": f"https://mail.google.com/mail/u/2/#inbox/{message['id']}",
                    "body": get_email_body(message["id"], service),
                    "labels": ["meeting", "work", "important"],
                }
                emails_details.append(email_details)

        # TODO - Pagination handling
        # while "nextPageToken" in response:
        #     page_token = response["nextPageToken"]
        #     response = (
        #         service.users()
        #         .messages()
        #         .list(userId="me", q=query, pageToken=page_token)
        #         .execute()
        #     )

        #     if "messages" in response:
        #         for message in response["messages"]:
        #             msg = (
        #                 service.users()
        #                 .messages()
        #                 .get(userId="me", id=message["id"], format="full")
        #                 .execute()
        #             )
        #             # Similar data extraction and pagination process as above
        #             ...

    return emails_details


def get_email_body(email_id, service):
    msg = (
        service.users().messages().get(userId="me", id=email_id, format="raw").execute()
    )

    # Decode the email body
    msg_raw = base64.urlsafe_b64decode(msg["raw"].encode("ASCII"))
    msg_str = email.message_from_bytes(msg_raw)

    if msg_str.is_multipart():
        for part in msg_str.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                return body
                break
    else:
        body = msg_str.get_payload(decode=True).decode()
        return body


def get_email_details_from_senders_cached(emails_info=[]):
    with open("./emails_details_summaries.json") as f:
        email_details = json.load(f)
        return email_details


def remove_html_tags(input_string):
    """
    Removes HTML tags from a string.

    Parameters:
    input_string (str): The string containing HTML tags.

    Returns:
    str: The string with HTML tags removed.
    """
    # Regular expression for finding HTML tags
    tag_re = re.compile(r"<[^>]+>")

    # Use re.sub() to replace HTML tags with an empty string
    return tag_re.sub("", input_string)


def get_summaries():
    config = AIConfigRuntime.load("./newsletter.aiconfig.yaml")
    inference_options = InferenceOptions(stream=True)
    mails = get_emails()

    async def get_themes(body):
        themes = await config.run(
            "get_themes",
            options=inference_options,
            params={"email": body},
        )
        themes = [0].data

    async def get_summaries(body):
        summarised_points = await config.run(
            "prompt_get_bullet_points",
            options=inference_options,
            params={"email": body},
        )
        summarised_tldr = await config.run(
            "prompt_get_tldr",
            options=inference_options,
            params={"email": body},
        )
        return {"points": summarised_points[0].data, "tldr": summarised_tldr[0].data}

    async def populate_with_summaries(mails):
        final_emails = []
        for mail in tqdm(mails):
            try:
                m = mail
                print(mail["body"])
                labels = input().split(",")
                m["themes"] = labels

                # summaries = await get_themes(mail["body"])
                final_emails.append(m)
            except Exception as e:
                print(e)
                continue
        try:
            with open("emails_details_summaries_themes.json", "w") as f:
                json.dump(final_emails, f)
        except Exception:
            import ipdb

            ipdb.set_trace()

    asyncio.run(populate_with_summaries(mails))


def clean_email_body(body):
    body = remove_html_tags(body)
    return body


def clean_emails_helper(email_details):
    cleaned_email_details = []
    for email_detail in email_details:
        if email_detail["body"] is not None:
            email_detail["body"] = clean_email_body(email_detail["body"])
            cleaned_email_details.append(email_detail)
    return email_details


if __name__ == "__main__":
    get_summaries()
    # email_details = get_email_details_from_senders(
    #     [
    #         "alex@sunsama.com",
    #         "weaviate@mail.beehiiv.com",
    #         "notboring@substack.com",
    #         "abundantia@substack.com",
    #         "crew@morningbrew.com",
    #     ]
    # )

    # email_details = clean_emails_helper(email_details)
    # with open("emails_details_more.json", "w") as f:
    #     json.dump(email_details, f)
    # atlas.map_data(email_details, identifier="Newsletters", indexed_field="body")
