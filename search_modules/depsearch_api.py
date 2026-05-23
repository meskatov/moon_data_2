import aiohttp
from config import DEPSEARCH_TOKEN, DEPSEARCH_BASE_URL

async def search_depsearch(query):
    try:
        headers = {'Authorization': f'Bearer {DEPSEARCH_TOKEN}'}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DEPSEARCH_BASE_URL}search", params={'q': query}, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except:
        return None