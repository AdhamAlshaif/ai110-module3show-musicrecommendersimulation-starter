import os

import pytest

from src.recommender import (
    Song,
    UserProfile,
    Recommender,
    load_songs,
    recommend_songs,
    score_song,
)

CATALOG = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.csv")
LOFI = {
    "favorite_genre": "lofi",
    "favorite_mood": "chill",
    "target_energy": 0.3,
    "likes_acoustic": True,
}

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# Reliability tests (Phase 4) — properties the recommender must always hold.
# All of these run offline against the rule-based scorer (no LLM, no network),
# so `pytest` stays fast, free, and deterministic.
# ---------------------------------------------------------------------------

def test_scoring_follows_the_recipe():
    """A perfect pop/happy/energy match scores exactly 5 + 4 + 2 = 11 and its
    reasons cite the real rules (grounding)."""
    song = {
        "genre": "pop", "mood": "happy", "energy": 0.9,
        "acousticness": 0.1, "tempo_bpm": 120, "valence": 0.9, "danceability": 0.8,
    }
    prefs = {"favorite_genre": "pop", "favorite_mood": "happy",
             "target_energy": 0.9, "likes_acoustic": False}
    score, reasons = score_song(prefs, song)
    assert score == pytest.approx(11.0, abs=0.01)
    assert any("genre" in r for r in reasons)
    assert any("mood" in r for r in reasons)
    assert any("energy" in r for r in reasons)


def test_recommendations_are_deterministic():
    """Same input -> same output, every time."""
    songs = load_songs(CATALOG)
    first = recommend_songs(LOFI, songs, k=5)
    second = recommend_songs(LOFI, songs, k=5)
    assert [s["id"] for s, _, _ in first] == [s["id"] for s, _, _ in second]


def test_no_duplicate_songs_in_results():
    songs = load_songs(CATALOG)
    recs = recommend_songs(LOFI, songs, k=10)
    ids = [s["id"] for s, _, _ in recs]
    assert len(ids) == len(set(ids))


def test_results_are_sorted_by_score_descending():
    songs = load_songs(CATALOG)
    recs = recommend_songs(LOFI, songs, k=10)
    scores = [score for _, score, _ in recs]
    assert scores == sorted(scores, reverse=True)


def test_recommended_songs_are_real_catalog_songs():
    """No hallucinations: every recommended song exists in the catalog."""
    songs = load_songs(CATALOG)
    catalog_ids = {s["id"] for s in songs}
    recs = recommend_songs(LOFI, songs, k=8)
    assert all(s["id"] in catalog_ids for s, _, _ in recs)


def test_explanation_references_real_attributes():
    """The offline explanation names the song and cites a real matched rule."""
    rec = make_small_recommender()
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    song = rec.songs[0]  # the pop/happy track
    text = rec.explain_recommendation(user, song)
    assert song.title in text
    assert ("genre match" in text) or ("mood match" in text)
