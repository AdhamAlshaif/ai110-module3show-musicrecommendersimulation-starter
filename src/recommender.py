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
    Required by recommend_songs() and src/main.py
    """
    # TODO: Implement scoring logic using your Algorithm Recipe from Phase 2.
    # Expected return format: (score, reasons)
    return []

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    # TODO: Implement scoring and ranking logic
    # Expected return format: (song_dict, score, explanation)
    return []
