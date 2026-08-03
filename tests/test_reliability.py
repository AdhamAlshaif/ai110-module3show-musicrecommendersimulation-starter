"""
Reliability tests (Phase 4) for the AI pipeline.

These focus on the guarantees that make the agentic recommender trustworthy:
  - The hallucination guard (validate_picks) only ever returns real catalog ids,
    de-duplicated, capped at k, and backfilled when the LLM under-delivers.
  - JSON parsing survives the messy ways an LLM can wrap its output.
  - The retriever is deterministic and returns on-target songs.

The pure-function tests need no API key or network. The one true end-to-end test
that actually calls Claude is skipped unless you opt in with RUN_LLM_TESTS=1, so
the normal `pytest` run stays fast and free.
"""

import os

import pytest

from src.agent import _extract_json, materialize_picks, validate_picks
from src.retriever import (
    build_index,
    profile_to_query,
    retrieve_for_profile,
    song_to_document,
)

# A tiny fake candidate pool (ids 1,2,3) with rule scores for backfill ordering.
CANDIDATES = [
    {"id": 1, "title": "Alpha", "artist": "X", "genre": "pop", "mood": "happy", "energy": 0.8, "rule_score": 9.0},
    {"id": 2, "title": "Bravo", "artist": "Y", "genre": "pop", "mood": "moody", "energy": 0.7, "rule_score": 6.0},
    {"id": 3, "title": "Charlie", "artist": "Z", "genre": "lofi", "mood": "chill", "energy": 0.3, "rule_score": 3.0},
]


# --- hallucination guard ----------------------------------------------------

def test_validate_drops_hallucinated_ids():
    picks = [{"id": 1, "reason": "real"}, {"id": 999, "reason": "made up"}]
    out = validate_picks(picks, CANDIDATES, k=3)
    ids = [p["id"] for p in out]
    assert 999 not in ids
    assert all(i in {1, 2, 3} for i in ids)


def test_validate_removes_duplicates():
    picks = [{"id": 1, "reason": "a"}, {"id": 1, "reason": "dup"}]
    out = validate_picks(picks, CANDIDATES, k=3)
    assert [p["id"] for p in out].count(1) == 1


def test_validate_caps_at_k():
    picks = [{"id": 1}, {"id": 2}, {"id": 3}]
    out = validate_picks(picks, CANDIDATES, k=2)
    assert len(out) == 2


def test_validate_backfills_by_rule_score():
    """If the LLM returns too few, fill up to k from the best rule-scored songs."""
    picks = [{"id": 1, "reason": "only one"}]
    out = validate_picks(picks, CANDIDATES, k=3)
    assert len(out) == 3
    assert [p["id"] for p in out] == [1, 2, 3]  # 2 (6.0) before 3 (3.0)


def test_materialize_returns_full_songs_with_reason():
    by_id = {c["id"]: c for c in CANDIDATES}
    out = materialize_picks([{"id": 2, "reason": "because moody"}], by_id)
    assert out[0]["title"] == "Bravo"
    assert out[0]["reason"] == "because moody"


# --- JSON parsing robustness ------------------------------------------------

def test_extract_json_plain():
    assert _extract_json('{"a": 1}')["a"] == 1


def test_extract_json_code_fenced():
    assert _extract_json('```json\n{"a": 2}\n```')["a"] == 2


def test_extract_json_with_surrounding_text():
    assert _extract_json('Sure, here you go: {"a": 3} — done!')["a"] == 3


# --- taste/document text ----------------------------------------------------

def test_profile_to_query_mentions_taste():
    q = profile_to_query({"favorite_genre": "lofi", "favorite_mood": "chill",
                          "target_energy": 0.3, "likes_acoustic": True})
    assert "lofi" in q and "chill" in q


def test_song_to_document_mentions_genre_and_mood():
    doc = song_to_document({
        "title": "T", "artist": "A", "genre": "jazz", "mood": "sad", "energy": 0.4,
        "valence": 0.5, "danceability": 0.5, "acousticness": 0.8, "tempo_bpm": 90,
    })
    assert "jazz" in doc and "sad" in doc


# --- retriever behavior (offline; loads the embedding model once) -----------

@pytest.fixture(scope="module")
def indexed():
    build_index()
    return True


def test_retriever_is_on_genre(indexed):
    prefs = {"favorite_genre": "lofi", "favorite_mood": "chill",
             "target_energy": 0.3, "likes_acoustic": True}
    genres = [r["genre"] for r in retrieve_for_profile(prefs, k=5)]
    assert genres.count("lofi") >= 3  # majority of the top 5 are on-genre


def test_retriever_is_deterministic(indexed):
    prefs = {"favorite_genre": "metal", "favorite_mood": "intense",
             "target_energy": 0.95, "likes_acoustic": False}
    first = [r["id"] for r in retrieve_for_profile(prefs, k=5)]
    second = [r["id"] for r in retrieve_for_profile(prefs, k=5)]
    assert first == second


# --- optional: real end-to-end agent run (costs a few cents, needs a key) ---

@pytest.mark.skipif(
    not os.getenv("RUN_LLM_TESTS"),
    reason="set RUN_LLM_TESTS=1 to run the paid live-Claude integration test",
)
def test_agent_end_to_end_is_valid():
    from src.agent import RecommenderAgent
    from src.retriever import DEFAULT_CATALOG
    from src.recommender import load_songs

    agent = RecommenderAgent(k=5)
    result = agent.recommend({"favorite_genre": "lofi", "favorite_mood": "chill",
                              "target_energy": 0.3, "likes_acoustic": True})
    recs = result["recommendations"]
    ids = [r["id"] for r in recs]
    catalog_ids = {s["id"] for s in load_songs(DEFAULT_CATALOG)}

    assert len(recs) == 5
    assert len(ids) == len(set(ids))                 # no duplicates
    assert all(i in catalog_ids for i in ids)         # no hallucinations
    assert all(str(r["reason"]).strip() for r in recs)  # every pick explained
