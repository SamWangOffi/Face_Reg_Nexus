
# FACE_REG_NEXUS

A modular visitor detection and tracking system built using YOLOv8 and ByteTrack. It includes real-time people counting via RTSP stream, finite state machine logic, warning alert logging, group tracking state management, and Outlook Calendar integration with PostgreSQL.

---

## 📁 Project Structure

```text
FACE_REG_NEXUS/
├── README.md                # Project documentation and usage guide
├── requirements.txt         # Python dependencies
├── people_counting_api/     # People tracking and calendar sync module
│   ├── people_track_rtsp.py     # RTSP-based YOLOv8 + ByteTrack tracker with FSM logic
│   ├── smart_tour_server.py     # Flask server to expose group status + init DB
│   ├── outlook_sync.py          # Sync visitor schedule from Outlook Calendar to PostgreSQL
│   └── yolov8n.pt               # YOLOv8 model weights
├── people_warning_api/      # Warning alert server module
│   └── server_warning.py        # Flask API to receive and log warning signals
```

---

##  Requirements

- Python 3.8+
- PostgreSQL (running locally or remotely)
- RTSP-compatible IP camera or stream
- YOLOv8 model file (`yolov8n.pt`) — [Download from Ultralytics](https://github.com/ultralytics/ultralytics)
- Outlook API credentials (if using `outlook_sync.py`)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Make sure `flask` CLI is installed:

```bash
pip install flask
```

---

##  Running the System

### 1. Initialize the PostgreSQL Database

```bash
cd people_counting_api
flask --app smart_tour_server.py init-db
```

### 2. Start the Group Tracking Server

```bash
python smart_tour_server.py
```

### 3. Start RTSP People Detection & Tracking

```bash
python people_track_rtsp.py
```

### 4. Start the Warning Receiver API (in another terminal)

```bash
cd ../people_warning_api
python server_warning.py
```

### 5. (Optional) Sync Outlook Calendar Schedule

```bash
python outlook_sync.py
```

---

##  API Endpoints Overview

| Endpoint               | Method | Description                             |
|------------------------|--------|-----------------------------------------|
| `/group_status`        | GET    | Returns current group state             |
| `/update_group_status` | POST   | Updates and logs group state            |
| `/warning`             | POST   | Receives warning alerts                 |
| `/warning`             | GET    | Verifies that the API is running        |
| `/warnings`            | GET    | Lists the 10 most recent warnings       |

---

##  Finite State Machine (FSM)

The system uses an FSM to manage group tracking logic:

**WAITING → DETECTING → ENTERING → ENTERED → LEAVING → FINISHED**


---

##  Database Schema Overview

This system uses a PostgreSQL database to store visitor tracking, facial recognition, group activity, and warning logs.

### Tables Overview

#### 1. `face_encoding`  
*Stores pre-encoded facial vectors of known visitors for future recognition.*

| Column Name | Type      | Description                          |
|-------------|-----------|--------------------------------------|
| id          | SERIAL    | Primary key                          |
| name        | VARCHAR   | Visitor’s name                       |
| encoding    | FLOAT8[]  | 128-dimensional face encoding vector |
| created_at  | TIMESTAMP | Record creation timestamp            |

#### 2. `group_status_log`  
*Logs real-time group size and tracking state.*

| Column Name   | Type      | Description                         |
|---------------|-----------|-------------------------------------|
| id            | SERIAL    | Primary key                         |
| current_count | INTEGER   | Current number of people detected   |
| total_count   | INTEGER   | Total people in the group           |
| status        | VARCHAR   | Group tracking status (FSM state)   |
| timestamp     | TIMESTAMP | Record creation timestamp           |

#### 3. `visitor_event_log`  
*Records recognized visitors based on face encoding.*

| Column Name              | Type      | Description                                 |
|--------------------------|-----------|---------------------------------------------|
| id                       | SERIAL    | Primary key                                 |
| visitor_name             | VARCHAR   | Visitor’s name (from recognition)           |
| matched_from_encoding_id | INTEGER   | Foreign key referencing `face_encoding.id`  |
| detected_time            | TIMESTAMP | When the visitor was detected               |

#### 4. `visitor_schedule`  
*Stores expected visit schedules synced from Outlook.*

| Column Name  | Type      | Description                       |
|--------------|-----------|-----------------------------------|
| id           | SERIAL    | Primary key                       |
| visitor_name | VARCHAR   | Visitor’s full name               |
| company      | VARCHAR   | Company or organization name      |
| visit_start  | TIMESTAMP | Scheduled visit start time        |
| visit_end    | TIMESTAMP | Scheduled visit end time          |
| tour_lead    | VARCHAR   | Tour lead name or identifier      |

#### 5. `warning_log`  
*Logs warning signals triggered when occupancy exceeds threshold.*

| Column Name   | Type      | Description                         |
|---------------|-----------|-------------------------------------|
| id            | SERIAL    | Primary key                         |
| current_count | INTEGER   | Number of people when warning sent  |
| status        | VARCHAR   | Always "WARNING" for now            |
| timestamp     | TIMESTAMP | Time the warning was triggered      |
| company       | VARCHAR   | Visitor company (if available)      |

---

