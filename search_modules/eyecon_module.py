import requests
import re


def check_eyecon(phone):
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
        headers = {"User-Agent": "Mozilla/5.0", "e-auth-v": "e1", "e-auth": "d9889e1c-521c-4ded-9b15-f64bb069148b",
                   "e-auth-c": "46", "e-auth-k": "PgdtSBeR0MumR7fO"}
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