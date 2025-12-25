import os
import json
import asyncio
from playwright.async_api import async_playwright
import google.genai as genai
from google.genai import types

# ---------------- CONFIG ----------------
BANK_ID = "9f687e1b-da3f-4c65-a2a5-554507"
URL = "https://nbu.uz/ru/fizicheskim-litsam-kursy-valyut"
OUTPUT_FILE = "rates_gemini.json"
FULL_HTML_FILE = "rates_full.html"

# ---------------- HTML ----------------
async def fetch_html(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        html = await page.content()
        await browser.close()
        return html

# ---------------- Gemini Prompt ----------------
SYSTEM_PROMPT = f"""
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
  "bankId": "{BANK_ID}",
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

# ---------------- Main ----------------
async def main():
    print(f"🌍 Загружаем страницу: {URL}")
    html = await fetch_html(URL)
    print(f"💾 Полный HTML загружен, длина: {len(html)}")

    # Сохраняем HTML
    with open(FULL_HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"💾 HTML сохранён в {FULL_HTML_FILE}")

    # Проверка API ключа
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY не задан")

    client = genai.Client(api_key=api_key)

    # Отправка запроса в Gemini
    print("📦 Отправка HTML в Gemini...")
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[SYSTEM_PROMPT, html],
        config=types.GenerateContentConfig(temperature=0)
    )

    result_text = clean_gemini_response(response.text)
    print("🔹 Ответ Gemini (preview):", result_text[:500], "...")

    # Преобразуем в JSON
    try:
        result = json.loads(result_text)
    except json.JSONDecodeError:
        print("⚠️ Gemini вернул некорректный JSON. Сохраняем текст как есть.")
        result = {"raw_text": result_text}

    # Сохраняем финальный JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Результат записан в {OUTPUT_FILE}")

# ---------------- Run ----------------
if __name__ == "__main__":
    asyncio.run(main())
