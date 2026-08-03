"""
Agentic recommender — the Plan -> Act -> Check loop that turns retrieved songs
into explained recommendations.

Instead of a single LLM call, this runs a small *agent loop* so the system can
reason about its own output and fix it:

  1. PLAN     Turn the listener's taste into a retrieval query.
  2. RETRIEVE Pull the top candidate songs from the RAG index (src/retriever.py)
              and attach each one's rule-based score (src/recommender.py). This is
              the grounding: the LLM may ONLY recommend from these real songs.
  3. ACT      Claude reads the candidates and picks + ranks the best k, writing a
              one-sentence reason for each that references real song attributes.
  4. CHECK    Claude reviews its own list — does it match the taste? Enough
              variety? Are the reasons grounded? — and revises once if not.

Grounding + validation keep it reliable: recommended songs are matched back to
real catalog ids, hallucinated ids are dropped, and short lists are backfilled
from the rule-ranked candidates. Runs deterministically (temperature 0).

Smoke test:  python -m src.agent
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

from src.llm_client import LLMClient, LLMError
from src.recommender import score_song
from src.retriever import DEFAULT_CATALOG, build_index, profile_to_query, retrieve

# How many candidates to retrieve, and how many to finally recommend.
N_CANDIDATES = 12
TOP_K = 5

# Only these fields are shown to the LLM per candidate (compact + grounded).
_CANDIDATE_FIELDS = (
    "id", "title", "artist", "genre", "mood",
    "energy", "valence", "danceability", "acousticness", "rule_score",
)

_ACT_SYSTEM = (
    "You are VibeCheck, an expert music recommender. You recommend ONLY songs "
    "from the provided candidate list, referring to each by its integer id. Every "
    "explanation must be one short sentence that cites the song's real genre, mood, "
    "or energy. Respond with JSON only, no prose, no code fences."
)

_CHECK_SYSTEM = (
    "You are a strict reviewer of music recommendations. You judge whether a "
    "proposed list truly fits the listener and is varied and well-justified. If it "
    "can be improved, you rewrite it using ONLY the candidate ids provided. Respond "
    "with JSON only, no prose, no code fences."
)


def _extract_json(text: str) -> dict:
    """Pull a JSON object out of an LLM reply, tolerating code fences / stray text."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


class RecommenderAgent:
    """Runs the Plan -> Act -> Check loop to produce explained recommendations."""

    def __init__(
        self,
        catalog_path: str = DEFAULT_CATALOG,
        k: int = TOP_K,
        n_candidates: int = N_CANDIDATES,
        model: Optional[str] = None,
    ) -> None:
        self.catalog_path = catalog_path
        self.k = k
        self.n_candidates = n_candidates
        # temperature 0 => deterministic picks (important for the reliability tests).
        self.llm = LLMClient(model=model, temperature=0.0, max_tokens=1200)
        build_index(catalog_path)  # ensure the RAG index exists

    # --- the loop -----------------------------------------------------------

    def recommend(self, prefs: Dict) -> Dict:
        """
        Return a dict with the full agent trace:
          query, candidates, recommendations, check, revised.
        `recommendations` is the final ranked list of songs + reasons.
        """
        # 1. PLAN + 2. RETRIEVE
        query = profile_to_query(prefs)
        candidates = retrieve(query, k=self.n_candidates)
        for c in candidates:
            c["id"] = int(c["id"])
            score, _ = score_song(prefs, c)
            c["rule_score"] = round(score, 2)
        by_id = {c["id"]: c for c in candidates}

        # 3. ACT — Claude picks + explains (falls back to rule order on failure).
        picks = self._act(prefs, candidates)
        picks = self._validate(picks, candidates)

        # 4. CHECK — Claude critiques its own list and may revise once.
        check = self._check(prefs, candidates, picks, by_id)
        revised = False
        if check.get("verdict") == "revise" and check.get("revised"):
            new_picks = self._validate(check["revised"], candidates)
            if new_picks:
                picks = new_picks
                revised = True

        recommendations = self._materialize(picks, by_id)
        return {
            "query": query,
            "candidates": candidates,
            "recommendations": recommendations,
            "check": check,
            "revised": revised,
        }

    # --- steps --------------------------------------------------------------

    def _act(self, prefs: Dict, candidates: List[Dict]) -> List[Dict]:
        """Ask Claude to pick + rank + explain. Returns [{id, reason}]."""
        prompt = (
            f"Listener taste profile:\n{self._format_prefs(prefs)}\n\n"
            f"Candidate songs (recommend only from these, by id):\n"
            f"{self._format_candidates(candidates)}\n\n"
            f"Pick the {self.k} best songs for this listener and rank them best-first. "
            f"For each, write ONE short sentence saying why it fits, citing a real "
            f"attribute (genre, mood, or energy).\n"
            f'Respond with ONLY this JSON:\n'
            f'{{"recommendations": [{{"id": <int>, "reason": "<one sentence>"}}]}}'
        )
        try:
            data = _extract_json(self.llm.complete(prompt, system=_ACT_SYSTEM))
            return data.get("recommendations", [])
        except (LLMError, json.JSONDecodeError, KeyError):
            # Fallback: rank by the rule-based score, reason from the rule matches.
            ranked = sorted(candidates, key=lambda c: c["rule_score"], reverse=True)
            out = []
            for c in ranked[: self.k]:
                _, reasons = score_song(prefs, c)
                why = "; ".join(reasons) if reasons else "solid overall match for your taste"
                out.append({"id": c["id"], "reason": f"{c['genre']}/{c['mood']} pick ({why})."})
            return out

    def _check(self, prefs: Dict, candidates: List[Dict], picks: List[Dict], by_id: Dict) -> Dict:
        """Ask Claude to review its own picks and optionally revise them."""
        proposed = [
            {"id": p["id"], "title": by_id[p["id"]]["title"],
             "genre": by_id[p["id"]]["genre"], "mood": by_id[p["id"]]["mood"],
             "energy": by_id[p["id"]]["energy"], "reason": p.get("reason", "")}
            for p in picks if p["id"] in by_id
        ]
        prompt = (
            f"Listener taste profile:\n{self._format_prefs(prefs)}\n\n"
            f"Proposed recommendations:\n{json.dumps(proposed, indent=2)}\n\n"
            f"Full candidate list (you may swap in these ids if it improves the list):\n"
            f"{self._format_candidates(candidates)}\n\n"
            f"Review the proposed list for: (1) does it match the taste? (2) is there "
            f"enough variety (avoid many songs by the same artist or near-identical "
            f"picks)? (3) does each reason cite a real attribute?\n"
            f"If it is already good, approve it. If not, provide a revised ranked list "
            f"of {self.k} songs using ONLY candidate ids.\n"
            f'Respond with ONLY this JSON:\n'
            f'{{"verdict": "approve" | "revise", "issues": ["..."], '
            f'"revised": [{{"id": <int>, "reason": "<one sentence>"}}]}}'
        )
        try:
            return _extract_json(self.llm.complete(prompt, system=_CHECK_SYSTEM))
        except (LLMError, json.JSONDecodeError):
            return {"verdict": "approve", "issues": [], "revised": []}

    # --- helpers ------------------------------------------------------------

    def _validate(self, picks: List[Dict], candidates: List[Dict]) -> List[Dict]:
        """
        Keep only picks that reference a real candidate id, de-duplicated, capped
        at k. If the LLM returned too few, backfill from the rule-ranked candidates
        so we always return a full list.
        """
        valid_ids = {c["id"] for c in candidates}
        seen, cleaned = set(), []
        for p in picks:
            try:
                pid = int(p.get("id"))
            except (TypeError, ValueError):
                continue
            if pid in valid_ids and pid not in seen:
                seen.add(pid)
                cleaned.append({"id": pid, "reason": str(p.get("reason", "")).strip()})
            if len(cleaned) == self.k:
                break

        if len(cleaned) < self.k:
            for c in sorted(candidates, key=lambda c: c["rule_score"], reverse=True):
                if c["id"] not in seen:
                    seen.add(c["id"])
                    cleaned.append({"id": c["id"], "reason": "Strong overall match for your taste."})
                if len(cleaned) == self.k:
                    break
        return cleaned

    def _materialize(self, picks: List[Dict], by_id: Dict) -> List[Dict]:
        """Turn [{id, reason}] into full song dicts carrying the reason + scores."""
        out = []
        for p in picks:
            song = dict(by_id[p["id"]])
            song["reason"] = p["reason"]
            out.append(song)
        return out

    @staticmethod
    def _format_prefs(prefs: Dict) -> str:
        return (
            f"- favorite_genre: {prefs.get('favorite_genre')}\n"
            f"- favorite_mood: {prefs.get('favorite_mood')}\n"
            f"- target_energy: {prefs.get('target_energy')} (0=calm, 1=intense)\n"
            f"- likes_acoustic: {prefs.get('likes_acoustic')}"
        )

    @staticmethod
    def _format_candidates(candidates: List[Dict]) -> str:
        compact = [{k: c[k] for k in _CANDIDATE_FIELDS if k in c} for c in candidates]
        return json.dumps(compact, indent=2)


def print_result(name: str, prefs: Dict, result: Dict) -> None:
    """Human-readable CLI printout of the whole agent trace."""
    bar = "=" * 70
    print(bar)
    print(f"PROFILE: {name}")
    print(f"  {RecommenderAgent._format_prefs(prefs).replace(chr(10), ' | ')}")
    print(bar)
    print(f"PLAN  -> retrieval query: \"{result['query']}\"")
    print(f"ACT   -> {len(result['candidates'])} candidates retrieved from the RAG index")
    verdict = result["check"].get("verdict", "approve")
    issues = result["check"].get("issues", [])
    print(f"CHECK -> verdict: {verdict}" + (f" | revised: {result['revised']}" if verdict == "revise" else ""))
    for issue in issues:
        print(f"         - {issue}")
    print("\nFINAL RECOMMENDATIONS:")
    for i, s in enumerate(result["recommendations"], 1):
        print(f"  {i}. {s['title']} - {s['artist']}  [{s['genre']}/{s['mood']}, "
              f"energy {s['energy']:.2f}, rule {s.get('rule_score', 0):.1f}]")
        print(f"     {s['reason']}")
    print()


if __name__ == "__main__":
    # Phase 3 smoke test: run the full loop on one profile and show the trace.
    demo_name = "High-Energy Pop"
    demo_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.9,
        "likes_acoustic": False,
    }
    agent = RecommenderAgent()
    result = agent.recommend(demo_prefs)
    print()
    print_result(demo_name, demo_prefs, result)
    print("Phase 3 OK - agentic recommender works.")
