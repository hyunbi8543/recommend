from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time


# Selenium 날짜 선택 함수
def select_day(driver, input_month, input_day):
    all_day = driver.find_elements(By.CLASS_NAME,'sc-kpDqfm.ljuuWQ.month')
    month_day = []
    for i in all_day:
        month = i.find_elements(By.CLASS_NAME,'sc-dAlyuH.cKxEnD')
        for j in month:
            if j.text == input_month:
                month_day = i.find_elements(By.CSS_SELECTOR,'.day b')
    for i in month_day:
        if i.text == input_day:
            i.click()
            break

# 드라이버 설정 함수 정의
def setup_driver():
    # ChromeDriver 설정
    chrome_options = Options()
    chrome_options.add_argument("--disable-popup-blocking")  # 팝업 차단 비활성화
    chrome_options.add_argument("--disable-gpu")  # GPU 사용 안 함
    chrome_options.add_argument("--no-sandbox")  # 리눅스 환경에서 권한 문제 방지
    # chrome_options.add_argument("--headless")  # 헤드리스 모드 (브라우저 창을 띄우지 않고 실행) 필요할 때만 주석 해제

    # WebDriver 초기화
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    return driver