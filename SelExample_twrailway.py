from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

def extract_td_content(td_element):
    """解析包含 <ul><li> 的複雜表格格內容"""
    try:
        # 先嘗試抓取 ul 列表內容
        ul = td_element.find_element(By.TAG_NAME, 'ul')
        items = [li.text.strip() for li in ul.find_elements(By.TAG_NAME, 'li')]
        #print(items)
        #print('.',end='')
        return ' / '.join(items)
    except:
        # 沒有 ul 則直接抓取文字
        #print(td_element.text)
        #print('.',end='')
        return td_element.text.strip()

def get_timetable():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(
        service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get("https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime")

        # 強化輸入函數
        def enhanced_input(field_id, station_name):
            input_field = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, field_id))
            )
            input_field.send_keys(Keys.CONTROL + "a")
            input_field.send_keys(Keys.BACKSPACE)
            
            # 模擬人類輸入速度
            for char in station_name:
                input_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            # 雙重定位策略
            try:
                WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//ul[contains(@class,'MuiAutocomplete-listbox')]/li[1]")
                    )
                ).click()
            except:
                input_field.send_keys(Keys.ARROW_DOWN, Keys.ENTER)

        # 輸入車站
        enhanced_input("startStation", "桃園")
        time.sleep(random.uniform(0.5, 1.5))
        enhanced_input("endStation", "高雄")

        # 日期輸入
        date_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "rideDate"))
        )
        date_field.send_keys(Keys.CONTROL + "a")
        date_field.send_keys("20250420")

        # 提交查詢
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']"))
        ).click()

        # 關鍵等待機制
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".itinerary-controls"))
        )
        time.sleep(2)  # 緩衝時間確保數據完全渲染

        # 解析表格結構
        print("讀取表格中")
        table = driver.find_element(By.CSS_SELECTOR, ".itinerary-controls")
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")

        timetable = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 8:
                timetable.append({
                    "車次": extract_td_content(cols[0]),
                    "出發時間": extract_td_content(cols[1]),
                    "抵達時間": extract_td_content(cols[2]),
                    "行駛時間": extract_td_content(cols[3]),
                    "票價": extract_td_content(cols[6])
                })
            print('.',end='')
        print()
        return timetable

    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        driver.save_screenshot("error.png")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    result = get_timetable()
    if result:
        print(f"成功獲取 {len(result)} 班次資料：")
        for idx, train in enumerate(result[:5], 1):
            print(f"{idx}. {train['車次']} ")
            print(f"   出發: {train['出發時間']} → 抵達: {train['抵達時間']}")
            print(f"   行駛時間: {train['行駛時間']} | 票價: {train['票價']}\n")
    else:
        print("查無資料")

