#this is a file python file that coverts pasted knowt flashcard text in an array to a csv file that can be imported into blooket
import random
import csv
import io

#function to parse knowt flashcard text

def parse_knowt_flashcards(text):
    cards = []
    lines = text.strip().split('\n')
    for line in lines:
        lineparts = line.split('\t')
        if len(lineparts) >= 2:
            term = lineparts[0].strip()
            definition = lineparts[1].strip()
            cards.append((term, definition))
    return cards
#function to generate random wrong answers
def generate_random_wrongs(cards, n=3):
    definitions = [d for _, d in cards]
    rows = []
    for term, correct in cards:
        pool = [d for d in definitions if d != correct]
        if len (pool) > n:
            wrongs = random.sample(pool, n)
        else:
            wrongs = pool.copy()
            while len(wrongs) < n:
                wrongs.append("")
        rows.append((term, correct, wrongs))
    return rows

#function to genrate blank wronng answers
def generate_blank_wrongs(cards, n=3):
    return [(term, correct, [""] * n) for term, correct in cards]

#function to write to csv
def build_blooketformat_csv(rows):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    
    #title row
    writer.writerow([
        "Blooket Import Template", "", "", "", "", "", "", ""
    ])
    #header row
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
        a1 = correct
        a2 = wrongs[0] if len(wrongs) > 0 else ""
        a3 = wrongs[1] if len(wrongs) > 1 else ""
        a4 = wrongs[2] if len(wrongs) > 2 else ""

        writer.writerow([
            i,          # Question #
            term,       # Question text
            a1, a2, a3, a4,
            20,         # time limit (constant)
            1           # correct answer index
        ])

    return output.getvalue()


if __name__ == "__main__":
    # Simulate Knowt exported text
    test_text = """test	1
test	2
test	3
test	4
test	5
test	6
test	7
test	8
test	9
test	10"""

    # Step 1: Parse
    cards = parse_knowt_flashcards(test_text)
    print("Parsed cards:", cards)

    # Step 2: Generate wrong answers (random or blank)
    rows = generate_random_wrongs(cards)   # or generate_blank_wrongs(cards)

    # Step 3: Build Blooket CSV
    csv_data = build_blooketformat_csv(rows)

    # Step 4: Save to file so you can test import in Blooket
    with open("test_blooket.csv", "w", encoding="utf-8") as f:
        f.write(csv_data)

    print("\nCSV generated as test_blooket.csv — upload this to Blooket.")



