import aiohttp
import re
from config import INFINITY_API_URL, INFINITY_TOKEN


async def search_infinity(search_type, query):
    """
    Поиск через Infinity API
    """
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