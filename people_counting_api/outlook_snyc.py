# pip install O365
from O365 import Account, FileSystemTokenBackend
import psycopg2

# Test credentials (client_id and client_secret from Azure app registration)
credentials = (
    "74658136-14ec-4630-ad9b-26e160ff0fc6",  # client_id
    "vM9Q~SyoLpK3xbEoS3Cw5j1LYu18jR6IXx0hdcbO"  # client_secret
)

# Token storage backend (for reusing access tokens)
token_backend = FileSystemTokenBackend(token_path='.', token_filename='o365_token.txt')

# Create an O365 account instance (will open browser for first-time authentication)
account = Account(credentials, token_backend=token_backend)

# First-time authentication (browser-based)
if not account.is_authenticated:
    account.authenticate(scopes=['basic', 'calendar_all'])

# Access the calendar service
schedule = account.schedule()
calendar = schedule.get_default_calendar()

# Fetch today's events from the calendar
from datetime import datetime, timedelta
now = datetime.now()
events = calendar.get_events(start=now, end=now + timedelta(days=1))

# Connect to PostgreSQL database
conn = psycopg2.connect(
    dbname="smart_tour",
    user="postgres",
    password="your-password",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Parse and insert events into visitor_schedule table
for event in events:
    subject = event.subject
    start_time = event.start
    end_time = event.end
    body = event.body_preview

    print(f"📅 Event: {subject}, Time: {start_time} ~ {end_time}")

    # Extract visitor information from the event (can be customized)
    visitor_name = subject or "Unknown"
    company = "TBD"
    tour_lead = "TBD"

    # Insert into visitor_schedule table
    cursor.execute("""
        INSERT INTO visitor_schedule (visitor_name, company, visit_start, visit_end, tour_lead)
        VALUES (%s, %s, %s, %s, %s)
    """, (visitor_name, company, start_time, end_time, tour_lead))

conn.commit()
conn.close()
