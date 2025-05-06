# FACE_REG_NEXUS

This project is a visitor detection and tracking system using YOLOv8 and ByteTrack, with features for people counting, group status tracking, warning alerts, and Outlook Calendar integration.

## Project Structure

```
\FACE_REG_NEXUS/
├── init_db.py                  # One-click script to initialize all PostgreSQL tables
├── README.md                   # Project description and instructions
├── requirements.txt            # Python dependencies
├── people_counting_api/        # Module for detection, tracking, and calendar syncing
│   ├── __pycache__/
│   ├── outlook_sync.py         # Sync visitor schedule from Outlook Calendar to PostgreSQL
│   ├── people_track_rtsp.py    # Run real-time people detection and tracking from RTSP stream
│   ├── server.py               # Flask API to store and expose group tracking status
│   └── yolov8n.pt              # YOLOv8 model weight file
├── people_warning_api/         # Module for warning alert server
│   └── server_warning.py       # Flask API to receive and log warning signals
```

## Requirements

Ensure the following:

- Python 3.8+
- PostgreSQL running and configured
- YOLOv8 model file (`yolov8n.pt`)
- RTSP-compatible camera or stream
- Outlook Calendar API credentials (if using `outlook_sync.py`)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Running Each Component

**1. Initialize the local database:**

```bash
cd people_counting_api
python init_db.py
```

**2. Start the group tracking server:**

```bash
python server.py
```

**3. Start the RTSP-based people tracking:**

```bash
python people_track_rtsp.py
```

**4. Start the warning alert receiver (in a separate terminal):**

```bash
cd ../people_warning_api
python server_warning.py
```

**5. (Optional) Sync calendar schedule to PostgreSQL:**

```bash
python outlook_sync.py
```
