import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Set up Selenium WebDriver
driver = webdriver.Chrome()
url = "https://www.eventbrite.ca/d/canada--toronto/university-of-toronto/"
driver.get(url)

# Explicit wait for events to load
try:
    # Wait for the event container to be present
    WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'eds-event-card-content')))
except:
    print("Timed out waiting for page to load")

# Parse the page content after ensuring events are loaded
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Open a CSV file to store the data
with open('events.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    # Write the header
    csvwriter.writerow(['Title', 'Description'])

    # Scrape and store data
    events = soup.find_all('div', class_='eds-event-card-content')  # Adjusted to correct event class
    for event in events:
        title = event.find('div', class_='eds-event-card__formatted-name').text if event.find('div', class_='eds-event-card__formatted-name') else "No title"
        description = event.find('div', class_='eds-event-card__description').text if event.find('div', class_='eds-event-card__description') else "No description"
        csvwriter.writerow([title, description])

print("Data saved to events.csv")
# Print the first 1000 characters to inspect structure
print(soup.prettify()[:1000])

# Print the number of events found
print(f"Number of events found: {len(events)}")

driver.quit()
