"""
Data experiments for the Music Recommender Simulation (evaluation phase).

Runs the recommender under three weight configurations for the same profile so
you can see how sensitive the rankings are to the scoring weights:

  1. Baseline        - the default Algorithm Recipe weights.
  2. Weight Shift    - double `energy`, halve `genre` (energy matters more).
  3. Mood Removed    - the `mood` rule turned off (weight 0).

Run with:  python -m src.experiment
"""

from src.recommender import load_songs, recommend_songs, DEFAULT_WEIGHTS

# The profile we probe with. "Happy Pop" is the assignment's running example.
PROFILE = {
    "name": "Happy Pop",
    "favorite_genre": "pop",
    "favorite_mood": "happy",
    "target_energy": 0.9,
    "likes_acoustic": False,
}

# The three weight configurations to compare.
EXPERIMENTS = {
    "1. Baseline (genre 5, mood 4, energy 2, acoustic 1)": DEFAULT_WEIGHTS,
    "2. Weight Shift (energy x2 -> 4, genre /2 -> 2.5)": {
        **DEFAULT_WEIGHTS,
        "genre": 2.5,
        "energy": 4.0,
    },
    "3. Mood Removed (mood -> 0)": {
        **DEFAULT_WEIGHTS,
        "mood": 0.0,
    },
}

SEP = "=" * 68


def run() -> None:
    songs = load_songs("data/songs.csv")
    print()
    print(SEP)
    print(f"EXPERIMENT PROFILE: {PROFILE['name']}")
    print(
        f"  genre={PROFILE['favorite_genre']}, mood={PROFILE['favorite_mood']}, "
        f"energy={PROFILE['target_energy']}, acoustic={PROFILE['likes_acoustic']}"
    )
    print(SEP)

    for label, weights in EXPERIMENTS.items():
        print(f"\n--- {label} ---")
        recs = recommend_songs(PROFILE, songs, k=5, weights=weights)
        for rank, (song, score, explanation) in enumerate(recs, start=1):
            print(f"  {rank}. {song['title']:<20} score {score:5.2f}   {explanation}")
    print()


if __name__ == "__main__":
    run()
