import cv2
import face_recognition
import pickle
import os
import numpy as np
import pandas as pd
import smtplib
import threading
import base64
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, Response, jsonify, request, redirect, url_for
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import unicodedata

app = Flask(__name__)

ENCODINGS_FILE = "encodings.pickle"
REPORT_DIR = "attendance_reports"

SENDER_EMAIL = "luuhaan204@gmail.com"
APP_PASSWORD = "myvq xuik svqz sike"

TIMETABLE = {
    "Ca Sáng (07:20 - 12:00)": ("07:20", "12:00"),
    "Ca Chiều (13:05 - 17:45)": ("13:05", "17:45")
}

ADMIN_USER = "admin@gmail.com"
ADMIN_PASS = "12345a"
REGISTER_SAMPLE_COUNT = 5

os.makedirs(REPORT_DIR, exist_ok=True)

current_shift_name = None
current_start_dt = None
current_end_dt = None
attendance_records = {}
last_message = ""
sound_trigger = False
camera_running = False


def is_valid_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)


def student_exists(student_id):
    data = load_face_data()
    return any(sv["id"] == student_id for sv in data["info"])


def save_student_encodings(student_id, name, email, images_base64):
    data = load_face_data()

    new_encodings = []
    new_info = []

    for img_base64 in images_base64:
        img_data = img_base64.split(",")[1]
        img_bytes = base64.b64decode(img_data)

        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        face_locations = face_recognition.face_locations(rgb)

        if len(face_locations) != 1:
            return False, "Mỗi ảnh phải có đúng 1 khuôn mặt."

        encoding = face_recognition.face_encodings(rgb, face_locations)[0]

        new_encodings.append(encoding)
        new_info.append({
            "id": student_id,
            "name": name,
            "email": email
        })

    data["encodings"].extend(new_encodings)
    data["info"].extend(new_info)

    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)

    return True, "Đăng ký khuôn mặt thành công."


def remove_vietnamese_accents(text):
    text = text.replace("đ", "d")
    text = text.replace("Đ", "D")

    text = unicodedata.normalize("NFD", text)
    text = ''.join(
        c for c in text
        if unicodedata.category(c) != 'Mn'
    )

    return text

def load_face_data():
    if not os.path.exists(ENCODINGS_FILE):
        return {"encodings": [], "info": []}

    with open(ENCODINGS_FILE, "rb") as f:
        return pickle.load(f)


def send_email_to_student(receiver_email, student_name, student_id, class_start_time, checkin_time):
    try:
        time_str = checkin_time.strftime("%H:%M:%S")
        delay = (checkin_time - class_start_time).total_seconds() / 60

        if delay <= 0:
            status = "Đúng giờ"
            subject = f"Xác nhận điểm danh - Sinh viên {student_name}"
            body = f"""Chào {student_name},

Hệ thống ghi nhận bạn điểm danh thành công!
- Mã SV: {student_id}
- Thời gian: {time_str}
- Trạng thái: {status}

Chúc bạn học tập hiệu quả."""
        else:
            delay_mins = int(delay)
            status = f"Đi muộn {delay_mins} phút"
            subject = f"[CẢNH BÁO] Điểm danh muộn - Sinh viên {student_name}"
            body = f"""Chào {student_name},

Hệ thống ghi nhận bạn đã điểm danh.
- Mã SV: {student_id}
- Thời gian: {time_str}
- Trạng thái: {status}

Bạn đã đi học muộn {delay_mins} phút so với giờ quy định.

Trân trọng."""

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()

        print(f"[MAIL] Đã gửi cho {student_id}")

    except Exception as e:
        print("[MAIL ERROR]", e)


def get_status(checkin_time):
    delay = (checkin_time - current_start_dt).total_seconds() / 60

    if delay <= 0:
        return "Có mặt", "Đúng giờ"

    return "Đi muộn", f"Muộn {int(delay)} phút"


def generate_frames():
    global attendance_records, last_message, sound_trigger, camera_running

    data = load_face_data()
    known_encodings = data["encodings"]
    known_info = data["info"]

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("[CAMERA ERROR] Không mở được webcam")
        return

    camera_running = True

    while camera_running:
        success, frame = cap.read()
        if not success:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = np.ascontiguousarray(small_frame[:, :, ::-1])

        face_locations = face_recognition.face_locations(rgb_small)
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            top, right, bottom, left = [v * 4 for v in face_location]

            name = "Khách lạ"
            student_id = "N/A"
            color = (0, 0, 255)

            if len(known_encodings) > 0:
                distances = face_recognition.face_distance(known_encodings, face_encoding)
                best_index = np.argmin(distances)

                if distances[best_index] < 0.5:
                    info = known_info[best_index]
                    student_id = info["id"]
                    name = info["name"]
                    email = info["email"]
                    color = (0, 255, 0)

                    if student_id not in attendance_records:
                        checkin_time = datetime.now()
                        status, note = get_status(checkin_time)

                        attendance_records[student_id] = {
                            "id": student_id,
                            "name": name,
                            "email": email,
                            "time": checkin_time.strftime("%H:%M:%S"),
                            "status": status,
                            "note": note
                        }

                        last_message = f"{name} đã điểm danh thành công!"
                        sound_trigger = True

                        threading.Thread(
                            target=send_email_to_student,
                            args=(email, name, student_id, current_start_dt, checkin_time),
                            daemon=True
                        ).start()
                    else:
                        last_message = f"{name} đã điểm danh rồi!"

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            display_name = remove_vietnamese_accents(name)
            cv2.putText(
                frame,
                f"{display_name} ({student_id})",
                (left + 6, bottom - 8),
                cv2.FONT_HERSHEY_DUPLEX,
                0.6,
                (255, 255, 255),
                1
            )

        cv2.putText(
            frame,
            remove_vietnamese_accents(last_message),
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )

    cap.release()
    
@app.route("/motcua/check", methods=["POST"])
def motcua_check():
    admin_email = request.form.get("admin_email", "").strip()
    admin_password = request.form.get("admin_password", "").strip()

    if admin_email == ADMIN_USER and admin_password == ADMIN_PASS:
        return jsonify({
            "success": True,
            "message": "Xác thực admin thành công."
        })

    return jsonify({
        "success": False,
        "message": "Sai tài khoản hoặc mật khẩu admin."
    })

@app.route("/motcua", methods=["GET", "POST"])
def motcua():
    if request.method == "GET":
        return render_template("admin_register.html")

    admin_email = request.form.get("admin_email", "").strip()
    admin_password = request.form.get("admin_password", "").strip()

    student_id = request.form.get("student_id", "").strip()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    images = request.form.getlist("images[]")

    if admin_email != ADMIN_USER or admin_password != ADMIN_PASS:
        return jsonify({
            "success": False,
            "message": "Sai tài khoản admin."
        })

    if not student_id or not name or not email:
        return jsonify({
            "success": False,
            "message": "Vui lòng nhập đầy đủ thông tin sinh viên."
        })

    if not is_valid_email(email):
        return jsonify({
            "success": False,
            "message": "Email sinh viên không hợp lệ."
        })

    if student_exists(student_id):
        return jsonify({
            "success": False,
            "message": "Mã sinh viên đã tồn tại."
        })

    if len(images) < REGISTER_SAMPLE_COUNT:
        return jsonify({
            "success": False,
            "message": f"Cần chụp đủ {REGISTER_SAMPLE_COUNT} ảnh."
        })

    success, message = save_student_encodings(student_id, name, email, images)

    return jsonify({
        "success": success,
        "message": message
    })

@app.route("/")
def index():
    message = request.args.get("message")
    return render_template("index.html", shifts=TIMETABLE.keys(), message=message)


@app.route("/start", methods=["POST"])
def start_attendance():
    global current_shift_name, current_start_dt, current_end_dt
    global attendance_records, last_message

    selected = request.form.get("shift")
    start_str, end_str = TIMETABLE[selected]

    now = datetime.now()

    h_s, m_s = map(int, start_str.split(":"))
    h_e, m_e = map(int, end_str.split(":"))

    start_dt = now.replace(hour=h_s, minute=m_s, second=0, microsecond=0)
    end_dt = now.replace(hour=h_e, minute=m_e, second=0, microsecond=0)

    # Tạm thời bỏ kiểm tra thời gian để test
    current_shift_name = selected
    current_start_dt = start_dt
    current_end_dt = end_dt

    attendance_records = {}
    last_message = "Camera đang hoạt động..."

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", shift=current_shift_name)


@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/attendance_data")
def attendance_data():
    data = load_face_data()
    total_students = len(data["info"])
    present = len(attendance_records)

    late = sum(1 for r in attendance_records.values() if r["status"] == "Đi muộn")
    on_time = sum(1 for r in attendance_records.values() if r["status"] == "Có mặt")
    absent = total_students - present

    return jsonify({
        "records": list(attendance_records.values()),
        "message": last_message,
        "total": total_students,
        "present": present,
        "on_time": on_time,
        "late": late,
        "absent": absent
    })


@app.route("/sound_status")
def sound_status():
    global sound_trigger

    if sound_trigger:
        sound_trigger = False
        return jsonify({"play": True})

    return jsonify({"play": False})


@app.route("/stop")
def stop_camera():
    global camera_running
    camera_running = False
    return redirect(url_for("index"))


@app.route("/report")
def export_report():
    data = load_face_data()
    all_students = data["info"]

    report_data = []

    for sv in all_students:
        student_id = sv["id"]
        name = sv["name"]

        if student_id in attendance_records:
            record = attendance_records[student_id]
            time_str = record["time"]
            status = record["status"]
            note = record["note"]
        else:
            time_str = ""
            status = "Nghỉ học"
            note = ""

        report_data.append({
            "Mã SV": student_id,
            "Họ tên": name,
            "Thời gian quét": time_str,
            "Trạng thái": status,
            "Ghi chú": note
        })

    df = pd.DataFrame(report_data)
    filename = f"BaoCao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(REPORT_DIR, filename)
    df.to_excel(filepath, index=False)

    send_report_to_teacher(filepath)

    return f"Đã xuất báo cáo và gửi email: {filename}"


def send_report_to_teacher(filepath):
    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"Báo cáo điểm danh - {current_shift_name}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = SENDER_EMAIL

        msg.attach(MIMEText("File báo cáo điểm danh được đính kèm.", "plain", "utf-8"))

        with open(filepath, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(filepath)}"
        )
        msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, SENDER_EMAIL, msg.as_string())
        server.quit()

    except Exception as e:
        print("[REPORT MAIL ERROR]", e)


if __name__ == "__main__":
    app.run(debug=True)