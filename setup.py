import os
import time
import pandas as pd
import psycopg2
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

load_dotenv()

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

# Define the range of dates
start_date = '2024-03-18'
end_date = '2024-03-22'  # Example end date, you can adjust as needed

# Initialize WebDriver
driver = webdriver.Chrome()

# Initialize an empty list to store all scraped data
info_list = []

try:
    # Loop through each date in the range
    current_date = start_date
    while current_date <= end_date:
        # Construct the URL for the current date
        url = f'https://www.forebet.com/en/football-predictions/under-over-25-goals/{current_date}'
        driver.get(url)

        while True:
            # Wait for page to load
            time.sleep(2)  # Adjust as needed

            # Scraping logic
            all_elements = driver.find_elements(By.CSS_SELECTOR, '.rcnt.tr_0, .rcnt.tr_1, .rcnt.tr_2')

            for match_div in all_elements:
                league = match_div.find_element(By.XPATH, ".//div[1]/div[1]/span").text if match_div.find_elements(By.XPATH, ".//div[1]/div[1]/span") else None
                home_team = match_div.find_element(By.XPATH, ".//div[2]/div/a/span[1]/span").text if match_div.find_elements(By.XPATH, ".//div[2]/div/a/span[1]/span") else None
                away_team = match_div.find_element(By.XPATH, ".//div[2]/div/a/span[2]/span").text if match_div.find_elements(By.XPATH, ".//div[2]/div/a/span[2]/span") else None
                date = match_div.find_element(By.XPATH, ".//div[2]/div/a/time").text if match_div.find_elements(By.XPATH, ".//div[2]/div/a/time") else None
                avg_goals = match_div.find_element(By.XPATH, ".//div[6]").text if match_div.find_elements(By.XPATH, ".//div[6]") else None
                coefficient = match_div.find_element(By.XPATH, ".//div[8]").text if match_div.find_elements(By.XPATH, ".//div[8]") else None
                ft_score = match_div.find_element(By.XPATH, ".//div[10]/span[1]/b").text if match_div.find_elements(By.XPATH, ".//div[10]/span[1]/b") else None

                ht_score_element = match_div.find_elements(By.XPATH, ".//div[10]/span[2]")
                ht_score = ht_score_element[0].text if ht_score_element else None

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

            # Locate the "More" button and click it
            try:
                more_button = driver.find_element(By.XPATH, "//*[@id='mrows']/span")
                driver.execute_script("arguments[0].scrollIntoView();", more_button)  # Scroll to the button before clicking
                more_button.click()
                time.sleep(2)  # Add a delay to wait for the new content to load
            except:
                break  # Break the loop if there are no more "More" buttons to click

        # Move to the next date
        current_date = pd.to_datetime(current_date) + pd.Timedelta(days=1)
        current_date = current_date.strftime('%Y-%m-%d')

    # Create DataFrame
    df = pd.DataFrame(info_list)

    # Save DataFrame to Excel
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        df.to_excel('soccer_predictions.xlsx', index=False)

    # Database connection and operations
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forebet (
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            date TEXT,
            average_goals TEXT,
            coefficient TEXT,
            ft_score TEXT,
            ht_score TEXT
        )
    ''')

    # Insert data into the table
    for index, row in df.iterrows():
        cursor.execute('''
            INSERT INTO forebet (league, home_team, away_team, date, average_goals, coefficient, ft_score, ht_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (row['League'], row['Home Team'], row['Away Team'], row['Date'], row['Avg Goals'], row['Coefficient'], row['FT Score'], row['HT Score']))

    conn.commit()

    # After database insertion, check and send email
    # After database insertion, check and send email
    for index, row in df.iterrows():
        try:
            avg_goals_str = row['Avg Goals']  # Get the value of 'Avg Goals' as a string
            if avg_goals_str is not None:  # Check if the value is not None
                avg_goals = float(avg_goals_str)  # Convert the string to float

                coefficient_value_str = row['Coefficient']  # Get the value of 'Coefficient' as a string
                if coefficient_value_str is not None:  # Check if the value is not None
                    coefficient_value = float(coefficient_value_str)  # Convert the string to float

                    if avg_goals == 1.05 or (avg_goals == 1.50 and coefficient_value == 1.50):
                        email_body = f"League: {row['League']}\nHome Team: {row['Home Team']}\nAway Team: {row['Away Team']}\nDate: {row['Date']}\nAverage Goals: {avg_goals_str}\nCoefficient: {coefficient_value_str}\nFT Score: {row['FT Score']}\nHT Score: {row['HT Score']}"
                        send_email("Match Condition Met", email_body, "recipient_email@gmail.com")

        except ValueError:
            # Handle error if conversion to float fails
            pass


except psycopg2.Error as e:
    print("Error while connecting to PostgreSQL:", e)

finally:
    # Close cursor and connection
    cursor.close()
    conn.close()

    # Quit WebDriver
    driver.quit()
