import cv2
import face_recognition
import pickle
import os
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import messagebox, ttk
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import threading
from datetime import datetime, timedelta

# ================= CẤU HÌNH HỆ THỐNG =================
ENCODINGS_FILE = "encodings.pickle"

SENDER_EMAIL = "luuhaan204@gmail.com" 
APP_PASSWORD = "myvq xuik svqz sike" 


# Tài khoản Admin (Giáo viên)
ADMIN_USER = "admin@gmail.com"
ADMIN_PASS = "12345a"

# Thời khóa biểu (giờ bắt đầu và kết thúc của từng ca/tiết học)
TIMETABLE = {
    "Ca Sáng (07:20 - 12:00)": ("07:20", "12:00"),
    "Ca Chiều (13:05 - 17:45)": ("13:05", "17:45")
}


def send_email_to_student(receiver_email, student_name, student_id, class_start_time, checkin_time):
    try:
        time_str = checkin_time.strftime("%H:%M:%S")
        delay = (checkin_time - class_start_time).total_seconds() / 60
        
        # Tách riêng nội dung Email dựa trên việc đi học muộn hay đúng giờ
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

⚠️ CẢNH BÁO: Bạn đã đi học muộn {delay_mins} phút so với giờ quy định! 
Đề nghị bạn chú ý đi học đúng giờ để đảm bảo tiến độ bài giảng và không bị trừ điểm chuyên cần.

Trân trọng."""
        
        # Khởi tạo và gửi email
        msg = MIMEText(body, "plain", "utf-8")
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        print(f"[MAIL] Đã gửi thông báo cho SV {student_id} ({status})")
    except Exception as e:
        print(f"[MAIL LỖI] Không thể gửi cho SV {student_id}: {e}")

# ================= GIAO DIỆN CHÍNH =================
class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ Thống Điểm Danh Trực Tuyến")
        self.root.geometry("650x450")
        
        # Biến lưu trữ dữ liệu điểm danh của ca hiện tại
        self.current_shift_name = ""
        self.current_start_dt = None
        self.attendance_records = {}
        
        tk.Label(root, text="HỆ THỐNG ĐIỂM DANH SINH VIÊN", font=("Arial", 18, "bold")).pack(pady=20)
        
        tk.Button(root, text="1. Đăng ký Khuôn mặt (Cần Admin)", font=("Arial", 12), bg="#ffb3b3", width=35, command=self.login_admin).pack(pady=10)
        tk.Button(root, text="2. Bắt đầu Điểm danh theo Ca", font=("Arial", 12), bg="lightgreen", width=35, command=self.open_shift_selector).pack(pady=10)
        tk.Button(root, text="3. Chốt sổ & Gửi file Báo cáo ngay", font=("Arial", 12), bg="#b3d9ff", width=35, command=self.manual_send_report).pack(pady=10)
        
        tk.Button(root, text="Thoát", font=("Arial", 11), width=15, command=root.quit).pack(pady=20)

    # ---------- MODULE 1: ĐĂNG NHẬP & ĐĂNG KÝ ----------
    def login_admin(self):
        login_win = tk.Toplevel(self.root)
        login_win.title("Xác thực Giáo viên")
        login_win.geometry("300x200")
        
        tk.Label(login_win, text="Email Giáo viên:").pack(pady=5)
        entry_user = tk.Entry(login_win, width=30)
        entry_user.pack()
        
        tk.Label(login_win, text="Mật khẩu:").pack(pady=5)
        entry_pass = tk.Entry(login_win, width=30, show="*")
        entry_pass.pack()
        
        def check_login():
            if entry_user.get() == ADMIN_USER and entry_pass.get() == ADMIN_PASS:
                messagebox.showinfo("Thành công", "Xác thực thành công!")
                login_win.destroy()
                self.open_register_window()
            else:
                messagebox.showerror("Lỗi", "Sai tài khoản hoặc mật khẩu!")
                
        tk.Button(login_win, text="Đăng nhập", command=check_login, bg="lightblue").pack(pady=15)

    def open_register_window(self):
        reg_win = tk.Toplevel(self.root)
        reg_win.title("Đăng ký sinh viên")
        reg_win.geometry("400x300")
        
        tk.Label(reg_win, text="Mã SV:").pack(pady=5)
        entry_id = tk.Entry(reg_win, width=30)
        entry_id.pack()
        tk.Label(reg_win, text="Họ Tên (Không dấu):").pack(pady=5)
        entry_name = tk.Entry(reg_win, width=30)
        entry_name.pack()
        tk.Label(reg_win, text="Email SV:").pack(pady=5)
        entry_email = tk.Entry(reg_win, width=30)
        entry_email.pack()
        
        def capture_and_save():
            s_id, s_name, s_email = entry_id.get().strip(), entry_name.get().strip(), entry_email.get().strip()
            if not s_id or not s_name or not s_email:
                messagebox.showerror("Lỗi", "Vui lòng nhập đủ thông tin!")
                return
                
            cap = cv2.VideoCapture(0)
            messagebox.showinfo("Hướng dẫn", "Nhấn OK, nhìn vào camera và bấm 'c' để chụp.")
            face_encoding_to_save = None
            
            while True:
                ret, frame = cap.read()
                if not ret: break
                cv2.imshow("Dang ky (Bam 'c' de chup, 'q' de huy)", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('c'):
                    rgb_frame = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    face_locations = face_recognition.face_locations(rgb_frame)
                    if len(face_locations) == 1:
                        face_encoding_to_save = face_recognition.face_encodings(rgb_frame, face_locations)[0]
                        break
                    else:
                        messagebox.showwarning("Cảnh báo", "Chỉ được có đúng 1 khuôn mặt!")
                elif key == ord('q'):
                    break
            cap.release()
            cv2.destroyAllWindows()
            
            if face_encoding_to_save is not None:
                data = {"encodings": [], "info": []}
                if os.path.exists(ENCODINGS_FILE):
                    with open(ENCODINGS_FILE, "rb") as f:
                        data = pickle.load(f)
                data["encodings"].append(face_encoding_to_save)
                data["info"].append({"id": s_id, "name": s_name, "email": s_email})
                with open(ENCODINGS_FILE, "wb") as f:
                    pickle.dump(data, f)
                messagebox.showinfo("Hoàn tất", f"Đã đăng ký: {s_name}")
                reg_win.destroy()

        tk.Button(reg_win, text="Mở Camera & Chụp", bg="yellow", command=capture_and_save).pack(pady=20)

    # ---------- MODULE 2: CHỌN CA & ĐIỂM DANH ----------
    def open_shift_selector(self):
        shift_win = tk.Toplevel(self.root)
        shift_win.title("Chọn Ca Học")
        shift_win.geometry("350x200")
        
        tk.Label(shift_win, text="Vui lòng chọn ca/tiết học hiện tại:", font=("Arial", 11)).pack(pady=15)
        
        shift_var = tk.StringVar()
        shift_combo = ttk.Combobox(shift_win, textvariable=shift_var, values=list(TIMETABLE.keys()), width=35, state="readonly")
        shift_combo.pack()
        if list(TIMETABLE.keys()):
            shift_combo.current(0)
            
        def validate_and_start():
            selected = shift_combo.get()
            start_str, end_str = TIMETABLE[selected]
            
            now = datetime.now()
            # Parse thời gian bắt đầu và kết thúc của ca học
            h_s, m_s = map(int, start_str.split(':'))
            h_e, m_e = map(int, end_str.split(':'))
            start_dt = now.replace(hour=h_s, minute=m_s, second=0, microsecond=0)
            end_dt = now.replace(hour=h_e, minute=m_e, second=0, microsecond=0)
            
            # RÀNG BUỘC THỜI GIAN: Chỉ cho phép điểm danh sớm tối đa 30 phút
            allowed_start_time = start_dt - timedelta(minutes=30)
            
            if now < allowed_start_time:
                messagebox.showerror("Chưa đến giờ", f"Ca học này bắt đầu lúc {start_str}.\nHệ thống chỉ mở điểm danh trước 30 phút (từ {allowed_start_time.strftime('%H:%M')}).")
                return
            if now > end_dt:
                messagebox.showerror("Đã hết giờ", f"Ca học này đã kết thúc lúc {end_str}. Không thể điểm danh!")
                return

            # Nếu hợp lệ, tiến hành reset records và mở camera
            self.current_shift_name = selected
            self.current_start_dt = start_dt
            self.attendance_records = {} # Reset danh sách điểm danh cho ca mới
            shift_win.destroy()
            self.run_attendance_camera()

        tk.Button(shift_win, text="Xác nhận & Mở Camera", bg="lightgreen", command=validate_and_start).pack(pady=20)

    def run_attendance_camera(self):
        try:
            with open(ENCODINGS_FILE, "rb") as f:
                data = pickle.load(f)
        except FileNotFoundError:
            messagebox.showerror("Lỗi", "Chưa có dữ liệu khuôn mặt!")
            return

        known_encodings, known_info = data["encodings"], data["info"]
        cap = cv2.VideoCapture(0)
        
        # Thiết lập thời gian bắt đầu
        open_time = datetime.now()
        delay_seconds = 15
        attendance_done = False # Biến cờ để đóng cam khi thành công
        
        print(f"[INFO] Đang chờ {delay_seconds}s trước khi bắt đầu điểm danh...")
        
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            now = datetime.now()
            elapsed_time = (now - open_time).total_seconds()
            remaining_time = int(delay_seconds - elapsed_time)

            # --- TRƯỜNG HỢP 1: ĐANG TRONG THỜI GIAN ĐỢI (DELAY) ---
            if elapsed_time < delay_seconds:
                # Vẽ lớp phủ mờ hoặc thông báo chờ
                cv2.putText(frame, f"He thong se quet sau: {remaining_time}s", (50, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                cv2.putText(frame, "Vui long dung vung truoc Camera", (50, 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            # --- TRƯỜNG HỢP 2: BẮT ĐẦU QUÉT MẶT ---
            else:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])
                
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                for face_encoding, face_location in zip(face_encodings, face_locations):
                    top, right, bottom, left = [c * 4 for c in face_location]
                    
                    if len(known_encodings) > 0:
                        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        
                        if face_distances[best_match_index] < 0.5:
                            info = known_info[best_match_index]
                            name, student_id, email = info["name"], info["id"], info["email"]
                            
                            # Vẽ khung xanh xác nhận
                            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                            cv2.putText(frame, "XAC NHAN THANH CONG!", (left, top - 10), 
                                        cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)
                            
                            # Điểm danh và gửi mail
                            checkin_time = datetime.now()
                            self.attendance_records[student_id] = checkin_time
                            threading.Thread(target=send_email_to_student, 
                                             args=(email, name, student_id, self.current_start_dt, checkin_time)).start()
                            
                            attendance_done = True
                            target_name = name # Lưu tên để hiện thông báo
                            break # Thoát vòng lặp for khuôn mặt

            cv2.imshow(f"Diem Danh: {self.current_shift_name}", frame)
            
            # Nếu đã điểm danh xong, đợi 1 giây để sinh viên thấy khung xanh rồi đóng
            if attendance_done:
                cv2.waitKey(1000) 
                messagebox.showinfo("Thành công", f"Sinh viên {target_name} đã điểm danh thành công!")
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()

    # ---------- MODULE 3: CHỐT SỔ & XUẤT EXCEL ----------
    def manual_send_report(self):
        if not self.current_start_dt:
            messagebox.showwarning("Cảnh báo", "Bạn chưa thực hiện điểm danh ca nào trong phiên làm việc này!")
            return
            
        confirm = messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn chốt sổ báo cáo cho:\n{self.current_shift_name}?")
        if not confirm: return
        
        try:
            with open(ENCODINGS_FILE, "rb") as f:
                data = pickle.load(f)
            all_students = data["info"]

            report_data = []
            for sv in all_students:
                s_id, name = sv["id"], sv["name"]
                
                if s_id in self.attendance_records:
                    checkin_time = self.attendance_records[s_id]
                    delay = (checkin_time - self.current_start_dt).total_seconds() / 60
                    status = "Có mặt" if delay <= 0 else "Đi muộn"
                    note = "Đúng giờ" if delay <= 0 else f"Muộn {int(delay)} phút"
                    time_str = checkin_time.strftime("%H:%M:%S")
                else:
                    status, note, time_str = "Nghỉ học", "", ""

                report_data.append({
                    "Mã SV": s_id, "Họ Tên": name,
                    "Thời gian quét": time_str,
                    "Trạng thái": status, "Ghi chú": note
                })

            # Xuất Excel
            df = pd.DataFrame(report_data)
            excel_filename = f"BaoCao_{self.current_start_dt.strftime('%Y%m%d_%H%M')}.xlsx"
            df.to_excel(excel_filename, index=False)
            
            # Gửi Email cho Giáo viên
            msg = MIMEMultipart()
            msg['Subject'] = f"Báo cáo Điểm danh - {self.current_shift_name}"
            msg['From'] = msg['To'] = SENDER_EMAIL
            msg.attach(MIMEText("Hệ thống gửi file đính kèm báo cáo điểm danh.", "plain", "utf-8"))

            with open(excel_filename, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {excel_filename}")
            msg.attach(part)

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, SENDER_EMAIL, msg.as_string())
            server.quit()
            
            messagebox.showinfo("Thành công", "Đã chốt sổ, tạo file Excel và gửi về Email của Giáo viên!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra khi tạo báo cáo:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()