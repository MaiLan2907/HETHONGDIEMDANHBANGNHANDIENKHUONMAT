<h1 align="center">FACE ATTENDANCE SYSTEM
HỆ THỐNG ĐIỂM DANH KHUÔN MẶT</h1>

<div align="center">
<p align="center">
  <img src="static/logoDaiNam.png" alt="DaiNam University Logo" width="200"/>
  <img src="static/LogoAIoTLab.png" alt="AIoTLab Logo" width="170"/>
</p>

[![Made by AIoTLab](https://img.shields.io/badge/Made%20by%20AIoTLab-blue?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Fit DNU](https://img.shields.io/badge/Fit%20DNU-green?style=for-the-badge)](https://fitdnu.net/)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-red?style=for-the-badge)](https://dainam.edu.vn)

[![Made with Flask](https://img.shields.io/badge/Made%20with-Flask-blue?style=for-the-badge)](https://flask.palletsprojects.com/)
[![Computer Vision](https://img.shields.io/badge/Computer%20Vision-OpenCV-yellow?style=for-the-badge)](https://opencv.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge)](https://www.python.org/)
[![Email Alert](https://img.shields.io/badge/Feature-Email%20Alert-orange?style=for-the-badge)](https://developer.mozilla.org/)

</div>

---

## 🌟 Giới thiệu

**Face Attendance System** là một hệ thống điểm danh tự động sử dụng **Nhận diện khuôn mặt** và **Webcam** để kiểm tra danh tính sinh viên, ghi nhận thời gian vào lớp và gửi thông báo email.

Hệ thống hỗ trợ:
- Đăng ký sinh viên qua webcam với nhiều mẫu ảnh.
- Quét khuôn mặt trực tiếp trong lớp học.
- Tự động phân loại đúng giờ / đi muộn.
- Xuất báo cáo điểm danh và gửi email cho giảng viên.

<img src="static\Screenshot 2026-05-25 182711.png" alt="Dashboard" width="100%"/>

---

## 🚀 Tính Năng Chính

### 📷 **Đăng Ký Khuôn Mặt Sinh Viên**
- Yêu cầu **5 ảnh mẫu** cho mỗi sinh viên.
- Xác thực admin trước khi đăng ký.
- Lưu encoding khuôn mặt vào file `encodings.pickle`.

### 📡 **Điểm Danh Thực Tế**
- Sử dụng **webcam** để quét khuôn mặt.
- So sánh với dữ liệu đã đăng ký.
- Hiển thị tên, mã số và trạng thái trực tiếp lên video.
- Cảnh báo khi sinh viên quét lại hoặc điểm danh thành công.

### 🧾 **Báo Cáo Điểm Danh**
- Xuất file Excel trong thư mục `attendance_reports/`.
- Gửi báo cáo tự động qua email.
- Thống kê số sinh viên:
  - Có mặt
  - Đi muộn
  - Nghỉ học

### 🎯 **Quản Lý Lịch Ca Học**
- Hỗ trợ 2 ca mặc định:
  - Ca sáng: 07:20 - 12:00
  - Ca chiều: 13:05 - 17:45
- Chỉ cho phép điểm danh trong khung giờ hợp lệ.

---

## 📁 Cấu Trúc Dự Án

```
face-attendance-system/
│
├── app.py                      # 🔧 Ứng dụng Flask chính + nhận diện khuôn mặt
├── README.md                   # 📖 Tài liệu này
├── encodings.pickle            # 🧠 Dữ liệu encoding khuôn mặt đã lưu
├── attendance_reports/         # 📂 Lưu file báo cáo Excel xuất ra
│
├── templates/
│   ├── index.html              # 🌐 Trang chọn ca và bắt đầu điểm danh
│   ├── dashboard.html          # 📊 Bảng điều khiển điểm danh trực tiếp
│   └── admin_register.html     # 👤 Trang admin đăng ký sinh viên
│
├── static/
│   └── success.mp3             # 🔔 Âm thanh cảnh báo điểm danh
│
├── venv/                       # 🐍 Môi trường ảo Python
└── dlib-19.22.99-cp310-cp310-win_amd64.whl  # 📦 Thư viện dlib cho nhận diện khuôn mặt
```

---

## ⚙️ Công Nghệ Sử Dụng

| Công nghệ | Mục đích |
|-----------|---------|
| **Python 3.10+** | Ngôn ngữ chính |
| **Flask** | Web framework cho giao diện và API |
| **OpenCV** | Xử lý ảnh/video và webcam |
| **face_recognition** | Nhận diện khuôn mặt |
| **pickle** | Lưu trữ encoding khuôn mặt |
| **pandas** | Tạo báo cáo Excel |
| **smtplib** | Gửi email thông báo |

---

## 🖥️ Cài Đặt & Chạy Ứng Dụng

### 1️⃣ Chuẩn bị môi trường
```bash
cd d:\MAILAN
python -m venv venv
venv\Scripts\activate
```

### 2️⃣ Cài đặt thư viện
```bash
pip install flask opencv-python face-recognition pandas openpyxl
```

### 3️⃣ Chạy ứng dụng
```bash
python app.py
```

**Truy cập:** `http://localhost:5000`

---

## 📖 Hướng Dẫn Sử Dụng

### 👨‍🏫 Đăng nhập admin và đăng ký sinh viên
1. Mở `http://localhost:5000/motcua`
2. Nhập tài khoản admin:
   - Email: `admin@gmail.com`
   - Mật khẩu: `12345a`
3. Nhập mã sinh viên, tên và email.
4. Chụp đủ 5 ảnh để hệ thống lưu encoding.

### 🎥 Bắt đầu điểm danh
1. Mở trang chính `http://localhost:5000`.
2. Chọn ca học phù hợp.
3. Nhấn **Bắt đầu** để vào dashboard.
4. Webcam sẽ quét khuôn mặt và ghi nhận điểm danh.

### 📊 Xem báo cáo
- Truy cập `http://localhost:5000/report` để xuất báo cáo Excel.
- File sẽ được lưu trong `attendance_reports/`.
- Hệ thống cũng gửi báo cáo tới email cấu hình sẵn.

---

## 🔧 Cấu Hình Email

Mở `app.py` và sửa các giá trị sau nếu cần:

```python
SENDER_EMAIL = "Youremail@gmail.com"
APP_PASSWORD = "your email code"
```

> Lưu ý: Tài khoản Gmail phải bật **Less secure app access** hoặc sử dụng mật khẩu ứng dụng.

---

## 📌 Lưu ý

- Hệ thống hiện tại sử dụng **webcam mặc định** (`cv2.VideoCapture(0)`).
- Nếu muốn chạy với webcam khác, sửa trong hàm `generate_frames()`.
- File `encodings.pickle` chứa dữ liệu khuôn mặt; sao lưu nếu cần mở rộng dữ liệu.

---

<div align="center">

**⭐ Nếu dự án hữu ích, hãy cho một ⭐ star!**

</div>
