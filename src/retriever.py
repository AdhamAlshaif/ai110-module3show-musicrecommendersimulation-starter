"""
RAG retriever — the "R" in Retrieval-Augmented Generation.

Before Claude recommends anything, we first *retrieve* the handful of songs most
relevant to a listener's taste out of the whole catalog. That way the LLM reasons
over a small, on-target shortlist instead of the entire CSV (which won't scale and
wastes tokens). This is exactly how real RAG systems ground an LLM in real data.

How it works:
  1. Turn each song into a short natural-language "document" (genre, mood, and its
     numeric features described in words like "high energy", "acoustic").
  2. Embed every document into a vector with a local sentence-transformers model
     (all-MiniLM-L6-v2) — runs on the GPU if one is available.
  3. Store the vectors in a local Chroma collection (persisted under .chroma/).
  4. At query time, embed the listener's taste the same way and ask Chroma for the
     nearest songs by cosine similarity.

Everything is local and free; only Phase 3's recommendation step calls Claude.

Smoke test:  python -m src.retriever
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from src.recommender import load_songs

# --- configuration ----------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
DEFAULT_CATALOG = os.path.join(PROJECT_ROOT, "data", "catalog.csv")
CHROMA_DIR = os.path.join(PROJECT_ROOT, ".chroma")
COLLECTION_NAME = "songs"
EMBED_MODEL = "all-MiniLM-L6-v2"  # small, fast, 384-dim; great for short docs

# Lazily-created singletons so importing this module is cheap.
_model = None
_client = None


# --- describing songs & tastes in words -------------------------------------

def _band(value: float, low: str, mid: str, high: str, very_high: str) -> str:
    """Map a 0..1 feature onto plain words the embedder can reason about."""
    if value < 0.35:
        return low
    if value < 0.55:
        return mid
    if value < 0.8:
        return high
    return very_high


def song_to_document(song: Dict) -> str:
    """
    Render a song as a short natural-language description. The embedding of this
    text is what we search over, so it names the genre/mood and *describes* the
    numeric features rather than dumping raw numbers.
    """
    energy = _band(song["energy"], "very calm, low energy", "gently calm energy",
                   "high energy", "very high, intense energy")
    valence = _band(song["valence"], "sad, downbeat feel", "neutral mood feel",
                    "upbeat, positive feel", "very happy, euphoric feel")
    acoustic = _band(song["acousticness"], "electronic, produced sound", "part-acoustic sound",
                     "mostly acoustic sound", "very acoustic, organic sound")
    dance = _band(song["danceability"], "not danceable", "somewhat danceable",
                  "danceable", "very danceable")
    return (
        f"{song['title']} by {song['artist']}. "
        f"A {song['mood']} {song['genre']} song. "
        f"It has {energy}, a {valence}, and a {acoustic}. "
        f"Tempo around {int(song['tempo_bpm'])} BPM, {dance}."
    )


def profile_to_query(prefs: Dict) -> str:
    """Render a listener's taste profile as a query string, symmetric to the docs."""
    energy = _band(
        float(prefs.get("target_energy", 0.5)),
        "very calm, low energy", "gently calm energy",
        "high energy", "very high, intense energy",
    )
    parts = [
        f"A {prefs.get('favorite_mood', 'any')} {prefs.get('favorite_genre', 'any')} song",
        f"with {energy}",
    ]
    if prefs.get("likes_acoustic"):
        parts.append("and a mostly acoustic sound")
    return ", ".join(parts) + "."


# --- model & vector store ---------------------------------------------------

def _get_model():
    """Load the sentence-transformers model once, on GPU when available."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        device = "cpu"
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
        except Exception:
            pass
        print(f"Loading embedding model '{EMBED_MODEL}' on {device}...")
        _model = SentenceTransformer(EMBED_MODEL, device=device)
    return _model


def _get_client():
    """Return a persistent Chroma client (stores vectors under .chroma/)."""
    global _client
    if _client is None:
        import chromadb
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client


def _embed(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts into normalized vectors (cosine-ready)."""
    model = _get_model()
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vecs]


# --- public API -------------------------------------------------------------

def build_index(catalog_path: str = DEFAULT_CATALOG, rebuild: bool = False) -> int:
    """
    Embed every song in the catalog and store it in Chroma.

    If the collection already holds exactly the catalog's songs and `rebuild` is
    False, this is a no-op (so repeated runs are fast). Returns the song count.
    """
    songs = load_songs(catalog_path)
    client = _get_client()

    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    # Skip re-embedding if the index already matches the catalog size.
    if not rebuild and collection.count() == len(songs):
        print(f"Index already built ({collection.count()} songs). Use rebuild=True to force.")
        return collection.count()

    # Fresh build: clear anything stale, then add every song.
    if collection.count() and not rebuild:
        client.delete_collection(COLLECTION_NAME)
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )

    documents = [song_to_document(s) for s in songs]
    embeddings = _embed(documents)
    ids = [str(s["id"]) for s in songs]
    # Chroma metadata values must be str/int/float/bool -> song dicts already are.
    metadatas = [dict(s) for s in songs]

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    print(f"Indexed {len(songs)} songs into Chroma collection '{COLLECTION_NAME}'.")
    return len(songs)


def retrieve(query: str, k: int = 10, where: Optional[Dict] = None) -> List[Dict]:
    """
    Return the top-k songs most similar to `query`.

    Each result is the song's metadata dict plus a `_similarity` score in 0..1
    (1 = identical direction). `where` is an optional Chroma metadata filter,
    e.g. {"genre": "lofi"}.
    """
    collection = _get_client().get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )
    if collection.count() == 0:
        build_index()

    q_emb = _embed([query])[0]
    res = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        where=where,
        include=["metadatas", "distances"],
    )
    metadatas = res.get("metadatas", [[]])[0]
    distances = res.get("distances", [[]])[0]

    out: List[Dict] = []
    for meta, dist in zip(metadatas, distances):
        song = dict(meta)
        # cosine distance -> similarity
        song["_similarity"] = round(1.0 - float(dist), 4)
        out.append(song)
    return out


def retrieve_for_profile(prefs: Dict, k: int = 10) -> List[Dict]:
    """Convenience: build a query from a taste profile and retrieve top-k songs."""
    return retrieve(profile_to_query(prefs), k=k)


if __name__ == "__main__":
    # Phase 2 smoke test: build the index, then run a few taste queries and show
    # that the retrieved songs actually match the requested vibe.
    n = build_index()
    print(f"\nCatalog indexed: {n} songs.\n")

    demos = [
        {"favorite_genre": "lofi", "favorite_mood": "chill", "target_energy": 0.3, "likes_acoustic": True},
        {"favorite_genre": "metal", "favorite_mood": "intense", "target_energy": 0.95, "likes_acoustic": False},
        {"favorite_genre": "jazz", "favorite_mood": "sad", "target_energy": 0.4, "likes_acoustic": True},
    ]
    for prefs in demos:
        print("=" * 70)
        print(f"QUERY profile: {prefs}")
        print(f"  -> \"{profile_to_query(prefs)}\"")
        for i, s in enumerate(retrieve_for_profile(prefs, k=5), 1):
            print(f"  {i}. {s['title']:<22} {s['genre']:<11} {s['mood']:<11} "
                  f"energy={s['energy']:.2f}  sim={s['_similarity']:.3f}")
        print()
    print("Phase 2 OK - retrieval works.")
