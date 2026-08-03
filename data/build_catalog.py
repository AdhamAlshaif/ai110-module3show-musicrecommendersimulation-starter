"""
Build an expanded, more balanced song catalog for the RAG recommender.

The original `data/songs.csv` has only 20 songs, and the model card flags three
biases that come straight from that tiny data set:
  1. Most genres have a single song  -> no variety within a genre.
  2. There is no "sad" mood at all.
  3. The catalog leans high-energy    -> calm-music fans get worse matches.

This script keeps the original 20 as a seed and generates a larger catalog
(`data/catalog.csv`) that fixes all three: many songs per genre, every mood
represented (including "sad"), and a full spread of energy from calm to intense.

The titles/artists are fictional, exactly like the originals -- this is a
simulation, not real music data. Output is deterministic (fixed seed) so
re-running produces the identical catalog.

Run:  python data/build_catalog.py
"""

from __future__ import annotations

import csv
import os
import random

SEED = 110
TARGET_PER_GENRE = 6  # generated songs per genre (on top of any seed songs)

HERE = os.path.dirname(os.path.abspath(__file__))
SEED_CSV = os.path.join(HERE, "songs.csv")
OUT_CSV = os.path.join(HERE, "catalog.csv")

FIELDS = [
    "id", "title", "artist", "genre", "mood",
    "energy", "tempo_bpm", "valence", "danceability", "acousticness",
]

# Per-genre feature tendencies. Each range is (low, high); a song draws uniformly
# from it. `moods` lists the moods that fit the genre. Energy bands are chosen so
# the catalog as a whole spans calm -> intense (fixing the high-energy lean), and
# "sad" appears across the mellow genres (fixing the missing-mood gap).
GENRE_PROFILES = {
    # --- calm / mellow genres (low energy, more acoustic) ---
    "lofi":      dict(energy=(0.25, 0.50), tempo=(60, 92),  valence=(0.40, 0.70), dance=(0.40, 0.66), acoustic=(0.60, 0.90), moods=["chill", "relaxed", "focused", "sad", "dreamy"]),
    "ambient":   dict(energy=(0.15, 0.40), tempo=(50, 80),  valence=(0.45, 0.75), dance=(0.30, 0.50), acoustic=(0.70, 0.95), moods=["chill", "dreamy", "relaxed", "melancholic"]),
    "classical": dict(energy=(0.20, 0.55), tempo=(55, 100), valence=(0.35, 0.70), dance=(0.20, 0.45), acoustic=(0.85, 0.98), moods=["dreamy", "melancholic", "sad", "chill", "romantic"]),
    "jazz":      dict(energy=(0.30, 0.60), tempo=(70, 120), valence=(0.45, 0.75), dance=(0.45, 0.70), acoustic=(0.65, 0.90), moods=["relaxed", "moody", "romantic", "sad"]),
    "folk":      dict(energy=(0.30, 0.55), tempo=(75, 115), valence=(0.45, 0.75), dance=(0.40, 0.60), acoustic=(0.75, 0.95), moods=["relaxed", "melancholic", "sad", "romantic"]),
    "blues":     dict(energy=(0.35, 0.60), tempo=(70, 110), valence=(0.30, 0.60), dance=(0.45, 0.65), acoustic=(0.55, 0.85), moods=["moody", "sad", "melancholic", "relaxed"]),
    "soul":      dict(energy=(0.40, 0.65), tempo=(80, 115), valence=(0.55, 0.85), dance=(0.55, 0.78), acoustic=(0.40, 0.70), moods=["romantic", "confident", "relaxed", "moody"]),

    # --- mid-energy genres ---
    "r&b":       dict(energy=(0.45, 0.70), tempo=(85, 120), valence=(0.50, 0.80), dance=(0.60, 0.85), acoustic=(0.25, 0.60), moods=["confident", "romantic", "moody", "relaxed"]),
    "indie pop": dict(energy=(0.55, 0.80), tempo=(105, 130), valence=(0.55, 0.85), dance=(0.65, 0.85), acoustic=(0.25, 0.55), moods=["happy", "dreamy", "moody", "romantic"]),
    "country":   dict(energy=(0.40, 0.68), tempo=(85, 125), valence=(0.50, 0.80), dance=(0.45, 0.70), acoustic=(0.55, 0.85), moods=["relaxed", "happy", "melancholic", "romantic"]),
    "reggae":    dict(energy=(0.45, 0.70), tempo=(80, 110), valence=(0.60, 0.90), dance=(0.60, 0.82), acoustic=(0.30, 0.60), moods=["happy", "relaxed", "chill"]),
    "world":     dict(energy=(0.40, 0.72), tempo=(90, 125), valence=(0.55, 0.85), dance=(0.50, 0.78), acoustic=(0.50, 0.80), moods=["relaxed", "happy", "dreamy"]),
    "funk":      dict(energy=(0.60, 0.85), tempo=(100, 125), valence=(0.60, 0.88), dance=(0.75, 0.92), acoustic=(0.10, 0.35), moods=["confident", "happy", "energetic"]),

    # --- high-energy genres ---
    "pop":       dict(energy=(0.60, 0.92), tempo=(100, 132), valence=(0.60, 0.92), dance=(0.70, 0.90), acoustic=(0.05, 0.30), moods=["happy", "confident", "energetic", "moody"]),
    "rock":      dict(energy=(0.65, 0.92), tempo=(110, 155), valence=(0.40, 0.70), dance=(0.55, 0.75), acoustic=(0.05, 0.30), moods=["intense", "confident", "energetic", "moody"]),
    "synthwave": dict(energy=(0.60, 0.85), tempo=(100, 125), valence=(0.40, 0.70), dance=(0.65, 0.85), acoustic=(0.10, 0.35), moods=["moody", "dreamy", "energetic"]),
    "hip hop":   dict(energy=(0.60, 0.88), tempo=(85, 120),  valence=(0.45, 0.78), dance=(0.75, 0.93), acoustic=(0.05, 0.35), moods=["confident", "energetic", "moody"]),
    "electronic":dict(energy=(0.70, 0.93), tempo=(115, 135), valence=(0.45, 0.78), dance=(0.75, 0.94), acoustic=(0.03, 0.25), moods=["energetic", "intense", "euphoric"]),
    "edm":       dict(energy=(0.75, 0.97), tempo=(120, 140), valence=(0.55, 0.90), dance=(0.80, 0.96), acoustic=(0.02, 0.20), moods=["euphoric", "energetic", "intense", "happy"]),
    "metal":     dict(energy=(0.80, 0.98), tempo=(130, 175), valence=(0.30, 0.60), dance=(0.50, 0.72), acoustic=(0.02, 0.15), moods=["intense", "angry", "energetic"]),
}

# Word pools for fictional titles/artists (same playful style as the originals).
TITLE_ADJ = [
    "Neon", "Velvet", "Midnight", "Golden", "Silver", "Crystal", "Electric", "Silent",
    "Broken", "Distant", "Hidden", "Frozen", "Burning", "Faded", "Wild", "Endless",
    "Lonely", "Sacred", "Cosmic", "Paper", "Glass", "Amber", "Scarlet", "Indigo",
    "Restless", "Gentle", "Ocean", "Desert", "Mountain", "City", "Rainy", "Sunlit",
]
TITLE_NOUN = [
    "Skyline", "Echoes", "Dreams", "Horizon", "Static", "Embers", "Currents", "Mirage",
    "Lanterns", "Avenue", "Tides", "Pulse", "Bloom", "Drift", "Halo", "Vertigo",
    "Shadows", "Daylight", "Fever", "Signal", "Orbit", "Harbor", "Reverie", "Motion",
    "Nights", "Rooms", "Streets", "Waves", "Frost", "Ashes", "Glow", "Rush",
]
ARTIST_A = [
    "Neon", "Blue", "Paper", "Midnight", "Velvet", "Silver", "Echo", "Lunar", "Crimson",
    "Golden", "Static", "Glass", "Amber", "Wild", "Slow", "Electric", "Cosmic", "Hollow",
]
ARTIST_B = [
    "Echo", "Room", "Lanterns", "Parade", "Frame", "Signal", "Bloom", "Ghost", "Collective",
    "Strings", "Circuit", "Stereo", "Fever", "Trio", "Hollow", "Verse", "Pulse", "Drift",
]


def _load_seed(rng: random.Random) -> tuple[list[dict], set[str]]:
    """Read the original 20 songs so the catalog is a strict superset of them."""
    seed_rows: list[dict] = []
    used_titles: set[str] = set()
    if not os.path.exists(SEED_CSV):
        return seed_rows, used_titles
    with open(SEED_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seed_rows.append(row)
            used_titles.add(row["title"].strip().lower())
    return seed_rows, used_titles


def _unique_title(rng: random.Random, used: set[str]) -> str:
    """Draw a fictional 'Adjective Noun' title that hasn't been used yet."""
    for _ in range(200):
        title = f"{rng.choice(TITLE_ADJ)} {rng.choice(TITLE_NOUN)}"
        if title.lower() not in used:
            used.add(title.lower())
            return title
    # Extremely unlikely fallback: append a number.
    n = len(used)
    return f"{rng.choice(TITLE_ADJ)} {rng.choice(TITLE_NOUN)} {n}"


def _rand_song(rng: random.Random, genre: str, prof: dict, sid: int, used: set[str]) -> dict:
    """Generate one fictional song row for a genre using its feature tendencies."""
    def rnd(lo_hi: tuple[float, float]) -> float:
        lo, hi = lo_hi
        return round(rng.uniform(lo, hi), 2)

    return {
        "id": sid,
        "title": _unique_title(rng, used),
        "artist": f"{rng.choice(ARTIST_A)} {rng.choice(ARTIST_B)}",
        "genre": genre,
        "mood": rng.choice(prof["moods"]),
        "energy": rnd(prof["energy"]),
        "tempo_bpm": int(rng.uniform(*prof["tempo"])),
        "valence": rnd(prof["valence"]),
        "danceability": rnd(prof["dance"]),
        "acousticness": rnd(prof["acoustic"]),
    }


def build() -> None:
    rng = random.Random(SEED)
    seed_rows, used_titles = _load_seed(rng)

    rows: list[dict] = list(seed_rows)
    next_id = max((int(r["id"]) for r in seed_rows), default=0) + 1

    for genre, prof in GENRE_PROFILES.items():
        for _ in range(TARGET_PER_GENRE):
            rows.append(_rand_song(rng, genre, prof, next_id, used_titles))
            next_id += 1

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in FIELDS})

    # Quick summary so you can see the biases are fixed.
    genres = sorted({r["genre"] for r in rows})
    moods = sorted({r["mood"] for r in rows})
    calm = sum(1 for r in rows if float(r["energy"]) < 0.5)
    print(f"Wrote {len(rows)} songs to {os.path.relpath(OUT_CSV, os.path.dirname(HERE))}")
    print(f"  Genres ({len(genres)}): {', '.join(genres)}")
    print(f"  Moods  ({len(moods)}): {', '.join(moods)}")
    print(f"  'sad' present: {'yes' if 'sad' in moods else 'no'}")
    print(f"  Calm songs (energy < 0.5): {calm} of {len(rows)}")


if __name__ == "__main__":
    build()
