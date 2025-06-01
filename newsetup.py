import os
import time
import pandas as pd
import psycopg2
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

# Email Sending Function
def send_email(subject, body, to_email):
    from_email = os.getenv("FROM_EMAIL")
    from_password = os.getenv("FROM_PASSWORD")
    to_email = "samwel@kwolco.com"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, from_password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()

# Date Range for Scraping
start_date = '2025-05-28'
end_date = '2025-05-30'

# Configure WebDriver Options
options = webdriver.ChromeOptions()
options.add_argument("--incognito")  # Open in Incognito mode
options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent bot detection
options.add_argument("--start-maximized")  # Open browser in fullscreen

driver = webdriver.Chrome(options=options)

# Data Storage
info_list = []

try:
    current_date = start_date
    while current_date <= end_date:
        print(f"Scraping data for {current_date}...")  # Debugging line
        url = f'https://www.forebet.com/en/football-predictions/under-over-25-goals/{current_date}'
        driver.get(url)

        time.sleep(7)  # Allow page to load completely
        
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.rcnt.tr_0')))
        except:
            print(f"Page load failed for {current_date}. Skipping...")
            current_date = pd.to_datetime(current_date) + pd.Timedelta(days=1)
            current_date = current_date.strftime('%Y-%m-%d')
            continue

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        while True:
            time.sleep(2)
            all_elements = driver.find_elements(By.CSS_SELECTOR, '.rcnt.tr_0, .rcnt.tr_1, .rcnt.tr_2')
            
            for match_div in all_elements:
                league = match_div.find_element(By.XPATH, ".//div[1]/div[1]/span").text if match_div.find_elements(By.XPATH, ".//div[1]/div[1]/span") else None
                home_team = match_div.find_element(By.XPATH, ".//div[2]/div/a/span[1]/span").text if match_div.find_elements(By.XPATH, ".//div[2]/div/a/span[1]/span") else None
                away_team = match_div.find_element(By.XPATH, ".//div[2]/div/a/span[2]/span").text if match_div.find_elements(By.XPATH, ".//div[2]/div/a/span[2]/span") else None
                date = match_div.find_element(By.XPATH, ".//div[2]/div/a/time").text if match_div.find_elements(By.XPATH, ".//div[2]/div/a/time") else None
                avg_goals = match_div.find_element(By.XPATH, ".//div[6]").text if match_div.find_elements(By.XPATH, ".//div[6]") else None
                coefficient = match_div.find_element(By.XPATH, ".//div[8]").text if match_div.find_elements(By.XPATH, ".//div[8]") else None
                ft_score = match_div.find_element(By.XPATH, ".//div[10]/span[1]/b").text if match_div.find_elements(By.XPATH, ".//div[10]/span[1]/b") else None
                ht_score = match_div.find_element(By.XPATH, ".//div[10]/span[2]").text if match_div.find_elements(By.XPATH, ".//div[10]/span[2]") else None
                
                predict_item = {
                    'League': league,
                    'Home Team': home_team,
                    'Away Team': away_team,
                    'Date': date,
                    'Avg Goals': avg_goals,
                    'Coefficient': coefficient,
                    'FT Score': ft_score,
                    'HT Score': ht_score
                }
                info_list.append(predict_item)
            
            try:
                more_button = driver.find_element(By.XPATH, "//*[@id='mrows']/span")
                driver.execute_script("arguments[0].scrollIntoView();", more_button)
                more_button.click()
                time.sleep(2)
            except:
                break

        current_date = pd.to_datetime(current_date) + pd.Timedelta(days=1)
        current_date = current_date.strftime('%Y-%m-%d')
    
    print("All dates processed successfully!")
    df = pd.DataFrame(info_list)
    df.to_excel('soccer_predictions.xlsx', index=False)

except Exception as e:
    print("Error:", e)

finally:
    driver.quit()
