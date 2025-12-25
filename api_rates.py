# api_rates_windows.py
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.sync_api import sync_playwright
import google.genai as genai
from google.genai import types
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# ---------------- Models ----------------
class BankInput(BaseModel):
    id: str
    name_en: str
    name_local: str
    email: str
    url_cur_page: str

# ---------------- Config ----------------
MAX_CHUNK_LEN = 120_000  # если нужно разбивать на части
executor = ThreadPoolExecutor(max_workers=2)

# ---------------- HTML Fetch ----------------
def fetch_html_sync(url: str) -> str:
    """Синхронный fetch HTML через Playwright"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(3000)  # ждём, чтобы JS подгрузился
        html = page.content()
        browser.close()
        return html

# ---------------- Gemini Prompt ----------------
def build_gemini_prompt(bank_id: str) -> str:
    return f"""
You are extracting structured currency exchange data from raw HTML of a bank website.

Task:
Analyze the HTML and find exchange rates for USD, EUR, and RUB.

Data sources to look for (by meaning, not exact text):
- ATM rates (банкомат, ATM)
- Exchange office cash rates (пункты обмена, касса, наличные)
- Mobile app / online banking rates (приложение, online, интернет-банк)

Rules:
- Extract ONLY numeric values.
- Do NOT include currency symbols, text, or explanations.
- If a rate is missing or not found, return null.
- Do NOT calculate or guess values.
- Do NOT merge sources: ATM, office, and app must be separate.
- Use the FIRST clearly matching rate found in the HTML for each field.

Return the result strictly in the following JSON format and nothing else:

{{
  "bankId": "{bank_id}",
  "atm": {{"purchase_USD": "", "sale_USD": "", "purchase_EUR": "", "sale_EUR": "", "purchase_RUB": "", "sale_RUB": ""}},
  "office": {{"purchase_USD": "", "sale_USD": "", "purchase_EUR": "", "sale_EUR": "", "purchase_RUB": "", "sale_RUB": ""}},
  "app": {{"purchase_USD": "", "sale_USD": "", "purchase_EUR": "", "sale_EUR": "", "purchase_RUB": "", "sale_RUB": ""}}
}}
"""

def clean_gemini_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    if text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text

# ---------------- Gemini Call ----------------
def call_gemini(prompt: str, html_chunk: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY не задан")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, html_chunk],
        config=types.GenerateContentConfig(temperature=0)
    )

    result_text = clean_gemini_response(response.text)

    try:
        result_json = json.loads(result_text)
    except json.JSONDecodeError:
        result_json = {"raw_text": result_text}

    return result_json

# ---------------- FastAPI Endpoint ----------------
@app.post("/extract_rates")
def extract_rates(bank: BankInput):
    try:
        # Получаем HTML в отдельном потоке, чтобы не блокировать FastAPI
        html = executor.submit(fetch_html_sync, bank.url_cur_page).result()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch HTML: {e}")

    # Формируем промпт для Gemini
    prompt = build_gemini_prompt(bank.id)

    try:
        # Отправляем HTML в Gemini
        result = call_gemini(prompt, html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini request failed: {e}")

    return result
