# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

<!-- Describe the goal you asked the agent to accomplish -->

**Prompts used:**

<!-- Paste the key prompts you gave the agent -->

**What did the agent generate or change?**

<!-- List the files edited, code generated, or commands run -->

**What did you verify or fix manually?**

<!-- Describe anything the agent got wrong or that required human review -->

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

<!-- e.g., Strategy, Factory, Observer, etc. -->

**How did AI help you brainstorm or implement it?**

<!-- Describe the conversation or suggestions that led to your decision -->

**How does the pattern appear in your final code?**

<!-- Point to the relevant class or method -->
