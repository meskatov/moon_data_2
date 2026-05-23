import requests
import re
from bs4 import BeautifulSoup


def check_zvonili(phone_number):
    try:
        phone_number = re.sub(r'[\s\-\(\)\+]', '', phone_number)
        if phone_number.startswith('8'):
            phone_number = '7' + phone_number[1:]
        if not phone_number.startswith('7'):
            phone_number = '7' + phone_number

        phone_for_url = phone_number[1:] if phone_number.startswith('7') else phone_number
        url = f"https://zvonili.com/phone/{phone_for_url}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

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