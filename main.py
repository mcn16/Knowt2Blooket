#this is a file python file that coverts pasted knowt flashcard text in an array to a csv file that can be imported into blooket
import random
import csv
import io
import os
from datetime import datetime
from flcleask import Flask, request, send_file, render_template

app=Flask(__name__)

#function to parse knowt flashcard text

def parse_knowt_flashcards(text):
    cards = []
    lines = text.strip().split('\n')
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 2:
            term = parts[0].strip()
            definition = parts[1].strip()
            cards.append((term, definition))
    return cards
#function to generate random wrong answers
def generate_random_wrongs(cards, n=3):
    """Return list of tuples: (term, correct, [wrong1, wrong2, wrong3])"""
    definitions = [d for _, d in cards]
    rows = []
    for term, correct in cards:
        pool = [d for d in definitions if d != correct]
        if len (pool) > n:
            wrongs = random.sample(pool, n)
        else:
            wrongs = pool + [""] * (n - len(pool))
        rows.append((term, correct, wrongs))
    return rows

#function to genrate blank wronng answers
def generate_blank_wrongs(cards, n=3):
    return [(term, correct, [""] * n) for term, correct in cards]

#function to write to csv
def build_blooketformat_csv(rows):
    """
    rows: list of (term, correct, wrongs_list)
    This writes the required first title row, header row, then question rows.
    For each question, the correct answer is placed in a random answer slot (1-4)
    among the available slots; other slots are filled with wrong answers or blanks.
    """
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")#lineterminator to avoid new lines being made cus that was causing problems
    
    #title row(ughhh stupid ass blooket made me do this)
    writer.writerow([
        "Blooket Import Template", "", "", "", "", "", "", ""
    ])
    #header row(again with the stupid blooket)
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
    #question rows
    for i, (term, correct, wrongs) in enumerate(rows, start=1):
        wrongs_filled=wrongs[:]
        answers =["","","",""]
        not_blank_wrongs = [w for w in wrongs_filled if w.strip() != ""]
        num_extra = min(len(not_blank_wrongs), 3)
        total_answer_slots = 1 + num_extra
        
        
        used_slot_indices = list(range(total_answer_slots))
        physical_slots = random.sample(range(4), total_answer_slots)
        physical_slots.sort()
        correct_slot = random.choice(physical_slots)
        answers[correct_slot] = correct
        
        fill_slots =[s for s in physical_slots if s != correct_slot]
        random.shuffle(not_blank_wrongs)
        
        for idx, slot in enumerate(fill_slots):
            if idx < len(not_blank_wrongs):
                answers[slot] = not_blank_wrongs[idx]
            else:
                answers[slot] = ""
        converted_correct_slot = correct_slot + 1
        time_limit = 20 # default time change later if needed
        writer.writerow([
            i,
            term,
            answers[0],
            answers[1],
            answers[2],
            answers[3],
            time_limit,
            str(converted_correct_slot)
        ])
        return output.getvalue()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    content = request.form.get("content", "")
    mode = request.form.get("mode", "blank")

    cards = parse_knowt_flashcards(content)

    if mode == "random":
        rows = generate_random_wrongs(cards)
    else:
        rows = generate_blank_wrongs(cards)

    csv_data = build_blooketformat_csv(rows)

    return send_file(
        io.BytesIO(csv_data.encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"blooket_import_file_{datetime.now().strftime('%Y-%m-%d')}.csv"
    )

if __name__ == "__main__":
    # optional: set port via environment
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, port=port)
