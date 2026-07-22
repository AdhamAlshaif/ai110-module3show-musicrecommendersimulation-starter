"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # Taste profile: an upbeat "pop / happy" listener.
    # Keys match the UserProfile fields and the Algorithm Recipe weights.
    user_prefs = {
        "favorite_genre": "pop",    # exact-match genre bonus (+5)
        "favorite_mood": "happy",   # exact-match mood bonus (+4)
        "target_energy": 0.8,       # scored by closeness (up to +2)
        "likes_acoustic": False,    # +1 when song.acousticness > 0.6
    }

    k = 5
    recommendations = recommend_songs(user_prefs, songs, k=k)

    header = (
        f"Top {k} recommendations for a "
        f"{user_prefs['favorite_genre']} / {user_prefs['favorite_mood']} listener"
    )
    print()
    print("=" * len(header))
    print(header)
    print("=" * len(header))
    print()

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} - {song['artist']}")
        print(f"   Score:   {score:.2f}")
        print(f"   Reasons: {explanation}")
        print()


if __name__ == "__main__":
    main()
