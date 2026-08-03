"""
VibeCheck — Streamlit web app.

The browser face of the whole system: enter your taste, and it runs the RAG +
Claude agent (Plan -> Act -> Check) to recommend songs with reasons, then lets you
generate an original audio clip for any pick on your GPU.

Run:  streamlit run app.py
(Needs ANTHROPIC_API_KEY in .env, same as the CLI.)
"""

import os

import streamlit as st

from src.agent import RecommenderAgent
from src.audio_gen import DEFAULT_SECONDS, MAX_SECONDS, MIN_SECONDS, describe_vibe, generate_for_song
from src.retriever import DEFAULT_CATALOG
from src.recommender import load_songs

st.set_page_config(page_title="VibeCheck", page_icon="🎵", layout="centered")


# --- cached heavy resources (loaded once per session, not per interaction) ---

@st.cache_resource(show_spinner="Loading catalog + AI models...")
def get_agent() -> RecommenderAgent:
    return RecommenderAgent()


@st.cache_data
def get_options():
    songs = load_songs(DEFAULT_CATALOG)
    genres = sorted({s["genre"] for s in songs})
    moods = sorted({s["mood"] for s in songs})
    return genres, moods, len(songs)


def _index(options, value):
    return options.index(value) if value in options else 0


# --- header -----------------------------------------------------------------

st.title("🎵 VibeCheck")
st.caption("AI music recommender — RAG retrieval + Claude reasoning + local audio generation")

if not os.getenv("ANTHROPIC_API_KEY"):
    st.error("No `ANTHROPIC_API_KEY` found. Add it to your `.env` file, then reload.")
    st.stop()

genres, moods, n_songs = get_options()

# Audio controls live in the sidebar so they're always available.
with st.sidebar:
    st.header("🎧 Audio settings")
    clip_len = st.slider(
        "Clip length (seconds)", MIN_SECONDS, MAX_SECONDS, DEFAULT_SECONDS, 1,
        help="How long each generated clip is. MusicGen tops out around 30s; "
             "longer clips take a little longer to generate.",
    )


# --- taste form -------------------------------------------------------------

with st.form("taste"):
    st.subheader("Tell me your taste")
    c1, c2 = st.columns(2)
    genre = c1.selectbox("Favorite genre", genres, index=_index(genres, "pop"))
    mood = c2.selectbox("Mood", moods, index=_index(moods, "happy"))
    energy = st.slider("Energy", 0.0, 1.0, 0.70, 0.05, help="0 = calm, 1 = intense")
    acoustic = st.checkbox("I like acoustic songs")
    submitted = st.form_submit_button("Find my songs", type="primary")

if submitted:
    prefs = {
        "favorite_genre": genre,
        "favorite_mood": mood,
        "target_energy": energy,
        "likes_acoustic": acoustic,
    }
    with st.spinner("Thinking… retrieving candidates and running Claude (Plan → Act → Check)…"):
        st.session_state["result"] = get_agent().recommend(prefs)
    st.session_state["audio"] = {}  # reset any clips from a previous search


# --- results ----------------------------------------------------------------

result = st.session_state.get("result")
if not result:
    st.info(f"Pick a genre, mood, and energy above, then hit **Find my songs**. "
            f"Searching {n_songs} songs.")
    st.stop()

# The agent's reasoning trace.
with st.expander("How the agent decided (Plan → Act → Check)"):
    st.markdown(f"**Plan** — retrieval query:\n\n> _{result['query']}_")
    st.markdown(f"**Act** — retrieved **{len(result['candidates'])}** candidate songs "
                f"from the catalog, scored them, and asked Claude to pick the best.")
    verdict = result["check"].get("verdict", "approve")
    if verdict == "revise" and result["revised"]:
        st.markdown("**Check** — Claude reviewed its own list and **revised it**:")
        for issue in result["check"].get("issues", []):
            st.markdown(f"- {issue}")
    else:
        st.markdown("**Check** — Claude reviewed its own list and **approved it**. ✅")

st.subheader("Your recommendations")
audio = st.session_state.setdefault("audio", {})

for i, song in enumerate(result["recommendations"], 1):
    with st.container(border=True):
        st.markdown(f"**{i}. {song['title']}** — {song['artist']}")
        st.caption(
            f"{song['genre']} · {song['mood']} · energy {float(song['energy']):.2f} · "
            f"rule score {float(song.get('rule_score', 0)):.1f}"
        )
        st.write(song["reason"])

        if st.button(f"🎧 Generate this vibe ({clip_len}s)", key=f"gen_{song['id']}"):
            with st.spinner("Generating audio on your GPU… (the first clip also loads the model)"):
                audio[song["id"]] = generate_for_song(song, seconds=clip_len)

        if song["id"] in audio:
            st.audio(audio[song["id"]])
            st.caption(f"MusicGen prompt: _{describe_vibe(song)}_")

st.divider()
st.caption("VibeCheck is a school project — a simulation, not a real music service.")
