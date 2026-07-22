# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world recommenders (Spotify, YouTube, etc.) learn what you like from your
behavior — the songs you play, like, skip, and save — and predict new songs with
similar features or that people with similar taste enjoyed. My version is simpler:
instead of learning from behavior, it uses a stated taste profile and scores each
song by how well its features match that profile. It prioritizes **genre and mood**
(the biggest matches) and then **energy** and **acoustic** preference for finer tuning.

**Features my `Song` object uses:** `genre`, `mood`, `energy`, `acousticness`.

**Features my `UserProfile` stores:** `favorite_genre`, `favorite_mood`,
`target_energy`, `likes_acoustic`.

### Algorithm Recipe

For every song, start `score = 0`, apply each rule, then rank.

- **Genre** — if `song.genre == user.favorite_genre`, add **+5**. Reason: "matches your favorite genre."
- **Mood** — if `song.mood == user.favorite_mood`, add **+4**. Reason: "matches your mood."
- **Energy** — add `2 × (1 − |song.energy − user.target_energy|)`. Perfect match adds ~2, far-off adds ~0. Reason: "energy is close to what you wanted."
- **Acoustic** — if `user.likes_acoustic` and `song.acousticness > 0.6`, add **+1**. Reason: "you like acoustic songs."

**Total** = sum of the rules. Sort descending, recommend the top `k`.

### Expected Bias

Because a genre match (+5) outscores a mood match (+4), this system **over-prioritizes genre** — it can bury a song that perfectly matches the user's mood just because it's in a different genre. It also assumes a stated profile is honest and stable, and only knows four features, so it ignores lyrics, artist, and anything about *why* someone likes a song.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

```
# e.g.:
# User profile: genre=indie, mood=chill, energy=low
# Recommendations:
#   1. ...
#   2. ...
#   3. ...
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



