# 🐍 Sử dụng Python 3.10 slim (Debian-based)
FROM python:3.10-slim

# 🏠 Đặt thư mục làm việc
WORKDIR /app

# 🏗 Cài đặt gói hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    fonts-dejavu \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 📥 Copy file requirements
COPY requirements.txt .

# 📦 Cài đặt thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# 📥 Copy mã nguồn
COPY . .

# 🔥 Mở cổng 8000
EXPOSE 8000

# 🚀 Chạy ứng dụng
CMD ["gunicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
