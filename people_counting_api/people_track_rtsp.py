import cv2
import os
import time
import numpy as np
import requests
from ultralytics import YOLO
from yolox.tracker.byte_tracker import BYTETracker

# ==== RTSP stream address ====
rtsp_url = "rtsp://admin:admin@10.100.124.17/defaultPrimary?streamType=u"
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

# ==== Load YOLOv8 model ====
model = YOLO("yolov8n.pt").to("cuda")

# ==== Initialize ByteTrack arguments ====
class TrackerArgs:
    track_thresh = 0.5
    track_buffer = 30
    match_thresh = 0.8
    aspect_ratio_thresh = 1.6
    min_box_area = 10
    mot20 = False
    frame_rate = 15

tracker = BYTETracker(TrackerArgs())

# ==== Horizontal line position ====
line_y = 800
line_x1, line_x2 = 600, 1500

# ==== Tracking and counting states ====
id_last_y = {}
entered_ids = set()
cooldown = {}
cooldown_seconds = 2

group_current_count = 0
group_total_count = 0
last_enter_time = time.time()
last_detection_time = time.time()

# ==== Initial state ====
state = "WAITING"

# ==== Warning control ====
last_warning_time = 0
warning_cooldown = 10  # seconds

# ==== Open RTSP stream ====
cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
cv2.namedWindow("Group Counter", cv2.WINDOW_NORMAL)

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Failed to read frame.")
        time.sleep(0.3)
        continue

    now = time.time()
    results = model(frame, classes=[0], verbose=False)[0]

    dets = []
    for box in results.boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        conf = float(box.conf[0])
        dets.append([x1, y1, x2, y2, conf])

    online_targets = tracker.update(np.array(dets), frame.shape, frame.shape) if dets else []
    current_detected_ids = set()

    for t in online_targets:
        tid = t.track_id
        x1, y1, w, h = t.tlwh
        x2, y2 = x1 + w, y1 + h
        cx, cy = int(x1 + w / 2), int(y1 + h / 2)

        if not (line_x1 <= cx <= line_x2):
            continue

        if tid in cooldown and now - cooldown[tid] < cooldown_seconds:
            continue

        if tid in id_last_y:
            last_y = id_last_y[tid]
            if last_y < line_y and cy >= line_y and tid not in entered_ids:
                entered_ids.add(tid)
                group_current_count += 1
                last_enter_time = now
                cooldown[tid] = now
                print(f"ID {tid} entered | Current count: {group_current_count}")

        id_last_y[tid] = cy
        current_detected_ids.add(tid)

        # Draw bounding box
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(frame, f"ID {tid}", (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # ==== Warning logic ====
    if group_current_count > 22 and now - last_warning_time > warning_cooldown:
        try:
            response = requests.post("http://localhost:6000/warning", json={
                "current_count": group_current_count,
                "status": "WARNING",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            if response.status_code == 200:
                print(f"Warning sent! Current count: {group_current_count}")
            last_warning_time = now
        except Exception as e:
            print(f"Failed to send warning: {e}")

    # ==== Finite State Machine ====
    if state == "WAITING":
        if current_detected_ids:
            print("DETECTING...")
            state = "DETECTING"
            last_enter_time = now

    elif state == "DETECTING":
        if group_current_count > 0:
            print("ENTERING...")
            state = "ENTERING"
        elif now - last_enter_time > 5:
            print("Returning to WAITING.")
            state = "WAITING"
            group_current_count = 0
            entered_ids.clear()
            id_last_y.clear()
            cooldown.clear()

    elif state == "ENTERING":
        if now - last_enter_time > 5:
            group_total_count = group_current_count
            print(f"ENTERED: Total = {group_total_count}")
            state = "ENTERED"

    elif state == "ENTERED":
        if group_current_count < group_total_count:
            print("LEAVING...")
            state = "LEAVING"

    elif state == "LEAVING":
        if not current_detected_ids and now - last_detection_time > 5:
            print("FINISHED. Resetting...")
            state = "FINISHED"

    elif state == "FINISHED":
        time.sleep(1)
        state = "WAITING"
        group_current_count = 0
        group_total_count = 0
        entered_ids.clear()
        id_last_y.clear()
        cooldown.clear()
        print("State reset to WAITING.")

    # Update last detection timestamp
    if current_detected_ids:
        last_detection_time = now

    # Visualization
    cv2.line(frame, (line_x1, line_y), (line_x2, line_y), (0, 0, 255), 3)
    cv2.putText(frame, f"Current: {group_current_count}", (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
    cv2.putText(frame, f"Total: {group_total_count}", (30, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)
    cv2.putText(frame, f"State: {state}", (30, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 100, 255), 2)

    cv2.imshow("Group Counter", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
