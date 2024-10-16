import requests
import datetime
import statistics
from collections import defaultdict
from config import get_env_var
from translations import translate_weather_description
import os

# OpenWeather API: 일별 날씨 데이터로 변환
def get_weather_data(latitude, longitude, start_timestamp, end_timestamp):
    api_key = os.getenv('OPENWEATHER_API_KEY')
    url = "https://history.openweathermap.org/data/2.5/history/city"
    params = {
        'lat': latitude,
        'lon': longitude,
        'type': 'hour',
        'start': start_timestamp,
        'end': end_timestamp,
        'appid': api_key,
        'lang': 'kr'  # API 응답을 한국어로 설정
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    raw_data = response.json()

    # 날짜별로 데이터를 그룹화할 딕셔너리
    daily_weather = defaultdict(list)

    # 시간별 데이터를 받아와서 날짜별로 그룹화
    for entry in raw_data.get('list', []):
        dt = entry['dt']
        date = datetime.datetime.utcfromtimestamp(dt).strftime('%Y-%m-%d')  # 날짜만 추출

        main_info = entry['main']
        temperature = main_info.get('temp')
        feels_like = main_info.get('feels_like')
        humidity = main_info.get('humidity')
        rain = entry.get('rain', {}).get('1h', 0)  # 강수량, 없으면 0으로
        weather_description = entry['weather'][0]['description']

        # 영어 날씨 설명을 한국어로 변환
        weather_description_korean = translate_weather_description(weather_description)

        # 해당 날짜에 관련된 정보를 리스트로 추가
        daily_weather[date].append({
            'temperature': temperature,
            'feels_like': feels_like,
            'humidity': humidity,
            'rain': rain,
            'weather_description': weather_description_korean  # 한국어로 변환된 날씨 설명 사용
        })

    # 각 날짜별로 데이터를 요약 (평균 온도, 총 강수량, 가장 빈번한 날씨 상태)
    weather_info = []
    for date, entries in daily_weather.items():
        avg_temp = statistics.mean([entry['temperature'] for entry in entries])  # 평균 온도
        avg_feels_like = statistics.mean([entry['feels_like'] for entry in entries])  # 평균 체감 온도
        avg_humidity = statistics.mean([entry['humidity'] for entry in entries])  # 평균 습도
        total_rain = sum(entry['rain'] for entry in entries)  # 총 강수량
        weather_description = statistics.mode([entry['weather_description'] for entry in entries])  # 가장 빈번한 날씨 상태

        # 일별 요약 데이터를 추가
        weather_info.append({
            'date': date,
            'temperature': avg_temp,
            'feels_like': avg_feels_like,
            'humidity': avg_humidity,
            'rain': total_rain,
            'weather_description': weather_description
        })

    return weather_info
