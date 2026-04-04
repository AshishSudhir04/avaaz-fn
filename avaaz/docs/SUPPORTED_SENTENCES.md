# Sentences This System Supports

These are example sentences that work well with the current rules and video lexicon. Names and place names are **fingerspelled** (letter by letter) when they have no dedicated sign.

---

## Best supported (rule-matched, predictable gloss)

### Greetings
- Hello
- Hi
- Hello, how are you?
- Hi, how are you?
- How are you?

### Thanks & goodbye
- Thank you
- Thanks
- Bye
- Good bye

### Name
- What is your name?
- My name is Rahul
- My name is Ashik Joy
- I am Priya
- I am John

### Where you live
- Where do you live?
- Where are you from?
- I live in Kochi
- I live in Mumbai
- I live in Delhi
- I live in Angamaly

### Age
- I am 25 years old
- I am 30 years old

### Feelings
- I am happy
- I am sad
- I am busy

---

## Well supported (lexicon words; order may use ML fallback)

These use words that exist in the video lexicon. Gloss order may come from rules or from the ML model.

- So, what about you?
- We can talk
- I study
- I work
- I go to college
- Hello, I am here
- Thank you and welcome
- Good day
- See you
- Come here
- Go home
- My home
- From here
- Not now
- I can do it
- We will see
- That is good
- This is great
- So and so
- You and me
- But not that
- More and more
- The whole world
- Learn sign language
- Talk with hands
- Eat and go
- Stay safe
- Beautiful day
- Best of luck
- Better now
- Right way
- Wrong way
- Without you
- With us
- Help me
- See you next time
- Now or never
- Day by day
- Time to go
- God is good
- Welcome home
- Pretty good
- Great work
- Good bye and thank you

---

## Names and places (fingerspelled)

Any **name** or **place name** that does not have its own sign is spelled letter by letter using A–Z videos.

- My name is **Ashik** → ME NAME A-S-H-I-K
- My name is **Joy** → ME NAME J-O-Y
- I live in **Angamaly** → ME LIVE A-N-G-A-M-A-L-I
- I am **Rahul** → ME NAME R-A-H-U-L

So you can use any English name or city; the system will fingerspell it.

---

## Numbers (0–9)

- Zero, one, two, three, four, five, six, seven, eight, nine  
  (Videos: 0.mp4 … 9.mp4)

---

## Summary

| Category        | Examples                                      |
|----------------|-----------------------------------------------|
| Greetings      | Hello, Hi, How are you?                       |
| Thanks / Bye   | Thank you, Thanks, Bye                        |
| Name           | What is your name? My name is X. I am X.       |
| Where live     | Where do you live? I live in X.                |
| Age            | I am 25 years old                             |
| Feelings       | I am happy / sad / busy                       |
| Names/places   | Any name or place → fingerspelled A–Z         |
| Lexicon words  | 140+ words (see `nlp/isl_lexicon.json`)        |

For more words, check `nlp/isl_lexicon.json`. Adding a new sentence type usually means adding a new rule in `nlp/nlp_gloss.py` and/or new entries in the lexicon.
