from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import easyocr
import io
import re
import numpy as np
import datetime
from PIL import Image
import uvicorn
from pdf2image import convert_from_bytes
from PyPDF2 import PdfReader

app = FastAPI()
reader = easyocr.Reader(["en", "vi"])  # Hỗ trợ cả tiếng Anh & tiếng Việt

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

    bank_corrections = {
        "AB": "ACB",
        "VetinBank": "Viettinbank"
    }

    bank_patterns = r"\b(BIDV|ACB|Vietcombank|Techcombank|MB|Sacombank|VPBank|TPBank|HDBank|VIB|SHB|SeABank|NamABank|Eximbank|OCB|Agribank|DongABank|BacABank|SCB|ABBANK|VietinBank|LienVietPostBank|NCB|PVcomBank|Kienlongbank|PG Bank|SaigonBank)\b"
    account_pattern = r"\b\d{6,16}\b"
    amount_pattern = r"(\d{1,3}(?:[., ]\d{3})*(?:\.\d{1,3})?)\s?(VND|VNĐ|₫)"
    transaction_id_pattern = r"\b[A-Z0-9]{10,}\b"
    time_pattern = r"\b\d{2}/\d{2}/\d{4}(?:\s+\d{2}[:.]\d{2}[:.]\d{2})?\b"
    fee_pattern = r"Phí[:]?\s?(Miễn phí|\d{1,3}(?:[ .,]?\d{3})*)\b"
    description_pattern = r"(?:Nội dung|chuyển tiền|chuyển khoản|chuyen|chuyển|khoản|chuyen tien|chuyen khoan)[: ]+ (.+)"
    status_pattern = r"(Thành công|Thất bại|Hoàn tiền)"
    recipient_pattern = r'Đến tài khoản\s+\d+\s+([A-ZĐÂÊÔƠƯÁÀẢÃẠÉÈẺẼẸÍÌỈĨỊÓÒỎÕỌÚÙỦŨỤẾỀỂỄỆỐỒỔỖỘỚỜỞỠỢỨỪỬỮỰ\s]+)'

    for text in text_list:
        text = text.strip()

        match = re.search(bank_patterns, text, re.IGNORECASE)
        if match:
            extracted_data["bank_name"] = match.group()

        if extracted_data["bank_name"] == "Không xác định":
            for key, value in bank_corrections.items():
                if re.search(rf"\b{re.escape(key)}\b", text, re.IGNORECASE):
                    extracted_data["bank_name"] = value
                    break

        if re.search(status_pattern, text, re.IGNORECASE):
            extracted_data["transaction_status"] = re.search(status_pattern, text, re.IGNORECASE).group()

        if re.search(account_pattern, text):
            extracted_data["account_number"] = re.search(account_pattern, text).group()

        if "amount" not in extracted_data or extracted_data["amount"] == "0":
            amount_match = re.search(amount_pattern, text)
            if amount_match:
                extracted_data["amount"] = amount_match.group(1).replace(" ", "").replace(".", "")

        if re.search(transaction_id_pattern, text):
            extracted_data["transaction_id"] = re.search(transaction_id_pattern, text).group()

        time_match = re.search(time_pattern, text)
        if time_match:
            extracted_data["transaction_time"] = time_match.group().replace(".", ":")
        else:
            extracted_data["transaction_time"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        match_desc = re.search(description_pattern, text)
        if match_desc:
            extracted_data["description"] = match_desc.group(1).strip()

        match_fee = re.search(fee_pattern, text)
        if match_fee:
            extracted_data["transaction_fee"] = match_fee.group()

        if "Đến tài khoản" in text:
            match = re.search(recipient_pattern, " ".join(text_list))
            if match:
                extracted_data['recipient_name'] = match.group(1).strip()

    return extracted_data

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)
        results = reader.readtext(image_np, detail=0)
        transaction_data = extract_transaction_details(results)
        return {"filename": file.filename, "transaction_data": transaction_data, "raw_data": results}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Error processing image: {str(e)}"}
        )

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        pdf_bytes = await file.read()
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PdfReader(pdf_file)
        
        all_results = []
        all_transaction_data = []
        
        images = convert_from_bytes(pdf_bytes)
        for i, image in enumerate(images):
            image_np = np.array(image)
            
            results = reader.readtext(image_np, detail=0)
            
            transaction_data = extract_transaction_details(results)
            
            all_results.extend(results)
            all_transaction_data.append({
                "page": i + 1,
                "data": transaction_data
            })
        
        return {
            "filename": file.filename,
            "total_pages": len(pdf_reader.pages),
            "transactions": all_transaction_data,
            "raw_data": all_results
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Error processing PDF: {str(e)}"}
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
