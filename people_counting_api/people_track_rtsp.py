import cv2
import os
import time
import requests
import numpy as np
from ultralytics import YOLO
from yolox.tracker.byte_tracker import BYTETracker

# ==== RTSP stream address ====
rtsp_url = "rtsp://admin:admin@10.100.124.17/defaultPrimary?streamType=u"
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

# ==== Initialize YOLOv8 model and ByteTrack tracker ====
model = YOLO("yolov8n.pt")

class TrackerArgs:
    track_thresh = 0.5
    track_buffer = 90
    match_thresh = 0.8
    aspect_ratio_thresh = 1.6
    min_box_area = 10
    mot20 = False
    frame_rate = 30

tracker = BYTETracker(TrackerArgs())

# ==== Crossing line parameters ====
line_y = 1250
line_x1 = 1000
line_x2 = 1500

# ==== Tracking state variables ====
id_last_y = {}
entered_ids = set()
left_ids = set()
id_cooldown = {}
cooldown_seconds = 5

# ==== Group status ====
group_current_count = 0
group_total_count = 0
last_enter_time = time.time()

# ==== Finite State Machine ====
state = "WAITING"

# ==== Warning control ====
last_warning_time = 0
warning_cooldown = 10  # in seconds

# ==== Start RTSP video stream ====
cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
cv2.namedWindow("RTSP Group Tracker", cv2.WINDOW_NORMAL)

print("🚀 Starting real-time group tracking from RTSP... Press Q to quit.")

def post_group_status(current, total, status):
    try:
        requests.post("http://localhost:5000/update_group_status", json={
            "current_count": current,
            "total_count": total,
            "status": status
        })
    except Exception as e:
        print(f"⚠️ Failed to connect to Flask server: {e}")

def send_warning(current_count):
    global last_warning_time
    now = time.time()

    if now - last_warning_time >= warning_cooldown:
        try:
            response = requests.post("http://localhost:6000/warning", json={
                "current_count": current_count,
                "status": "WARNING",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            if response.status_code == 200:
                print(f"🚨 Warning sent! Current count: {current_count}")
            else:
                print(f"⚠️ Warning failed, status code: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Warning request failed: {e}")
        last_warning_time = now

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Failed to read RTSP frame. Retrying...")
        time.sleep(0.5)
        continue

    results = model(frame, classes=[0], verbose=False)[0]
    dets = []
    for box in results.boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        conf = float(box.conf[0])
        dets.append([x1, y1, x2, y2, conf])

    if dets:
        dets_np = np.array(dets).reshape(-1, 5)
        online_targets = tracker.update(dets_np, frame.shape, frame.shape)
    else:
        online_targets = []

    now = time.time()
    current_detected_ids = set()

    for t in online_targets:
        tid = t.track_id
        x1, y1, w, h = t.tlwh
        x2, y2 = x1 + w, y1 + h
        cx, cy = int(x1 + w / 2), int(y1 + h / 2)

        current_detected_ids.add(tid)

        if line_x1 <= cx <= line_x2:
            if tid in id_cooldown and now - id_cooldown[tid] < cooldown_seconds:
                continue
            if tid in id_last_y:
                last_y = id_last_y[tid]

                if last_y < line_y and cy >= line_y and tid not in entered_ids:
                    entered_ids.add(tid)
                    group_current_count += 1
                    last_enter_time = now
                    id_cooldown[tid] = now
                    print(f"🟢 ID {tid} entered | Current count: {group_current_count}")

                elif last_y > line_y and cy <= line_y and tid not in left_ids:
                    left_ids.add(tid)
                    group_current_count = max(group_current_count - 1, 0)
                    id_cooldown[tid] = now
                    print(f"🔴 ID {tid} left | Current count: {group_current_count}")

        id_last_y[tid] = cy

        # Draw bounding box and ID
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(frame, f"ID {tid}", (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # ==== Trigger warning if group size exceeds threshold ====
    if group_current_count > 22:
        send_warning(group_current_count)

    # ==== Finite State Machine ====
    if state == "WAITING":
        if current_detected_ids:
            print("🟠 People detected. Switching to DETECTING.")
            state = "DETECTING"
            last_enter_time = now
            post_group_status(0, 0, "DETECTING")

    elif state == "DETECTING":
        if group_current_count > 0:
            print("🟡 Confirmed group entered. Switching to PROCESSING_ENTERING.")
            group_total_count = group_current_count
            state = "PROCESSING_ENTERING"
            post_group_status(group_current_count, group_total_count, "ENTERING")
        elif now - last_enter_time > 5:
            print("🟣 Timeout. Switching back to WAITING.")
            state = "WAITING"
            post_group_status(0, 0, "WAITING")

    elif state == "PROCESSING_ENTERING":
        if group_current_count < group_total_count:
            print("🔵 Group is leaving. Switching to PROCESSING_LEAVING.")
            state = "PROCESSING_LEAVING"
            post_group_status(group_current_count, group_total_count, "LEAVING")

    elif state == "PROCESSING_LEAVING":
        if group_current_count == 0:
            print("✅ All left. Switching to FINISHED.")
            state = "FINISHED"
            post_group_status(0, 0, "FINISHED")

    elif state == "FINISHED":
        time.sleep(1)
        group_current_count = 0
        group_total_count = 0
        entered_ids.clear()
        left_ids.clear()
        id_last_y.clear()
        id_cooldown.clear()
        print("🔄 System reset. Switching to WAITING.")
        post_group_status(0, 0, "WAITING")
        state = "WAITING"

    # ==== Visualization ====
    cv2.line(frame, (line_x1, line_y), (line_x2, line_y), (0, 0, 255), 3)
    cv2.putText(frame, "Cross Line", (line_x1, line_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.putText(frame, f"Now: {group_current_count} / Total: {group_total_count}", (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 3)

    cv2.putText(frame, f"State: {state}", (30, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)

    cv2.imshow("RTSP Group Tracker", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
