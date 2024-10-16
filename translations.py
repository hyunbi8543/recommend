
# 영어에서 한국어로 날씨 설명을 변환하는 함수
def translate_weather_description(description):
    translations = {
        "clear sky": "맑음",
        "few clouds": "약간 구름",
        "scattered clouds": "구름 조금",
        "broken clouds": "구름 많음",
        "shower rain": "소나기",
        "rain": "비",
        "light rain": "가벼운 비",
        "overcast clouds": "흐림",
        "thunderstorm": "천둥번개",
        "snow": "눈",
        "mist": "안개"
    }
    return translations.get(description, description)
