# Cấu hình Cursor cho Digital Metrics API

Dự án này đã được cấu hình để tự động kích hoạt môi trường ảo Python khi chạy với Cursor IDE.

## Các tệp cấu hình

- `.cursor/launch.json`: Cấu hình các cấu hình chạy và debug trong Cursor
- `.cursor/tasks.json`: Định nghĩa các tác vụ, bao gồm tác vụ kích hoạt môi trường
- `.cursor/runcommands.yaml`: Định nghĩa các lệnh tùy chỉnh khi chạy trong terminal
- `.cursor-commands.json`: Cung cấp các lệnh nhanh trong giao diện người dùng Cursor

## Cách sử dụng

### Chạy ứng dụng

1. Trong Cursor, nhấn `Ctrl+Shift+D` để mở panel Debug
2. Chọn cấu hình "Python: FastAPI" từ dropdown
3. Nhấn nút Play hoặc F5 để khởi động ứng dụng

### Chạy file hiện tại

1. Mở file Python bạn muốn chạy
2. Nhấn `Ctrl+Shift+D` để mở panel Debug
3. Chọn cấu hình "Python: Current File" từ dropdown
4. Nhấn nút Play hoặc F5 để chạy file

### Sử dụng lệnh tùy chỉnh

1. Mở terminal trong Cursor (Ctrl+`)
2. Các lệnh như `python`, `uvicorn`, `pytest`, `pip` đã được cấu hình để tự động kích hoạt môi trường ảo

### Lệnh nhanh trong UI

1. Nhấn `Ctrl+Shift+P` để mở Command Palette
2. Nhập "Run Command" và chọn "Run Command"
3. Chọn một trong các lệnh đã cấu hình:
   - Khởi động API
   - Debug
   - Chạy Tests
   - Cài đặt Packages
   - Kích hoạt Môi trường

## Cấu hình môi trường

Các cấu hình này sử dụng môi trường ảo Python nằm trong thư mục `venv` ở thư mục gốc của dự án. Đảm bảo bạn đã tạo môi trường ảo này trước khi sử dụng các cấu hình.

Để tạo môi trường ảo (nếu chưa có):

```powershell
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Cài đặt các gói cần thiết
pip install -r requirements.txt
```
