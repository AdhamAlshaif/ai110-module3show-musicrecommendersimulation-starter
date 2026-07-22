import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file into a list of dictionaries.

    Each row becomes a dict keyed by the CSV headers. Values arrive from the
    file as strings, so the numeric columns are converted to numbers to make
    them usable by the scoring functions:
      - id                                                    -> int
      - energy, tempo_bpm, valence, danceability, acousticness -> float
    Text columns (title, artist, genre, mood) are kept as trimmed strings.

    Rows that are blank or have unparseable numbers are skipped with a warning
    so one bad line can't crash the whole load.

    Required by src/main.py
    """
    print(f"Loading songs from {csv_path}...")

    songs: List[Dict] = []

    with open(csv_path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):  # start=2: header is line 1
            # Skip fully blank rows (e.g. a trailing newline at end of file).
            if row is None or not any((value or "").strip() for value in row.values()):
                continue

            try:
                # Keys follow the CSV header / Song field order. Numeric columns
                # are converted so the scoring math works on numbers, not text.
                song: Dict = {
                    "id": int(row["id"]),
                    "title": (row["title"] or "").strip(),
                    "artist": (row["artist"] or "").strip(),
                    "genre": (row["genre"] or "").strip(),
                    "mood": (row["mood"] or "").strip(),
                    "energy": float(row["energy"]),
                    "tempo_bpm": float(row["tempo_bpm"]),
                    "valence": float(row["valence"]),
                    "danceability": float(row["danceability"]),
                    "acousticness": float(row["acousticness"]),
                }
            except (KeyError, ValueError, TypeError) as err:
                print(f"  Skipping row {line_no}: {err}")
                continue

            songs.append(song)

    print(f"Loaded {len(songs)} songs.")
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.

    Applies the Algorithm Recipe rules and returns the total score plus a
    list of human-readable reasons explaining why the song scored points.

    Required by recommend_songs() and src/main.py
    """
    score = 0.0
    reasons: List[str] = []

    # Genre match (+5) — the biggest single bonus.
    if song.get("genre") == user_prefs.get("favorite_genre"):
        score += 5
        reasons.append("genre match (+5.0)")

    # Mood match (+4).
    if song.get("mood") == user_prefs.get("favorite_mood"):
        score += 4
        reasons.append("mood match (+4.0)")

    # Energy closeness: 2 * (1 - |song.energy - target|), so a perfect match
    # adds ~2 and a far-off one adds ~0. Clamped at 0 just in case.
    target_energy = user_prefs.get("target_energy")
    if target_energy is not None:
        energy_points = 2 * (1 - abs(song["energy"] - target_energy))
        energy_points = max(0.0, energy_points)
        score += energy_points
        if energy_points > 0:
            reasons.append(f"energy match (+{energy_points:.2f})")

    # Acoustic preference (+1).
    if user_prefs.get("likes_acoustic") and song.get("acousticness", 0) > 0.6:
        score += 1
        reasons.append("acoustic match (+1.0)")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song, sorts by score (highest first), and returns the top k.

    Each item is (song_dict, score, explanation), matching how src/main.py
    unpacks and prints the results.

    Required by src/main.py
    """
    # Judge every song: pair each with its score and a readable explanation.
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = ", ".join(reasons) if reasons else "no strong matches"
        scored.append((song, score, explanation))

    # sorted() returns a NEW list ordered by score, highest first; take top k.
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    return ranked[:k]
