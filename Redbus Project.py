import time
import pandas as pd
import pymysql
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize the Chrome driver and webdriver wait
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

# Function to scrape route links and names
def scrape_route_links():
    driver.get('https://www.redbus.in/online-booking/jksrtc')
    driver.maximize_window()

    links = []
    routes = []

    def scrape_data():
        route_elements = driver.find_elements(By.CSS_SELECTOR, 'div.route_link div.route_details a.route')
        for element in route_elements:
            links.append(element.get_attribute('href'))
            routes.append(element.get_attribute('title'))

    scrape_data()

    current_page = 1
    while True:
        try:
            next_button = driver.find_element(By.XPATH, f'//div[contains(@class, "DC_117_pageTabs") and text()="{current_page + 1}"]')
            wait.until(EC.element_to_be_clickable((By.XPATH, f'//div[contains(@class, "DC_117_pageTabs") and text()="{current_page + 1}"]')))
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(5)
            current_page += 1
            scrape_data()
            print(f'Navigated to page {current_page} and scraped data.')
        except Exception as e:
            print(f'No more pages or an error occurred: {e}')
            break

    data = {'Link': links, 'Route': routes}
    df = pd.DataFrame(data)
    csv_path = 'JKSRTC_routes_and_links.csv'
    df.to_csv(csv_path, index=False)
    print(df)

    driver.quit()

# Function to scrape bus details
def scrape_bus_details():
    driver = webdriver.Chrome()
    driver.get('https://www.redbus.in/bus-tickets/jammu-to-amritsar')
    driver.maximize_window()
    
    def incremental_scroll():
        scroll_pause_time = 2
        screen_height = driver.execute_script("return window.innerHeight;")
        current_position = 0
        while True:
            driver.execute_script(f"window.scrollBy(0, {screen_height});")
            time.sleep(scroll_pause_time)
            new_position = driver.execute_script("return window.scrollY;")
            if new_position == current_position:
                break
            current_position = new_position

    incremental_scroll()
    
    def expand_hidden_buses():
        try:
            while True:
                view_buttons = driver.find_elements(By.XPATH, "//div[contains(@class, 'button') and contains(text(), 'View Buses')]")
                if not view_buttons:
                    break
                for button in view_buttons:
                    try:
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(1)
                    except Exception as e:
                        print(f"Error clicking a button: {e}")
        except Exception as e:
            print(f"Error while clicking 'View Buses' buttons: {e}")

    expand_hidden_buses()

    def scrape_data():
        results = []
        try:
            bus_names = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='travels lh-24 f-bold d-color']")))
            bus_types = driver.find_elements(By.XPATH, "//div[@class='bus-type f-12 m-top-16 l-color evBus']")
            departing_times = driver.find_elements(By.XPATH, "//div[@class='dp-time f-19 d-color f-bold']")
            reaching_times = driver.find_elements(By.XPATH, "//div[@class='bp-time f-19 d-color disp-Inline']")
            star_ratings = driver.find_elements(By.XPATH, "//div[@class='rating-sec lh-24']//span[contains(text(),'.')]")
            prices = driver.find_elements(By.XPATH, "//span[@class='f-19 f-bold']")
            seat_availabilities = driver.find_elements(By.XPATH, "//div[@class='seat-left m-top-30']")

            for index in range(len(bus_names)):
                try:
                    results.append({
                        'bus_name': bus_names[index].text,
                        'bus_type': bus_types[index].text if index < len(bus_types) else 'N/A',
                        'departing_time': departing_times[index].text if index < len(departing_times) else 'N/A',
                        'reaching_time': reaching_times[index].text if index < len(reaching_times) else 'N/A',
                        'star_rating': star_ratings[index].text if index < len(star_ratings) else 'N/A',
                        'price': prices[index].text if index < len(prices) else 'N/A',
                        'seat_availability': seat_availabilities[index].text if index < len(seat_availabilities) else 'N/A'
                    })
                except IndexError:
                    continue

        except Exception as e:
            print(f"Error: {e}")
        
        return results

    results = scrape_data()
    df = pd.DataFrame(results)
    csv_path = 'Jammu_to_Amritsar.csv'
    df.to_csv(csv_path, index=False)
    print(df)

    driver.quit()

# Function to insert data into MySQL database
def insert_data_into_mysql():
    conn = pymysql.connect(
        host='127.0.0.1',
        user='root',
        passwd='dhinesh',
        db='redbus'
    )
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bus_info (
            id INT AUTO_INCREMENT PRIMARY KEY,
            route_name TEXT,
            route_link TEXT,
            busname TEXT,
            bustype TEXT,
            departing_time DATETIME,
            duration TEXT,
            reaching_time DATETIME,
            star_rating FLOAT,
            price DECIMAL(10, 2),
            seat_available INT
        )
    ''')

    csv_file_path = 'C:/Users/ELCOT/Downloads/bus_info.csv'  # Update with your CSV file path
    df = pd.read_csv(csv_file_path)

    default_date = datetime.now().strftime('%Y-%m-%d')

    def clean_datetime(date_str):
        try:
            if '-' in date_str and ':' in date_str:
                return datetime.strptime(date_str, '%d-%m-%Y %H:%M').strftime('%Y-%m-%d %H:%M:%S')
            elif ':' in date_str:
                return f"{default_date} {date_str}:00"
            else:
                return datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y-%m-%d 00:00:00')
        except ValueError:
            return None

    bus_info = [
        (
            row['route_name'], row['route_link'], row['busname'], row['bustype'],
            clean_datetime(row['departing_time']),
            row['duration'],
            clean_datetime(row['reaching_time']),
            row['star_rating'], row['price'], row['seat_available']
        )
        for _, row in df.iterrows()
    ]

    bus_info = [detail for detail in bus_info if detail[4] and detail[6]]

    try:
        for detail in bus_info:
            cursor.execute('''
                INSERT INTO bus_info (
                    route_name, route_link, busname, bustype, departing_time,
                    duration, reaching_time, star_rating, price, seat_available
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', detail)
        conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Run functions
scrape_route_links()
scrape_bus_details()
insert_data_into_mysql()
