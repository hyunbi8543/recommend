
import os
import requests
from config import get_env_var

# Shared OpenAI ChatGPT API Call
def call_chatgpt(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Google Maps API: Latitude/Longitude Lookup
def get_lat_long(city_name):
    api_key = os.getenv('GOOGLE_API_KEY')
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {'address': city_name, 'key': api_key}
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()
    if data['results']:
        latitude = data['results'][0]['geometry']['location']['lat']
        longitude = data['results'][0]['geometry']['location']['lng']
        return latitude, longitude
    else:
        return None, None

# Google Places API: Restaurant and Hotel Lookup
def get_restaurants(city_name, api_key):
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
    query = f"restaurants in {city_name}"
    response = requests.get(base_url + 'query=' + query + '&key=' + api_key + '&language=ko')
    response.raise_for_status()
    return response.json()

def get_hotels(city_name, api_key):
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
    query = f"hotels in {city_name}"
    response = requests.get(base_url + 'query=' + query + '&key=' + api_key + '&language=ko')
    response.raise_for_status()
    return response.json()

def get_tour_info(latitude, longitude, radius=1000, content_type_id=12):
    api_key = os.getenv('TOUR_API_KEY')
    url = f"http://apis.data.go.kr/B551011/KorService1/locationBasedList1?serviceKey={api_key}&numOfRows=10&pageNo=1&MobileOS=ETC&MobileApp=AppTest&mapX={longitude}&mapY={latitude}&radius=7000&contentTypeId={content_type_id}&_type=json"

    response = requests.get(url)

    if response.status_code == 200:
        try:
            if response.headers.get('Content-Type') == 'application/json':
                data = response.json()

                # 검증
                response_data = data.get('response')
                if isinstance(response_data, dict):
                    body = response_data.get('body')
                    if isinstance(body, dict):
                        items = body.get('items')
                        print("Actual 'items' content:", items)  # items의 실제 내용을 출력
                        if isinstance(items, dict):
                            return items.get('item', [])
                        elif isinstance(items, list):
                            # 'items'가 리스트일 경우, 그대로 반환
                            return items
                        else:
                            print("Error: 'items' is not a dictionary or list. Actual content:", items)
                            return []
                    else:
                        print("Error: 'body' is not a dictionary. Actual content:", body)
                        return []
                else:
                    print("Error: 'response' is not a dictionary. Actual content:", response_data)
                    return []
            else:
                print("Error: Response is not in JSON format.")
                print("Raw response content:", response.text)
                return []
        except ValueError:
            print("Error: Failed to parse JSON. Raw response content:")
            print(response.text)
            return []
    else:
        print(f"Tour API Error: {response.status_code}, {response.text}")
        return []


