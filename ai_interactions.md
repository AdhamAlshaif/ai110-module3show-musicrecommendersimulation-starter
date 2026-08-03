# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I used Claude Code (an agentic AI coding assistant) to add a full AI layer to my
rule-based recommender: RAG retrieval, an agentic Plan → Act → Check recommender,
a reliability test suite, local MusicGen audio generation, and a Streamlit web app.
I asked it to work in phases and stop for me to test after each one.

**Prompts used:**

- "Remember the plan we made for the final project" — to re-establish context.
- Answering its scoping questions: use the Claude API, build the Scenario B web app,
  include real audio generation, and break the work into phases that stop for testing.
- Short "go" messages to approve moving on to each next phase.
- Follow-up questions like "will we have a web application?", "does it generate the
  music or play the real songs from the list?", and "make the clips longer".

**What did the agent generate or change?**

Across 7 phases it created `src/llm_client.py`, `src/retriever.py`, `src/agent.py`,
`src/audio_gen.py`, `app.py`, `data/build_catalog.py`, `tests/test_reliability.py`,
and `diagrams/architecture.mmd`; implemented the `Recommender` OOP stubs for real;
added a `--ai` mode to `main.py`; extended the tests and `src/experiment.py`; set up
the virtualenv, `.env`, and `.gitignore`; and committed + pushed after every phase.

**What did you verify or fix manually?**

I ran each phase's smoke test myself, listened to the generated audio, and rotated my
API key after it was exposed in chat. I confirmed `pytest` and the reliability report
passed, and I checked that the recommendations actually matched each taste profile
before approving the next phase.

---

## Taste Profile Critique

> Used my AI assistant to critique the user taste profile before building the scorer.

**Proposed profile ("chill lofi listener"):**

```python
user_prefs = {
    "favorite_genre": "lofi",
    "favorite_mood":  "chill",
    "target_energy":  0.4,
    "likes_acoustic": True,
}
```

**Prompt I asked:** Will these preferences let the system tell "intense rock"
apart from "chill lofi," or is the profile too narrow?

**Critique I got back:**

- **It separates opposites decisively.** Scoring against the real catalog,
  *Midnight Coding* (chill lofi) ≈ **11.96** vs *Storm Runner* (intense rock)
  ≈ **0.98** — a ~12-vs-1 gap. So the profile is not too narrow for broad tastes.
- **But it's too narrow for nuance**, in four ways:
  1. Genre is exact-string / all-or-nothing — adjacent genres (ambient, jazz)
     score 0 just like metal.
  2. Mood is exact-string too — *Focus Flow* (lofi, "focused") loses the whole
     4-point mood bonus despite being a good fit.
  3. Energy (max +2) is outweighed by genre (+5) and mood (+4), so it barely
     re-ranks songs within the same genre.
  4. `tempo_bpm`, `valence`, `danceability` go unused, and `likes_acoustic`
     is a hard cliff at 0.6.

**What I changed:** wired this profile into `src/main.py` as `user_prefs`.
Possible follow-ups: partial-credit genre/mood families, higher energy weight,
or folding in `valence`/`tempo`.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

The **Strategy pattern** — the LLM provider is a swappable strategy hidden behind one
interface. `src/llm_client.py` exposes a single `LLMClient.complete()` method, and the
rest of the code (the agent, the web app) never imports a vendor SDK directly. Today
the strategy is Claude; swapping in Gemini or Groq is a change in one file, not everywhere.

**How did AI help you brainstorm or implement it?**

I asked the agent how to keep the project from being locked into one AI vendor. It
suggested isolating all model calls behind a single client class so the provider becomes
a pluggable strategy, and noted the same idea already existed in the scoring code
(`DEFAULT_WEIGHTS` lets you swap scoring "strategies" without touching the logic).

**How does the pattern appear in your final code?**

`LLMClient.complete(prompt, system)` is the stable interface; the provider-specific logic
lives in one place (`_complete_anthropic`) and is selected by a `provider` field, so
adding a new provider means adding one branch. `src/agent.py` and `app.py` just call
`complete()` — they don't know or care which model answers.
