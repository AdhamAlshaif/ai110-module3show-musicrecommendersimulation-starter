"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs

Step 5 (evaluation) stress-tests the recommender against several taste
profiles, including deliberately "adversarial" ones with conflicting or
impossible preferences, to see where the scoring logic breaks down.
"""

from src.recommender import load_songs, recommend_songs


# Taste profiles used to stress-test the recommender. The first three are
# "normal" listeners; the last two are adversarial edge cases designed to try
# to trick the scoring logic. Keys match the Algorithm Recipe weights.
PROFILES = {
    # --- Normal profiles ---
    "High-Energy Pop": {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.9,
        "likes_acoustic": False,
    },
    "Chill Lofi": {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.35,
        "likes_acoustic": True,
    },
    "Deep Intense Rock": {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.9,
        "likes_acoustic": False,
    },

    # --- Adversarial / edge-case profiles ---
    # Conflicting signals: wants high energy (0.9) but a "sad" mood, jazz, and
    # acoustic songs -- energy pulls loud tracks while genre/mood/acoustic pull
    # calm ones. Note: no song in the catalog has mood "sad", so that rule can
    # never fire. Which signal wins the ranking?
    "Conflicting Vibes (energy 0.9 + sad)": {
        "favorite_genre": "jazz",
        "favorite_mood": "sad",
        "target_energy": 0.9,
        "likes_acoustic": True,
    },
    # Impossible taste: a genre AND mood that don't exist in the catalog, so
    # only the energy rule can ever contribute points. Tests graceful fallback
    # when nothing matches -- ranking should collapse to pure energy closeness.
    "Impossible Taste (unknown genre/mood)": {
        "favorite_genre": "reggaeton",
        "favorite_mood": "euphoric",
        "target_energy": 0.5,
        "likes_acoustic": False,
    },
}

SEP = "=" * 60


def print_recommendations(name: str, user_prefs: dict, songs: list, k: int = 5) -> None:
    """Print the top-k recommendations for one named profile."""
    recommendations = recommend_songs(user_prefs, songs, k=k)

    print(SEP)
    print(f"PROFILE: {name}")
    print(
        f"  genre={user_prefs['favorite_genre']}, "
        f"mood={user_prefs['favorite_mood']}, "
        f"energy={user_prefs['target_energy']}, "
        f"acoustic={user_prefs['likes_acoustic']}"
    )
    print(SEP)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} - {song['artist']}")
        print(f"   Score:   {score:.2f}")
        print(f"   Reasons: {explanation}")
    print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    print()
    for name, prefs in PROFILES.items():
        print_recommendations(name, prefs, songs, k=5)


if __name__ == "__main__":
    main()
