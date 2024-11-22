import os
import tempfile
from flask import Flask, request, jsonify
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import requests

OLLAMA_URL = "http://10.1.0.101:8080/api/chat"
app = Flask(__name__)

def query_ollama(text):
    prompt = {
        "role": "system", 
        "content": "คุณเป็นเลขาของท่านประธาน หน้าที่ของคุณคือการสรุปเนื้อหาจากข้อความอย่างละเอียดและเป็นระเบียบ กรุณาสรุปเนื้อหาอย่างรอบคอบและแม่นยำ",
        "role": "user",
        "content": f"จงสรุปเนื้อหาต่อไปนี้ {text} กรุณาตอบเฉพาะเนื้อหาในข้อความและตอบเป็นภาษาไทย"
    }
    
    json_payload = {
        "model": "gemma2:27b",
        "messages": [prompt],
        "stream": False
    }
    
    # print(json_payload)
    
    response = requests.post(OLLAMA_URL, json=json_payload)
    # print(response)
    if response.status_code == 200:
        result = response.json().get("message", {}).get("content", "")
        # print(result)
        if result:
            return result
        else:
            return "The AI returned an empty response."
    else:
        print("Error:", response.status_code, response.text)
        return "Sorry, I couldn't get a response from the AI."

@app.route('/ocr', methods=['POST'])
def ocr_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request.'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400
    if file:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                file.save(tmp_pdf.name)
                pdf_path = tmp_pdf.name

            images = convert_from_path(pdf_path)

            extracted_text = ''

            for page_num, image in enumerate(images, start=1):
                print(f'Processing page {page_num}...')
                page_text = pytesseract.image_to_string(image, lang='tha')
                extracted_text += page_text + '\n\n'

            os.remove(pdf_path)
            
            text = query_ollama(extracted_text)
            return jsonify({'results': text}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'File processing failed.'}), 500

if __name__ == '__main__':
    app.run(debug=True)