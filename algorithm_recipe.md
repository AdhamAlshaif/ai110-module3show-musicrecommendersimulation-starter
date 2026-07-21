# 🎵 Algorithm Recipe — Song Scoring Rules

The set of rules the recommender uses to score each song against a user's taste
profile. For every song, start `score = 0`, apply each rule below, then rank.

## Scoring Rules

- **Genre** (weight 2): if `song.genre == user.favorite_genre`, add **5**.
  - Reason: "matches your favorite genre."
- **Mood** (weight 3): if `song.mood == user.favorite_mood`, add **4**.
  - Reason: "matches your mood."
- **Energy** (weight 2): add `2 × (1 − |song.energy − user.target_energy|)`.
  - A perfect energy match adds 2; a far-off one adds near 0.
  - Reason: "energy is close to what you wanted."
- **Acoustic** (weight 1): if `user.likes_acoustic` and `song.acousticness > 0.6`, add **1**.
  - Reason: "you like acoustic songs."

## Combine & Choose

- **Total** = sum of all the rules above.
- **Sort** songs by total score, descending.
- **Recommend** the top `k`.
