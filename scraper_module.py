# scraper_module.py

import os
import time
import base64
import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup


USERNAME = os.getenv("OPTIMA_USERNAME", "HOCC5T177")
PASSWORD = os.getenv("OPTIMA_PASSWORD", "9354454550")

PAGE_LOAD_TIMEOUT = 60
ELEMENT_TIMEOUT = 15


def get_chrome_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(
        ChromeDriverManager().install(),
        options=chrome_options
    )
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


def login_to_platform(driver: webdriver.Chrome) -> None:
    login_url = "https://optima.qeahub.com/"
    driver.get(login_url)
    WebDriverWait(driver, ELEMENT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, "txtUserID"))
    )
    driver.find_element(By.ID, "txtUserID").send_keys(USERNAME)
    driver.find_element(By.ID, "txtPassword").send_keys(PASSWORD)
    driver.find_element(By.ID, "btnLogin").click()
    WebDriverWait(driver, ELEMENT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Dashboard')]"))
    )


def navigate_to_chapter(driver: webdriver.Chrome,
                        area_text: str,
                        level: int,
                        chapter_name: str,
                        difficulty: str) -> None:
    area_xpath = f"//div[text()='{area_text}']"
    WebDriverWait(driver, ELEMENT_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, area_xpath))
    )
    driver.find_element(By.XPATH, area_xpath).click()

    level_xpath = f"//button[contains(text(), 'Level {level}')]"
    WebDriverWait(driver, ELEMENT_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, level_xpath))
    )
    driver.find_element(By.XPATH, level_xpath).click()

    chapter_xpath = f"//div[text()='{chapter_name}']"
    WebDriverWait(driver, ELEMENT_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, chapter_xpath))
    )
    driver.find_element(By.XPATH, chapter_xpath).click()

    difficulty_xpath = f"//label[text()='{difficulty}']"
    WebDriverWait(driver, ELEMENT_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, difficulty_xpath))
    )
    driver.find_element(By.XPATH, difficulty_xpath).click()


def count_questions_on_page(driver: webdriver.Chrome) -> int:
    try:
        WebDriverWait(driver, ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "questionHolder"))
        )
        question_elements = driver.find_elements(By.XPATH, "//div[@id='questionHolder']/div")
        return len(question_elements)
    except TimeoutException:
        return 0


def scroll_to_question(driver: webdriver.Chrome, q_index: int) -> None:
    try:
        q_elem = driver.find_element(By.XPATH, f"//div[@id='questionHolder']/div[{q_index}]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", q_elem)
        time.sleep(0.3)
    except NoSuchElementException:
        pass


def clean_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    for span in soup.find_all("span"):
        span.unwrap()
    text = soup.get_text(separator=" ", strip=True)
    return text


def extract_and_encode_images(driver: webdriver.Chrome, element) -> str:
    try:
        img_elem = element.find_element(By.TAG_NAME, "img")
        src = img_elem.get_attribute("src")
        if src.startswith("data:image/"):
            return src
        else:
            script = """
                const xhr = new XMLHttpRequest();
                xhr.open('GET', arguments[0], false);
                xhr.responseType = 'arraybuffer';
                xhr.send(null);
                const u8 = new Uint8Array(xhr.response);
                let binary = '';
                for (let i = 0; i < u8.byteLength; i++) {
                    binary += String.fromCharCode(u8[i]);
                }
                return btoa(binary);
            """
            base64_str = driver.execute_script(script, src)
            return f"data:image/png;base64,{base64_str}"
    except Exception:
        return None


def get_correct_option_index(driver: webdriver.Chrome, q_index: int) -> str:
    for opt in ["A", "B", "C", "D"]:
        try:
            opt_elem = driver.find_element(By.XPATH, f"//div[@id='ch{opt}']")
            weight = opt_elem.value_of_css_property("font-weight")
            if weight and ("700" in weight or "bold" in weight.lower()):
                return opt
        except NoSuchElementException:
            continue
    try:
        idx = driver.execute_script("return window.ansid || '';")
        if isinstance(idx, (int, float)) and 1 <= idx <= 4:
            return ["", "A", "B", "C", "D"][int(idx)]
        elif isinstance(idx, str) and idx in ["A", "B", "C", "D"]:
            return idx
    except Exception:
        pass
    return ""


def parse_current_q(driver: webdriver.Chrome, q_index: int) -> dict:
    result = {
        "question_number": q_index,
        "question": "",
        "options": {},
        "answer": "",
        "images": []
    }
    try:
        q_xpath = f"//div[@id='questionHolder']/div[{q_index}]/div[@class='questionText']"
        q_elem = driver.find_element(By.XPATH, q_xpath)
        raw_q_html = q_elem.get_attribute("innerHTML")
        result["question"] = clean_html(raw_q_html)
        img_b64 = extract_and_encode_images(driver, q_elem)
        if img_b64:
            result["images"].append({"context": "question", "data": img_b64})
    except NoSuchElementException:
        result["question"] = ""
    opts = {}
    for letter in ["A", "B", "C", "D"]:
        try:
            opt_xpath = f"{q_xpath}/following-sibling::div[@class='options']/div[@data-opt='{letter}']"
            opt_elem = driver.find_element(By.XPATH, opt_xpath)
            raw_opt_html = opt_elem.get_attribute("innerHTML")
            opts[letter] = clean_html(raw_opt_html)
            img_b64 = extract_and_encode_images(driver, opt_elem)
            if img_b64:
                result["images"].append({"context": f"option_{letter}", "data": img_b64})
        except NoSuchElementException:
            opts[letter] = ""
    result["options"] = opts
    answer = get_correct_option_index(driver, q_index)
    result["answer"] = answer
    return result


def run_scraper_and_return_dict(area_text: str,
                                level: int,
                                chapter_name: str,
                                difficulty: str) -> list:
    driver = get_chrome_driver()
    try:
        login_to_platform(driver)
        navigate_to_chapter(driver, area_text, level, chapter_name, difficulty)
        time.sleep(1.5)
        total_qs = count_questions_on_page(driver)
        results = []
        for idx in range(1, total_qs + 1):
            scroll_to_question(driver, idx)
            q_dict = parse_current_q(driver, idx)
            results.append(q_dict)
            time.sleep(0.2)
        return results
    finally:
        driver.quit()
