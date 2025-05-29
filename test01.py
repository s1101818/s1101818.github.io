from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

from selenium.webdriver.support.ui import Select #給下拉選擇出發時間用
import csv#給後面的scV輸出用
import os

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
        # 使用者輸入四個查詢參數
        startstation = input("請輸入出發站（例如：台南）：").strip() #.strip()清除空白和換行 以免輸入錯誤
        endstation = input("請輸入到達站（例如：台北）：").strip()
        date = input("請輸入乘車日期（格式：YYYYMMDD，例如：20250530）：").strip()
        departure_time = input("請輸入出發時間（格式：HH:MM，例如：07:30）：").strip()
        # 輸入車站
        enhanced_input("startStation", startstation)
        time.sleep(random.uniform(0.5, 1.5))
        enhanced_input("endStation", endstation)

        # 日期輸入
        date_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "rideDate"))
        )
        date_field.send_keys(Keys.CONTROL + "a")
        date_field.send_keys(date)
        # 輸入出發時間        
        start_time_select = Select(WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "startTime"))
        ))
        start_time_select.select_by_value(departure_time)

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
        # 建立 csv 子目錄（如果不存在）
        os.makedirs("csv", exist_ok=True)
        # 設定完整路徑與檔名
        # 設定基本檔名
        base_filename = f"{date}_{startstation}_to_{endstation}"

        # 獲得不重複檔案名
        csv_path = get_unique_filename("csv", base_filename)
        # 存成 CSV 檔案
        with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=["車次", "出發時間", "抵達時間", "行駛時間", "票價"])
            writer.writeheader()
            writer.writerows(timetable)
        print(f"已將查詢結果儲存為：{os.path.basename(csv_path)}")
        return timetable

    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        driver.save_screenshot("error.png")
        return None
    finally:
        driver.quit()
#存檔覆蓋問題
def get_unique_filename(folder, base_name):
    i = 1
    filename = f"{base_name}.csv"
    path = os.path.join(folder, filename)
    while os.path.exists(path):
        filename = f"{base_name}_{i}.csv"
        path = os.path.join(folder, filename)
        i += 1
    return path

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

