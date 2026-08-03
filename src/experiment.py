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


# ---------------------------------------------------------------------------
# Reliability report (Phase 4)
# ---------------------------------------------------------------------------
# Beyond weight sensitivity, we also want evidence the recommender *behaves*:
# same input -> same output, no duplicate songs, only real catalog songs, and
# grounded explanations. This runs offline over the full 140-song catalog.

CATALOG_PATH = "data/catalog.csv"

CHECK_PROFILES = {
    "Chill Lofi":      {"favorite_genre": "lofi",  "favorite_mood": "chill",   "target_energy": 0.30, "likes_acoustic": True},
    "High-Energy Pop": {"favorite_genre": "pop",   "favorite_mood": "happy",   "target_energy": 0.90, "likes_acoustic": False},
    "Intense Metal":   {"favorite_genre": "metal", "favorite_mood": "intense", "target_energy": 0.95, "likes_acoustic": False},
    "Sad Jazz":        {"favorite_genre": "jazz",  "favorite_mood": "sad",     "target_energy": 0.40, "likes_acoustic": True},
}


def _grounded(explanation: str) -> bool:
    """An explanation is 'grounded' if it's non-empty and cites a real rule."""
    e = explanation.strip()
    return bool(e) and ("match" in e or e == "no strong matches")


def reliability_report() -> None:
    """Check the reliability properties on every profile and print PASS/FAIL."""
    songs = load_songs(CATALOG_PATH)
    catalog_ids = {s["id"] for s in songs}

    print(SEP)
    print(f"RELIABILITY REPORT  (rule-based recommender over {len(songs)} songs)")
    print(SEP)

    profiles_passed = 0
    for name, prefs in CHECK_PROFILES.items():
        recs1 = recommend_songs(prefs, songs, k=5)
        recs2 = recommend_songs(prefs, songs, k=5)
        ids1 = [s["id"] for s, _, _ in recs1]

        deterministic = ids1 == [s["id"] for s, _, _ in recs2]
        no_dupes = len(ids1) == len(set(ids1))
        real_songs = all(i in catalog_ids for i in ids1)
        grounded = all(_grounded(expl) for _, _, expl in recs1)
        on_genre = recs1[0][0]["genre"] == prefs["favorite_genre"]

        passed = deterministic and no_dupes and real_songs and grounded
        profiles_passed += int(passed)

        def mark(ok: bool) -> str:
            return "PASS" if ok else "FAIL"

        print(
            f"  {name:<16} deterministic={mark(deterministic)}  "
            f"no-duplicates={mark(no_dupes)}  real-songs={mark(real_songs)}  "
            f"grounded={mark(grounded)}  top-genre-match={'yes' if on_genre else 'no'}"
        )

    total = len(CHECK_PROFILES)
    print("-" * 68)
    verdict = "ALL CHECKS PASSED" if profiles_passed == total else "SOME CHECKS FAILED"
    print(f"  Overall: {verdict}  ({profiles_passed}/{total} profiles)")
    print()


if __name__ == "__main__":
    run()
    reliability_report()
