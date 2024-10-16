from flask import Flask, request, session, jsonify
from flask_cors import CORS
import datetime
import time
import requests
from api_utils import call_chatgpt, get_lat_long, get_restaurants, get_hotels, get_tour_info
from weather_utils import get_weather_data
from selenium_utils import select_day
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from config import load_env
import os

# Load environment variables
load_env()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key_here')

# Generate domestic travel prompt
def generate_domestic_prompt(start_date, end_date, companions, departure_city, transportation, style):
    prompt = (
        f"Recommend a specific city in South Korea for someone traveling with {companions}. "
        f"They will be departing from {departure_city}, "
        f"and will be traveling from {start_date} to {end_date}. "
        f"They prefer to use {transportation} and enjoy {style} style trips. "
        f"Only recommend a city, not a province or a large region like Gangwon-do. "
        f"The recommendation should be a city suitable for tourism, not a broad area."
        f"please print only city name in korean"
    )
    return prompt

# Domestic travel survey
@app.route('/api/domestic', methods=['POST'])
def domestic_survey():
    data = request.json
    session['start_date'] = data['start_date']
    session['end_date'] = data['end_date']
    session['companions'] = data['companions']
    session['departure_city'] = data['departure_city']
    session['transportation'] = data['transportation']
    session['style'] = data['style']

    # Generate prompt and get city recommendation
    prompt = generate_domestic_prompt(
        session['start_date'], session['end_date'], session['companions'],
        session['departure_city'], session['transportation'], session['style']
    )
    city_name = call_chatgpt(prompt)['choices'][0]['message']['content'].strip()
    session['city_name'] = city_name

    # Get latitude/longitude and tour information
    latitude, longitude = get_lat_long(city_name)
    if latitude and longitude:
        # Get nearby tourist spots using coordinates
        tour_info = get_tour_info(latitude, longitude)

        # Get nearby restaurants and hotels using city name
        api_key = os.getenv('GOOGLE_API_KEY')
        restaurants_data = get_restaurants(city_name, api_key)
        hotels_data = get_hotels(city_name, api_key)

        # Extract relevant restaurant and hotel information
        restaurants_info = [{'name': restaurant['name'], 'address': restaurant.get('formatted_address', '주소 없음')} for restaurant in restaurants_data['results']]
        hotels_info = [{'name': hotel['name'], 'address': hotel.get('formatted_address', '주소 없음')} for hotel in hotels_data['results']]

        # Return data as JSON response
        return jsonify({
            'city_name': city_name,
            'tour_info': tour_info,
            'restaurants': restaurants_info,
            'hotels': hotels_info
        }), 200
    else:
        return jsonify({'error': f"Unable to find latitude and longitude for city: {city_name}"}), 404

# International travel survey
@app.route('/api/international', methods=['POST'])
def international_survey():
    data = request.json
    session['start_date'] = data['start_date']
    session['end_date'] = data['end_date']
    session['gender'] = data['gender']
    session['companions'] = data['companions']
    session['age'] = data['age']
    session['preference'] = data['preference']
    session['budget'] = data['budget']
    session['departure_city'] = data['departure_city']

    start_date = session['start_date']
    end_date = session['end_date']
    departure_city = session['departure_city']

    # 날짜 변환
    start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    # 1년 전 날짜 계산
    start_date_last_year = start_date_obj - datetime.timedelta(days=365)
    end_date_last_year = end_date_obj - datetime.timedelta(days=365)

    # 타임스탬프로 변환
    start_timestamp = int(start_date_last_year.timestamp())
    end_timestamp = int(end_date_last_year.timestamp())

    # 여행지 추천을 위한 ChatGPT API 호출
    prompt = (
        f"You are a travel abroad assistant. Recommend a specific city that fits the following conditions, and only return the city name (no other information): "
        f"\n- Budget: {session['budget']} KRW for the entire trip."
        f"\n- Traveler: {session['age']}-year-old {session['gender']} traveling with {session['companions']}."
        f"\n- Travel dates: From {start_date} to {end_date}."
        f"\n- Preferences: The traveler prefers {session['preference']} type of destinations."
        f"\n- Departure city: {departure_city}."
        f"\nProvide the best possible city destination for this trip, considering the Departure city, budget, flight time and preferences. "
        f"Please print city in Korean and except the country name"
    )

    chatgpt_response = call_chatgpt(prompt)
    session['city_name'] = chatgpt_response['choices'][0]['message']['content'].strip()

    # 위도/경도 가져오기
    latitude, longitude = get_lat_long(session['city_name'])
    if latitude and longitude:
        try:
            # 날씨 데이터 가져오기
            weather_data = get_weather_data(latitude, longitude, start_timestamp, end_timestamp)

            # 식당 및 호텔 정보 가져오기
            api_key = os.getenv('GOOGLE_API_KEY')
            restaurants_data = get_restaurants(session['city_name'], api_key)
            hotels_data = get_hotels(session['city_name'], api_key)

            # 필요한 정보만 전달하기 위해 리스트로 구성
            restaurants_info = [{'name': restaurant['name'], 'address': restaurant.get('formatted_address', '주소 없음')} for restaurant in restaurants_data['results']]
            hotels_info = [{'name': hotel['name'], 'address': hotel.get('formatted_address', '주소 없음')} for hotel in hotels_data['results']]

            # JSON 응답 반환
            return jsonify({
                'city_name': session['city_name'],
                'weather_data': weather_data,
                'restaurants': restaurants_info,
                'hotels': hotels_info
            }), 200

        except requests.exceptions.HTTPError as err:
            return jsonify({'error': f"Error retrieving weather data: {err}"}), 500
    else:
        return jsonify({'error': "Unable to find location information."}), 404

# Booking flight using Selenium
@app.route('/api/booking_flight', methods=['POST'])
def booking_flight():
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    departure_city = data.get('departure_city')
    city_name = data.get('city_name')

    # Selenium WebDriver 시작
    driver = webdriver.Chrome()
    driver.get('https://flight.naver.com/')

    wait = WebDriverWait(driver, 10)  # WebDriverWait 설정

    # 날짜 형식 변환
    start_list = start_date.split("-")
    start_day = start_list[2]
    start_month = start_list[0] + "." + start_list[1] + "."

    end_list = end_date.split("-")
    end_day = end_list[2]
    end_month = end_list[0] + "." + end_list[1] + "."

    try:
        # 출발지 입력
        start_area_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/div/main/div[2]/div/div/div[2]/div[1]/button[1]')))
        driver.execute_script("arguments[0].click();", start_area_button)  # JavaScript로 클릭 강제 실행
        time.sleep(2)
        search_area = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'autocomplete_input__qbYlb')))
        search_area.send_keys(departure_city)
        time.sleep(2)
        finish_area = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'autocomplete_inner__xHAxv')))
        driver.execute_script("arguments[0].click();", finish_area)

        # 도착지 입력
        end_area_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/div/main/div[2]/div/div/div[2]/div[1]/button[2]')))
        driver.execute_script("arguments[0].click();", end_area_button)
        time.sleep(2)
        search_area = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'autocomplete_input__qbYlb')))
        search_area.send_keys(city_name)
        time.sleep(2)
        finish_area = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'autocomplete_inner__xHAxv')))
        driver.execute_script("arguments[0].click();", finish_area)

        # 날짜 선택
        day_area_start = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/div/main/div[2]/div/div/div[2]/div[2]/button[1]')))
        driver.execute_script("arguments[0].click();", day_area_start)
        time.sleep(8)
        select_day(driver, start_month, start_day)

        day_area_end = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/div/main/div[2]/div/div/div[2]/div[2]/button[2]')))
        driver.execute_script("arguments[0].click();", day_area_end)
        time.sleep(8)
        select_day(driver, end_month, end_day)

        # 검색 버튼 클릭
        element = driver.find_element(By.CSS_SELECTOR, "button.searchBox_search__dgK4Z")
        driver.execute_script("arguments[0].click();", element)

    except TimeoutException:
        return jsonify({'error': "Timeout while finding elements on the page."}), 500
    except Exception as e:
        return jsonify({'error': f"Unexpected error: {str(e)}"}), 500
    finally:
        driver.quit()

    return jsonify({'message': "Flight booking completed successfully."}), 200

if __name__ == '__main__':
    app.run(debug=True)