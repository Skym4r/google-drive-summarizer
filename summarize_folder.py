import os
import gdown
import pdfplumber
import pytesseract
from PIL import Image
from openai import OpenAI

# --- КОНФИГУРАЦИЯ ---
FOLDER_URL = "https://drive.google.com/drive/folders/1x6EKNkVw6PlFVTr6cGrsVscmRuwqGrXd?usp=sharing"
LOCAL_DIR = "./documents"
OPENAI_API_KEY = "Вставьте_свое_АПИ"
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['ALL_PROXY'] = ''
os.environ['NO_PROXY'] = 'api.openai.com'
client = OpenAI(  base_url="https://openrouter.ai/api/v1", api_key=OPENAI_API_KEY)


def download_folder():
    if not os.path.exists(LOCAL_DIR):
        print("Скачиваем папку...")
        gdown.download_folder(FOLDER_URL, output=LOCAL_DIR, quiet=False)
    else:
        print("Папка уже скачана.")


def extract_text_from_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Ошибка чтения PDF {file_path}: {e}")
    return text


def extract_text_from_image(file_path):
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img, lang='rus+eng')
        return text
    except Exception as e:
        print(f"Ошибка OCR {file_path}: {e}")
        return ""


def collect_all_text():
    all_text = ""
    for root, dirs, files in os.walk(LOCAL_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            ext = file.lower().split('.')[-1]

            if ext == 'pdf':
                print(f"Извлекаем текст из PDF: {file}")
                all_text += extract_text_from_pdf(file_path) + "\n\n"
            elif ext in ['jpg', 'jpeg', 'png', 'webp']:
                print(f"Распознаем изображение: {file}")
                all_text += extract_text_from_image(file_path) + "\n\n"
    return all_text


def generate_summary(text):
    if not text.strip():
        return "Не удалось извлечь текст из документов."


    if len(text) > 10000:
        text = text[:10000] + "...(обрезано)"

    print("Отправляем текст в LLM для саммари...")
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {"role": "system",
             "content": "Ты — аналитик. Сделай краткое, но содержательное саммари по всем документам. Выдели ключевые темы, сущности и смысл."},
            {"role": "user", "content": f"Вот текст из папки с документами:\n\n{text}"}
        ]
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    download_folder()
    full_text = collect_all_text()
    summary = generate_summary(full_text)
    print("\n--- РЕЗУЛЬТАТ ---\n")
    print(summary)