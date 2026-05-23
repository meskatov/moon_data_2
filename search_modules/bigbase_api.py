import aiohttp
from config import BIGBASE_URL, BIGBASE_TOKEN

async def search_bigbase(query):
    try:
        headers = {'Authorization': BIGBASE_TOKEN}
        async with aiohttp.ClientSession() as session:
            async with session.post(BIGBASE_URL, json={'query': query}, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except:
        return None