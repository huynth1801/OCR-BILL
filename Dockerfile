# 🐍 Sử dụng Python 3.10 trở lên làm base image
FROM python:3.10-slim

# 🏠 Đặt thư mục làm việc trong container
WORKDIR /app

# 🏗 Cài đặt các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 📥 Copy file requirements vào container
COPY requirements.txt .

# 📦 Cài đặt các thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# 📥 Copy toàn bộ mã nguồn vào container
COPY . .

# 🔥 Mở cổng 8000
EXPOSE 8000

# 🚀 Chạy ứng dụng
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
