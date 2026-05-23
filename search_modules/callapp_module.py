import requests
import re


def check_callapp(phone_number):
    try:
        phone_number = re.sub(r'[\s\-\(\)\+]', '', phone_number)
        if phone_number.startswith('8'):
            phone_number = '7' + phone_number[1:]
        if not phone_number.startswith('7'):
            phone_number = '7' + phone_number

        params = {"cpn": f"+{phone_number}", "myp": "fb.1122543675802814", "ibs": "3", "tk": "0017356813", "cvc": 2038}
        url = "https://s.callapp.com/callapp-server/csrch"

        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, params=params, timeout=5)
        except:
            response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            return {'success': True, 'name': data.get('name'), 'rating': data.get('rating'),
                    'reviews': data.get('reviews')}
        return {'success': False}
    except:
        return {'success': False}