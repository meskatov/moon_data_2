import asyncio
import html
import os
import sqlite3
import re
import requests
import aiohttp
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import add_search_log, is_admin, send_tech_log
from config import (
    INFINITY_API_URL, INFINITY_TOKEN,
    DEPSEARCH_TOKEN, DEPSEARCH_BASE_URL,
    BIGBASE_URL, BIGBASE_TOKEN
)

router = Router()


# ==================== КЛАВИАТУРЫ ====================

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Искать")],
            [KeyboardButton(text="👤 Профиль | 🎫 Промокод")],
            [KeyboardButton(text="🛠️ Административная панель"), KeyboardButton(text="💬 Поддержка")]
        ],
        resize_keyboard=True
    )


def get_search_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Телефон")],
            [KeyboardButton(text="👤 ФИО")],
            [KeyboardButton(text="📧 Email")],
            [KeyboardButton(text="🔍 Username")],
            [KeyboardButton(text="🔑 Пароль")],
            [KeyboardButton(text="🆔 SNILS")],
            [KeyboardButton(text="📄 ИНН")],
            [KeyboardButton(text="🌐 IP-адрес")],
            [KeyboardButton(text="◀️ Назад в меню")]
        ],
        resize_keyboard=True
    )


class SearchState(StatesGroup):
    waiting_type = State()
    waiting_query = State()


# Глобальный словарь для хранения результатов
search_results = {}


# ==================== API ЗАПРОСЫ ====================

def call_depsearch(query):
    """Запрос к Depsearch API"""
    try:
        url = f"{DEPSEARCH_BASE_URL}quest={query}&token={DEPSEARCH_TOKEN}"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and data.get("results"):
                return data["results"]
            return data
    except:
        pass
    return None


def call_bigbase(query):
    """Запрос к BigBase API"""
    try:
        headers = {"Authorization": BIGBASE_TOKEN, "Content-Type": "application/json"}
        r = requests.post(BIGBASE_URL, headers=headers, json={"search": query}, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and data.get("results"):
                return data["results"]
            return data
    except:
        pass
    return None


async def call_infinity(search_type, query):
    """Запрос к Infinity API"""
    try:
        params = {'token': INFINITY_TOKEN}

        if search_type == '📱 Телефон':
            clean_phone = re.sub(r'[\s\-\(\)\+]', '', query)
            if clean_phone.startswith('8'):
                clean_phone = '7' + clean_phone[1:]
            if not clean_phone.startswith('7'):
                clean_phone = '7' + clean_phone
            params['phone'] = clean_phone
        elif search_type == '👤 ФИО':
            params['fio'] = query.strip()
        elif search_type == '📧 Email':
            params['email'] = query.strip().lower()
        elif search_type == '🌐 IP-адрес':
            params['ip'] = query.strip()
        elif search_type == '🔍 Username':
            params['telegram'] = query.strip()
        else:
            return None

        async with aiohttp.ClientSession() as session:
            async with session.get(INFINITY_API_URL, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                return None
    except Exception as e:
        print(f"[INFINITY] Error: {e}")
        return None


def check_callapp(phone_number):
    """Проверка номера через CallApp API"""
    try:
        phone_number = re.sub(r'[\s\-\(\)\+]', '', phone_number)
        if phone_number.startswith('8'):
            phone_number = '7' + phone_number[1:]
        if not phone_number.startswith('7'):
            phone_number = '7' + phone_number

        params = {
            "cpn": f"+{phone_number}",
            "myp": "fb.1122543675802814",
            "ibs": "3",
            "tk": "0017356813",
            "cvc": 2038
        }
        url = "https://s.callapp.com/callapp-server/csrch"

        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, params=params, timeout=5)
        except:
            response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            return {'success': True, 'name': data.get('name'), 'rating': data.get('rating')}
        return {'success': False}
    except:
        return {'success': False}


def check_eyecon(phone):
    """Проверка номера через Eyecon API"""
    try:
        clean_phone = re.sub(r'[^\d]', '', phone)
        if clean_phone.startswith('7') and len(clean_phone) == 11:
            formatted_phone = clean_phone
        elif clean_phone.startswith('8') and len(clean_phone) == 11:
            formatted_phone = f"7{clean_phone[1:]}"
        elif len(clean_phone) == 10:
            formatted_phone = f"7{clean_phone}"
        else:
            formatted_phone = clean_phone

        url = "https://api.eyecon-app.com/app/getnames.jsp"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "e-auth-v": "e1",
            "e-auth": "d9889e1c-521c-4ded-9b15-f64bb069148b",
            "e-auth-c": "46",
            "e-auth-k": "PgdtSBeR0MumR7fO"
        }
        params = {"cli": formatted_phone, "lang": "ru"}

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            result = {}
            if isinstance(data, dict):
                if data.get('name'):
                    result['name'] = data['name']
                if data.get('rating'):
                    result['rating'] = data['rating']
            return {'success': True, 'data': result} if result else {'success': False}
        return {'success': False}
    except:
        return {'success': False}


def check_zvonili(phone_number):
    """Проверка номера через zvonili.com"""
    try:
        phone_number = re.sub(r'[\s\-\(\)\+]', '', phone_number)
        if phone_number.startswith('8'):
            phone_number = '7' + phone_number[1:]
        if not phone_number.startswith('7'):
            phone_number = '7' + phone_number

        phone_for_url = phone_number[1:] if phone_number.startswith('7') else phone_number
        url = f"https://zvonili.com/phone/{phone_for_url}"
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            result = {'operator': None, 'region': None, 'rating': None}

            main_content = soup.find('div', class_='col-lg-9')
            if main_content:
                full_text = main_content.get_text()
                operator_match = re.search(r'оператору\s+([^в]+?)\s+в', full_text)
                if operator_match:
                    result['operator'] = operator_match.group(1).strip()
                region_match = re.search(r'регионе\s+([^\n]+)', full_text)
                if region_match:
                    result['region'] = region_match.group(1).strip()

            rating_span = soup.find('span', class_='rating-number')
            if rating_span:
                try:
                    result['rating'] = float(rating_span.text.strip())
                except:
                    pass

            return {'success': True, 'data': result}
        return {'success': False}
    except:
        return {'success': False}


# ==================== ПАРАЛЛЕЛЬНЫЕ ЗАПРОСЫ ====================

def run_parallel_requests(requests_list):
    """Выполняет несколько API запросов параллельно"""
    results = []
    if not requests_list:
        return results

    def make_request(name, query):
        if name == "DEPSEARCH":
            return call_depsearch(query)
        elif name == "BIGBASE":
            return call_bigbase(query)
        return None

    with ThreadPoolExecutor(max_workers=len(requests_list)) as executor:
        futures = {}
        for name, query in requests_list:
            future = executor.submit(make_request, name, query)
            futures[future] = (name, query)

        for future in as_completed(futures):
            try:
                data = future.result(timeout=10)
                if data:
                    results.append((data, futures[future][0]))
            except:
                pass

    return results


def extract_values(data, results, source):
    """Рекурсивно извлекает значения из JSON ответа"""
    if not data:
        return
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                results.append((item, source))
    elif isinstance(data, dict):
        if data.get("result"):
            extract_values(data["result"], results, source)
        elif data.get("results"):
            extract_values(data["results"], results, source)
        elif data.get("data"):
            extract_values(data["data"], results, source)
        else:
            results.append((data, source))


# ==================== ФОРМАТТЕРЫ ОТЧЕТОВ ====================

def format_preview(results):
    """Форматирует краткий предпросмотр результатов"""
    if not results:
        return "❌ Ничего не найдено"

    preview = "🔍 **Краткий результат:**\n"
    count = 0

    if results.get('infinity') and results['infinity'].get('results'):
        preview += f"• Infinity: {len(results['infinity']['results'])} записей\n"
        count += len(results['infinity']['results'])
    if results.get('depsearch') and results['depsearch']:
        preview += f"• Depsearch: {len(results['depsearch'])} записей\n"
        count += len(results['depsearch'])
    if results.get('bigbase') and results['bigbase']:
        preview += f"• BigBase: {len(results['bigbase'])} записей\n"
        count += len(results['bigbase'])
    if results.get('callapp') and results['callapp'].get('success'):
        preview += f"• CallApp: {results['callapp'].get('name', 'найден')}\n"
        count += 1
    if results.get('eyecon') and results['eyecon'].get('success') and results['eyecon'].get('data', {}).get('name'):
        preview += f"• Eyecon: {results['eyecon']['data'].get('name')}\n"
        count += 1
    if results.get('zvonili') and results['zvonili'].get('success') and results['zvonili'].get('data', {}).get(
            'operator'):
        preview += f"• Zvonili: {results['zvonili']['data'].get('operator')}\n"
        count += 1

    if count == 0:
        preview += "❌ Ничего не найдено"
    else:
        preview += f"\n📊 Всего найдено: {count} записей"

    return preview


def format_full_report(results, search_type, query):
    """Форматирует полный HTML отчет"""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Moon Data - Отчет по поиску</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .query {{
            background: rgba(255,255,255,0.2);
            padding: 10px;
            border-radius: 10px;
            font-family: monospace;
            font-size: 16px;
            margin: 5px 0;
        }}
        .content {{ padding: 30px; }}
        .section {{
            margin-bottom: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
        }}
        .section-title {{
            background: #f5f5f5;
            padding: 15px 20px;
            font-size: 18px;
            font-weight: bold;
            color: #333;
            border-bottom: 2px solid #667eea;
        }}
        .section-content {{ padding: 20px; }}
        .record {{
            background: #f9f9f9;
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}
        .record-item {{
            margin: 8px 0;
            display: flex;
        }}
        .record-label {{
            font-weight: bold;
            width: 100px;
            color: #555;
        }}
        .record-value {{
            flex: 1;
            color: #333;
            word-break: break-all;
        }}
        .footer {{
            background: #f5f5f5;
            padding: 15px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
        .badge {{
            background: #4CAF50;
            color: white;
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 11px;
            display: inline-block;
            margin-left: 10px;
        }}
        .no-data {{
            text-align: center;
            color: #999;
            padding: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌙 Moon Data 2.0</h1>
            <p>Результаты поиска</p>
            <div class="query">
                <strong>Тип:</strong> {html.escape(search_type)} | <strong>Запрос:</strong> {html.escape(query)}
            </div>
            <div class="query">
                <strong>Время:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
        <div class="content">
"""

    # Infinity результаты
    if results.get('infinity') and results['infinity'].get('results'):
        html_content += """
            <div class="section">
                <div class="section-title">🔗 Infinity Search <span class="badge">API</span></div>
                <div class="section-content">
        """
        for item in results['infinity']['results']:
            html_content += '<div class="record">'
            if item.get('fio'):
                html_content += f'<div class="record-item"><div class="record-label">ФИО:</div><div class="record-value">{html.escape(str(item["fio"]))}</div></div>'
            if item.get('phone'):
                html_content += f'<div class="record-item"><div class="record-label">Телефон:</div><div class="record-value">{html.escape(str(item["phone"]))}</div></div>'
            if item.get('email'):
                html_content += f'<div class="record-item"><div class="record-label">Email:</div><div class="record-value">{html.escape(str(item["email"]))}</div></div>'
            if item.get('data'):
                html_content += f'<div class="record-item"><div class="record-label">Данные:</div><div class="record-value">{html.escape(str(item["data"]))}</div></div>'
            html_content += '</div>'
        html_content += '</div></div>'

    # Depsearch результаты
    if results.get('depsearch') and results['depsearch']:
        html_content += """
            <div class="section">
                <div class="section-title">🔍 Depsearch <span class="badge">API</span></div>
                <div class="section-content">
        """
        for item in results['depsearch'][:15]:
            if isinstance(item, dict):
                html_content += '<div class="record">'
                for key, value in item.items():
                    if value and key not in ['raw']:
                        html_content += f'<div class="record-item"><div class="record-label">{key.capitalize()}:</div><div class="record-value">{html.escape(str(value))}</div></div>'
                html_content += '</div>'
            elif isinstance(item, str):
                html_content += f'<div class="record">{html.escape(item)}</div>'
        html_content += '</div></div>'

    # BigBase результаты
    if results.get('bigbase') and results['bigbase']:
        html_content += """
            <div class="section">
                <div class="section-title">🏦 BigBase <span class="badge">API</span></div>
                <div class="section-content">
        """
        for item in results['bigbase'][:15]:
            if isinstance(item, dict):
                html_content += '<div class="record">'
                for key, value in item.items():
                    if value:
                        html_content += f'<div class="record-item"><div class="record-label">{key.capitalize()}:</div><div class="record-value">{html.escape(str(value))}</div></div>'
                html_content += '</div>'
            elif isinstance(item, str):
                html_content += f'<div class="record">{html.escape(item)}</div>'
        html_content += '</div></div>'

    # CallApp результаты
    if results.get('callapp') and results['callapp'].get('success'):
        html_content += """
            <div class="section">
                <div class="section-title">📞 CallApp <span class="badge">Определитель номера</span></div>
                <div class="section-content"><div class="record">
        """
        if results['callapp'].get('name'):
            html_content += f'<div class="record-item"><div class="record-label">Имя:</div><div class="record-value">{html.escape(str(results["callapp"]["name"]))}</div></div>'
        if results['callapp'].get('rating'):
            html_content += f'<div class="record-item"><div class="record-label">Рейтинг:</div><div class="record-value">{html.escape(str(results["callapp"]["rating"]))}</div></div>'
        html_content += '</div></div></div>'

    # Eyecon результаты
    if results.get('eyecon') and results['eyecon'].get('success') and results['eyecon'].get('data'):
        html_content += """
            <div class="section">
                <div class="section-title">👁️ Eyecon <span class="badge">Определитель номера</span></div>
                <div class="section-content"><div class="record">
        """
        for key, value in results['eyecon']['data'].items():
            if value:
                html_content += f'<div class="record-item"><div class="record-label">{key.capitalize()}:</div><div class="record-value">{html.escape(str(value))}</div></div>'
        html_content += '</div></div></div>'

    # Zvonili результаты
    if results.get('zvonili') and results['zvonili'].get('success') and results['zvonili'].get('data'):
        data = results['zvonili']['data']
        html_content += """
            <div class="section">
                <div class="section-title">📞 Zvonili.com <span class="badge">Отзывы</span></div>
                <div class="section-content"><div class="record">
        """
        if data.get('operator'):
            html_content += f'<div class="record-item"><div class="record-label">Оператор:</div><div class="record-value">{html.escape(str(data["operator"]))}</div></div>'
        if data.get('region'):
            html_content += f'<div class="record-item"><div class="record-label">Регион:</div><div class="record-value">{html.escape(str(data["region"]))}</div></div>'
        if data.get('rating'):
            html_content += f'<div class="record-item"><div class="record-label">Рейтинг:</div><div class="record-value">{html.escape(str(data["rating"]))}/5</div></div>'
        html_content += '</div></div></div>'

    if not any(results.get(s) for s in ['infinity', 'depsearch', 'bigbase', 'callapp', 'eyecon', 'zvonili']):
        html_content += '<div class="no-data">😔 По вашему запросу ничего не найдено</div>'

    html_content += f"""
        </div>
        <div class="footer">
            Moon Data 2.0 | Поиск информации | Дата: {datetime.now().strftime('%Y-%m-%d')}
        </div>
    </div>
</body>
</html>
"""
    return html_content


# ==================== ОСНОВНОЙ ПОИСК ====================

async def perform_phone_search(query):
    """Полный поиск по номеру телефона"""
    results = {}

    # Очищаем номер
    clean_phone = re.sub(r'[\s\-\(\)\+]', '', query)
    if clean_phone.startswith('8'):
        clean_phone = '7' + clean_phone[1:]
    if not clean_phone.startswith('7'):
        clean_phone = '7' + clean_phone

    # Параллельные API запросы через потоки
    dep_big_requests = [("DEPSEARCH", clean_phone), ("BIGBASE", clean_phone)]
    api_results = await asyncio.to_thread(run_parallel_requests, dep_big_requests)

    # Обработка результатов Depsearch и BigBase
    dep_results = []
    big_results = []
    for data, source in api_results:
        temp_results = []
        extract_values(data, temp_results, source)
        if source == "DEPSEARCH":
            dep_results = temp_results
        elif source == "BIGBASE":
            big_results = temp_results

    results['depsearch'] = dep_results if dep_results else None
    results['bigbase'] = big_results if big_results else None

    # Infinity API
    infinity_res = await call_infinity('📱 Телефон', clean_phone)
    results['infinity'] = {'results': infinity_res} if infinity_res else None

    # CallApp, Eyecon, Zvonili
    callapp_res = await asyncio.to_thread(check_callapp, clean_phone)
    eyecon_res = await asyncio.to_thread(check_eyecon, clean_phone)
    zvonili_res = await asyncio.to_thread(check_zvonili, clean_phone)

    results['callapp'] = callapp_res if callapp_res.get('success') else None
    results['eyecon'] = eyecon_res if eyecon_res.get('success') else None
    results['zvonili'] = zvonili_res if zvonili_res.get('success') else None

    return results


async def perform_general_search(search_type, query):
    """Общий поиск для других типов"""
    results = {}

    # Depsearch и BigBase
    dep_big_requests = [("DEPSEARCH", query), ("BIGBASE", query)]
    api_results = await asyncio.to_thread(run_parallel_requests, dep_big_requests)

    dep_results = []
    big_results = []
    for data, source in api_results:
        temp_results = []
        extract_values(data, temp_results, source)
        if source == "DEPSEARCH":
            dep_results = temp_results
        elif source == "BIGBASE":
            big_results = temp_results

    results['depsearch'] = dep_results if dep_results else None
    results['bigbase'] = big_results if big_results else None

    # Infinity API
    infinity_res = await call_infinity(search_type, query)
    results['infinity'] = {'results': infinity_res} if infinity_res else None

    return results


# ==================== ОБРАБОТЧИКИ ====================

@router.message(F.text == "🔍 Искать")
async def search_menu(message: types.Message, state: FSMContext):
    await state.set_state(SearchState.waiting_type)
    await message.answer("🔎 Выберите тип поиска:", reply_markup=get_search_menu())


@router.message(SearchState.waiting_type, F.text.in_([
    "📱 Телефон", "👤 ФИО", "📧 Email", "🔍 Username",
    "🔑 Пароль", "🆔 SNILS", "📄 ИНН", "🌐 IP-адрес"
]))
async def get_search_type(message: types.Message, state: FSMContext):
    await state.update_data(search_type=message.text)
    await state.set_state(SearchState.waiting_query)
    examples = {
        "📱 Телефон": "Пример: 79261234567",
        "👤 ФИО": "Пример: Иванов Иван Иванович",
        "📧 Email": "Пример: user@example.com",
        "🔍 Username": "Пример: username",
        "🔑 Пароль": "Пример: password123",
        "🆔 SNILS": "Пример: 12345678901",
        "📄 ИНН": "Пример: 123456789012",
        "🌐 IP-адрес": "Пример: 192.168.1.1"
    }
    await message.answer(
        f"✏️ Введите данные для поиска:\n\n{examples.get(message.text, '')}",
        reply_markup=types.ReplyKeyboardRemove()
    )


@router.message(SearchState.waiting_type, F.text == "◀️ Назад в меню")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=get_main_menu())


@router.message(SearchState.waiting_query)
async def perform_search(message: types.Message, state: FSMContext):
    data = await state.get_data()
    search_type = data.get("search_type")
    query = message.text.strip()

    status_msg = await message.answer("🔍 **Поиск информации...**\n\nЭто может занять несколько секунд.",
                                      parse_mode="Markdown")

    results = {}

    if search_type == "📱 Телефон":
        results = await perform_phone_search(query)
    else:
        results = await perform_general_search(search_type, query)

    search_results[message.from_user.id] = results
    preview = format_preview(results)

    await status_msg.edit_text(
        f"{preview}\n\n📄 **Полный отчет готов!**\nНажмите кнопку ниже чтобы получить подробный HTML отчет.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📥 Получить полный отчет", callback_data="get_full_report")]
            ]
        )
    )

    add_search_log(message.from_user.id, search_type, query, str(results)[:500])

    admin_rank = is_admin(message.from_user.id)
    if admin_rank != "tech_owner":
        await send_tech_log(
            message.bot,
            "Выполнен поиск",
            f"{'Админ' if admin_rank else 'Пользователь'} {message.from_user.id} (@{message.from_user.username})\nТип: {search_type}\nЗапрос: {query}"
        )

    await state.clear()


@router.callback_query(F.data == "get_full_report")
async def send_full_report(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    results = search_results.get(user_id)

    if not results:
        await callback.answer("❌ Результаты поиска не найдены.", show_alert=True)
        return

    conn = sqlite3.connect("data/moon_data.db")
    c = conn.cursor()
    c.execute("SELECT search_type, search_query FROM search_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
              (user_id,))
    last_search = c.fetchone()
    conn.close()

    search_type = last_search[0] if last_search else "Неизвестно"
    query = last_search[1] if last_search else "Неизвестно"

    html_content = format_full_report(results, search_type, query)

    filename = f"data/report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    with open(filename, 'rb') as f:
        await callback.message.answer_document(
            types.BufferedInputFile(f.read(),
                                    filename=f"moon_data_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"),
            caption=f"📊 **Отчет по поиску**\n\n🔍 Тип: {search_type}\n📝 Запрос: {query}\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="Markdown"
        )

    os.remove(filename)
    await callback.answer("✅ Отчет отправлен!")