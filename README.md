# Exchage Rates Scraper & Gemini Extractor

Скрипт для скрапинга страницы банка (Playwright) и отправки HTML в Gemini (gemini-2.5-flash-lite) с системным промптом для извлечения курсов USD/EUR/RUB.

---

## Пример входного файла `input.json`

```json
{
  "id": "9f687e1b-da3f-4c65-a2a5-5545077246bd",
  "name_en": "National Bank of Uzbekistana",
  "name_local": "O'zmilliybank",
  "email": "info@nbu.uz",
  "url_cur_page": "https://nbu.uz/ru/fizicheskim-litsam-kursy-valyut"
}

Установка зависимостей

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium

requirements.txt:

httpx>=0.23.0
playwright>=1.40.0
python-dotenv>=1.0.0

Примеры запуска
1. Только скачать HTML (dry-run)

python rates.py --input input.json --output page.html --dry-run

Отправить в Gemini (API)

Необходимо задать переменную окружения GEMINI_API_KEY с вашим ключом.

Windows CMD:

set GEMINI_API_KEY=ВАШ_КЛЮЧ
python rates.py --input input.json --output rates_output.json


Результат

Файл rates_output.json будет содержать:

{
  "bankId": "9f687e1b-da3f-4c65-a2a5-5545077246bd",
  "atm": {
    "purchase_USD": "11996.14",
    "sale_USD": "11996.14",
    "purchase_EUR": "14051.08",
    "sale_EUR": "14051.08",
    "purchase_RUB": "148.54",
    "sale_RUB": "148.54"
  },
  "office": {
    "purchase_USD": "11996.14",
    "sale_USD": "11996.14",
    "purchase_EUR": "14051.08",
    "sale_EUR": "14051.08",
    "purchase_RUB": "148.54",
    "sale_RUB": "148.54"
  },
  "app": {
    "purchase_USD": "11996.14",
    "sale_USD": "11996.14",
    "purchase_EUR": "14051.08",
    "sale_EUR": "14051.08",
    "purchase_RUB": "148.54",
    "sale_RUB": "148.54"
  }
}
