import random
import csv
import io
import os
from datetime import datetime
from flask import Flask, request, send_file, render_template
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from groq import Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


app = Flask(__name__)

# --- Selenium scraper ---
def fetch_knowt_flashcards(url):
    """Given a public Knowt flashcard set URL, scrape the flashcards using Selenium."""
    options = Options()
    options.add_argument("--headless")  # run without opening a browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    time.sleep(3)  # wait for the JS to load the flashcards

    # Grab flashcards
    cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid^="auto-id-"] > .flex_flex__NGgQE')
    flashcards = []
    for card in cards:
        texts = card.find_elements(By.CSS_SELECTOR, '.ProseMirror p')
        if len(texts) >= 2:
            question = texts[0].text.strip()
            answer = texts[1].text.strip()
            flashcards.append((question, answer))

    driver.quit()
    return flashcards

# --- Random wrong answers generator ---
def generate_random_wrongs(cards, n=3):
    definitions = [d for _, d in cards]
    rows = []
    for term, correct in cards:
        pool = [d for d in definitions if d != correct]
        wrongs = random.sample(pool, n) if len(pool) >= n else pool + [""] * (n - len(pool))
        rows.append((term, correct, wrongs))
    return rows

# --- Blank wrong answers generator  ---
def generate_blank_wrongs(cards, n=3):
    return [(term, correct, [""] * n) for term, correct in cards]
#AI WRONGS
def generate_ai_wrongs_for_one(question, answer, n=3):
    prompt = f"""
    Create {n} plausible but incorrect answers for this flashcard:

    Question: {question}
    Correct Answer: {answer}

    Requirements:
    - WRONG answers only
    - not a synonym of the correct answer
    - relevant to the question
    - Must not include the correct answer
    - In similar style and length to the correct answer
    - easy to understand
    - eighth-grade reading level
    - Realistic and believable
    - Return each on its own line with no numbering
    """

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )

        # FIXED LINE
        text = resp.choices[0].message.content.strip()
        wrongs = text.split("\n")
        wrongs = [w.strip("-• ").strip() for w in wrongs if w.strip()]

        return wrongs[:n]

    except Exception as e:
        print("Groq error:", e)
        return ["Option A", "Option B", "Option C"][:n]
    
def generate_ai_wrongs(cards, n=3):
    rows = []
    for q, a in cards:
        wrongs = generate_ai_wrongs_for_one(q, a, n)
        rows.append((q, a, wrongs))

    return rows

# --- Build CSV in Blooket format ---
def build_blooketformat_csv(rows):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    
    writer.writerow(["Blooket Import Template", "", "", "", "", "", "", ""])
    writer.writerow([
        "Question #",
        "Question Text",
        "Answer 1",
        "Answer 2",
        "Answer 3 (Optional)",
        "Answer 4 (Optional)",
        "Time Limit (sec) (Max: 300 seconds)",
        "Correct Answer(s) (Only include Answer #)"
    ])
    
    for i, (term, correct, wrongs) in enumerate(rows, start=1):
        answers = ["", "", "", ""]
        # pick a random slot for the correct answer
        correct_slot = random.randint(0, 3)
        answers[correct_slot] = correct
        
        # fill the remaining slots with wrong answers
        wrong_idx = 0
        for slot in range(4):
            if slot != correct_slot and wrong_idx < len(wrongs):
                answers[slot] = wrongs[wrong_idx]
                wrong_idx += 1
        
        time_limit = 20
        writer.writerow([i, term, *answers, time_limit, str(correct_slot + 1)])
    
    return output.getvalue()


# --- Flask routes ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    url = request.form.get("url", "")
    mode = request.form.get("mode", "blank")
    
    if not url:
        return "No Knowt URL provided.", 400

    cards = fetch_knowt_flashcards(url)
    unique_cards = []
    seen_questions = set()
    for q, a in cards:
        if q not in seen_questions:
            unique_cards.append((q, a))
            seen_questions.add(q)
    if mode == "random":
        rows = generate_random_wrongs(unique_cards)
    elif mode == "ai":
        rows = generate_ai_wrongs(unique_cards)
    else:
        rows = generate_blank_wrongs(unique_cards)

    csv_data = build_blooketformat_csv(rows)

    return send_file(
        io.BytesIO(csv_data.encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"blooket_import_file_{datetime.now().strftime('%Y-%m-%d')}.csv"
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, port=port)
