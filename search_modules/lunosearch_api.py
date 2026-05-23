import aiohttp
from config import LUNOSEARCH_URL, LUNOSEARCH_TOKEN

async def search_lunosearch(query):
    try:
        headers = {'Authorization': LUNOSEARCH_TOKEN}
        async with aiohttp.ClientSession() as session:
            async with session.post(LUNOSEARCH_URL, json={'query': query}, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except:
        return None