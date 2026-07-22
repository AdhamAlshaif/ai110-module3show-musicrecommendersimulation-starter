"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # Taste profile: a "chill lofi listener".
    # Keys match the UserProfile fields and the Algorithm Recipe weights.
    user_prefs = {
        "favorite_genre": "lofi",   # exact-match genre bonus (+5)
        "favorite_mood": "chill",   # exact-match mood bonus (+4)
        "target_energy": 0.4,       # scored by closeness (up to +2)
        "likes_acoustic": True,     # +1 when song.acousticness > 0.6
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\nTop recommendations:\n")
    for rec in recommendations:
        # You decide the structure of each returned item.
        # A common pattern is: (song, score, explanation)
        song, score, explanation = rec
        print(f"{song['title']} - Score: {score:.2f}")
        print(f"Because: {explanation}")
        print()


if __name__ == "__main__":
    main()
