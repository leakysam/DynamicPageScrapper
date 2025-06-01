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

def send_email(subject, body, to_email):
    from_email = os.getenv("FROM_EMAIL")
    from_password = os.getenv("FROM_PASSWORD")
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, from_password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()

# Scraping date range
start_date = '2025-05-25'
end_date = '2025-05-31'

# Set up Selenium with incognito and anti-bot features
options = webdriver.ChromeOptions()
options.add_argument("--incognito")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# PostgreSQL setup
conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT')
)
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS forebet (
        id SERIAL PRIMARY KEY,
        league TEXT,
        home_team TEXT,
        away_team TEXT,
        date TEXT,
        average_goals TEXT,
        coefficient TEXT,
        ft_score TEXT,
        ht_score TEXT,
        CONSTRAINT unique_match UNIQUE (league, home_team, away_team, date)
    )
''')
conn.commit()

info_list = []

try:
    current_date = start_date
    while current_date <= end_date:
        print(f"Scraping data for {current_date}")
        url = f'https://www.forebet.com/en/football-predictions/under-over-25-goals/{current_date}'
        driver.get(url)
        time.sleep(7)

        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.rcnt.tr_0')))
        except:
            print(f"Page load failed for {current_date}. Skipping...")
            current_date = pd.to_datetime(current_date) + pd.Timedelta(days=1)
            current_date = current_date.strftime('%Y-%m-%d')
            continue

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

                # Clean and normalize
                avg_goals = None if not avg_goals or avg_goals.strip() == '-' else avg_goals
                coefficient = None if not coefficient or coefficient.strip() == '-' else coefficient
                ft_score = None if not ft_score or ft_score.strip() in ('-', '') else ft_score
                ht_score = None if not ht_score or ht_score.strip() in ('-', '') else ht_score

                if not avg_goals or not coefficient or not ft_score:
                    continue  # Skip incomplete rows

                # Insert to DB
                try:
                    cursor.execute('''
                        INSERT INTO forebet (league, home_team, away_team, date, average_goals, coefficient, ft_score, ht_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (league, home_team, away_team, date) DO NOTHING;
                    ''', (league, home_team, away_team, date, avg_goals, coefficient, ft_score, ht_score))
                    conn.commit()
                except Exception as e:
                    print("Insert failed:", e)
                    continue

                # Email condition check
                try:
                    ag = float(avg_goals)
                    coef = float(coefficient)
                    if ag == 1.05 or (ag == 1.5 and coef == 1.5):
                        email_body = f"League: {league}\nHome Team: {home_team}\nAway Team: {away_team}\nDate: {date}\nAverage Goals: {avg_goals}\nCoefficient: {coefficient}\nFT Score: {ft_score}\nHT Score: {ht_score}"
                        send_email("Match Condition Met", email_body, "samwel@kwolco.com")
                except ValueError:
                    continue

            try:
                more_button = driver.find_element(By.XPATH, "//*[@id='mrows']/span")
                driver.execute_script("arguments[0].scrollIntoView();", more_button)
                more_button.click()
                time.sleep(2)
            except:
                break

        current_date = pd.to_datetime(current_date) + pd.Timedelta(days=1)
        current_date = current_date.strftime('%Y-%m-%d')

except Exception as e:
    print("Error during scraping:", e)

finally:
    cursor.close()
    conn.close()
    driver.quit()
