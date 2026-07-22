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

When you run `python -m src.main` it goes through 5 profiles and prints the top 5
for each one. Here is the first profile, the High-Energy Pop listener
(`genre=pop, mood=happy, energy=0.9`):

```
Loading songs from data/songs.csv...
Loaded 20 songs.

============================================================
PROFILE: High-Energy Pop
  genre=pop, mood=happy, energy=0.9, acoustic=False
============================================================
1. Sunrise City - Neon Echo
   Score:   10.84
   Reasons: genre match (+5.0), mood match (+4.0), energy match (+1.84)
2. Gym Hero - Max Pulse
   Score:   6.94
   Reasons: genre match (+5.0), energy match (+1.94)
3. Rooftop Lights - Indigo Parade
   Score:   5.72
   Reasons: mood match (+4.0), energy match (+1.72)
4. Island Time - Palm Fever
   Score:   5.36
   Reasons: mood match (+4.0), energy match (+1.36)
5. Storm Runner - Voltline
   Score:   1.98
   Reasons: energy match (+1.98)
```

Sunrise City wins because it's the only song that hits all three things at once:
it's pop, it's happy, and its energy is close to what I asked for. Every pick
also shows its reasons and points so you can see why it got chosen. The other 4
profiles and the full breakdown are in the model card.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

I put all the point values in one spot (`DEFAULT_WEIGHTS` in
`src/recommender.py`), so running an experiment is just changing the weights.
`src/experiment.py` re-runs the Happy Pop profile (`pop / happy / energy 0.9`)
with three different setups. You can run it with `python -m src.experiment`.

**Experiment 1: double the energy weight (2 to 4) and cut the genre weight in
half (5 to 2.5).**

| Rank | Baseline | After the change |
|------|----------|------------------|
| 1 | Sunrise City | Sunrise City |
| 2 | Gym Hero | Rooftop Lights |
| 3 | Rooftop Lights | Island Time |
| 4 | Island Time | Gym Hero |
| 5 | Storm Runner | Storm Runner |

This made it more accurate, not just different. When genre matters less, Gym Hero
(which is pop but its mood is intense) drops from #2 to #4. The songs that are
actually happy, Rooftop Lights and Island Time, move up. For someone who asked
for happy pop, that is better. It showed me the baseline was leaning on genre too
much.

**Experiment 2: turn off the mood rule (set its weight to 0).**

Now Gym Hero jumps to #1, ahead of the happy Sunrise City. This one made it worse.
Gym Hero is a pop workout song that is intense, not happy. So it proved the mood
rule was actually doing real work. Without it, genre and energy alone hand a
"happy pop" person an intense song.

**What I learned:** the results change a lot depending on how I balance genre vs
mood. Turning genre down helped. Taking mood out hurt.

---

## Limitations and Risks

- It only has 20 songs, so it runs out of good options fast.
- Most genres only have one song, so you get no variety in your favorite genre.
- It doesn't understand lyrics, artists, or why someone likes a song.
- It leans toward loud music, so people who want calm music get worse matches.
- It never says "I found nothing", even when nothing really fits.

I go deeper on all of this in the model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



