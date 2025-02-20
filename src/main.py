from fastapi import FastAPI, File, UploadFile
import easyocr
import io
from PIL import Image
import numpy as np
import re
import uvicorn  # Import Uvicorn để chạy server

app = FastAPI()
reader = easyocr.Reader(["en", "vi"])  # Hỗ trợ cả tiếng Anh & tiếng Việt


# 🔍 Hàm nhận diện nội dung chuyển khoản từ ảnh
def extract_transaction_details(text_list):
    extracted_data = {
        "bank_name": "Không xác định",
        "transaction_status": "Không xác định",
        "amount": "0",
        "account_number": "Không xác định",
        "transaction_time": "Không xác định",
        "transaction_fee": "Không xác định",
        "transaction_id": "Không xác định",
        "description": "Không xác định",
        "recipient_name": "Không xác định",
    }

    # 🔥 Danh sách ngân hàng phổ biến
    bank_patterns = r"\b(?!BIDV|ACB)\w*bank\b"


    # 🔥 Biểu thức chính quy (Regex)
    account_pattern = r"\b\d{6,16}\b"  # Số tài khoản: 6-16 số
    amount_pattern = r"\b\d{1,3}(?:[ .,]?\d{3})*(?:₫| VND| VNĐ)?\b"  # Số tiền có dấu chấm hoặc khoảng trắng
    transaction_id_pattern = r"\b[A-Z0-9]{10,}\b"  # Mã giao dịch dài ít nhất 10 ký tự
    time_pattern = r'\b\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2})?\b'  # Thời gian dạng: DD/MM/YYYY HH:mm hoặc DD/MM/YYYY
    fee_pattern = r"\bPhí[:]? (\d{1,3}(?:[ .,]?\d{3})*)\b"  # Phí giao dịch (nếu có)
    description_pattern = r"(?:ND|Nội dung|Description)[:]? (.+)"  # Nội dung chuyển khoản
    status_pattern = r"(Thành công|Thất bại|Hoàn tiền)"  # Trạng thái giao dịch

    # 🔹 Regex tìm tên người nhận (IN HOA, có thể có số)
    recipient_pattern = r'Đến tài khoản\s+\d+\s+([A-ZĐÂÊÔƠƯÁÀẢÃẠÉÈẺẼẸÍÌỈĨỊÓÒỎÕỌÚÙỦŨỤẾỀỂỄỆỐỒỔỖỘỚỜỞỠỢỨỪỬỮỰ\s]+)'

    for text in text_list:
        text = text.strip()

        # 🔹 Kiểm tra ngân hàng
        # for bank in bank_patterns:
        #     if bank.lower() in text.lower():
        #         extracted_data["bank_name"] = bank
        #         break  # Dừng ngay khi tìm thấy

        if re.search(bank_patterns, text, re.IGNORECASE):
            extracted_data["bank_name"] = re.search(bank_patterns, text, re.IGNORECASE).group()
        # 🔹 Kiểm tra trạng thái giao dịch
        if re.search(status_pattern, text, re.IGNORECASE):
            extracted_data["transaction_status"] = re.search(status_pattern, text, re.IGNORECASE).group()

        # 🔹 Kiểm tra số tài khoản
        if re.search(account_pattern, text):
            extracted_data["account_number"] = re.search(account_pattern, text).group()

        # 🔹 Kiểm tra số tiền
        if re.search(amount_pattern, text):
            extracted_data["amount"] = re.search(amount_pattern, text).group().replace(" ", "").replace(".", "")

        # 🔹 Kiểm tra mã giao dịch
        if re.search(transaction_id_pattern, text):
            extracted_data["transaction_id"] = re.search(transaction_id_pattern, text).group()

        # 🔹 Kiểm tra thời gian giao dịch
        if re.search(time_pattern, text):
            extracted_data["transaction_time"] = re.search(time_pattern, text).group()

        # 🔹 Kiểm tra nội dung chuyển khoản
        match_desc = re.search(description_pattern, text)
        if match_desc:
            extracted_data["description"] = match_desc.group(1)

        # 🔹 Kiểm tra phí giao dịch
        match_fee = re.search(fee_pattern, text)
        if match_fee:
            extracted_data["transaction_fee"] = match_fee.group(1)

        if "Đến tài khoản" in text:
            match = re.search(recipient_pattern, " ".join(text_list))
            if match:
                extracted_data['recipient_name'] = match.group(1).strip()


    return extracted_data

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # Đọc ảnh từ file tải lên
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Chuyển ảnh PIL thành mảng NumPy
    image_np = np.array(image)

    # Nhận diện văn bản từ ảnh
    results = reader.readtext(image_np, detail=0)

    print("result", results)

    # Trích xuất thông tin giao dịch từ văn bản OCR
    transaction_data = extract_transaction_details(results)

    return {"filename": file.filename, "transaction_data": transaction_data}


# Chạy server nếu chạy trực tiếp file này
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
