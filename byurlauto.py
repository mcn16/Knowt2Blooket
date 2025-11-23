from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
url = "https://knowt.com/flashcards/a6d9b054-7326-4a6b-b972-1af6c2f9802e"

options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)


try:
    driver.get(url)
    time.sleep(5)  # wait for JS to load the flashcards

    # Grab all flashcard elements
    cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid^="auto-id-"] > .flex_flex__NGgQE')

    flashcards = []
    for card in cards:
        texts = card.find_elements(By.CSS_SELECTOR, '.ProseMirror p')
        if len(texts) >= 2:
            flashcards.append({
                "question": texts[0].text,
                "answer": texts[1].text
            })

    for i, fc in enumerate(flashcards, 1):
        print(f"{i}. Q: {fc['question']} | A: {fc['answer']}")

finally:
    driver.quit()