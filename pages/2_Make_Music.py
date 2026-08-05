"""
"Make Music" — a second page for the VibeCheck web app.

Describe any music in plain words and the AI generates it: Claude turns your
request into a MusicGen prompt, then MusicGen creates an original instrumental
clip on the GPU. Streamlit auto-adds any file in `pages/` to the app's sidebar
nav, so this shows up alongside the recommender.

Note: MusicGen makes instrumental music only — it does not sing or reproduce any
real person's voice (see the guardrail in src/audio_gen.music_prompt_from_text).
"""

import os

import streamlit as st

from src.audio_gen import (
    DEFAULT_SECONDS,
    MAX_SECONDS,
    MIN_SECONDS,
    generate_clip,
    music_prompt_from_text,
)
from src.llm_client import LLMClient

st.set_page_config(page_title="Make Music", page_icon="🎹")


@st.cache_resource(show_spinner=False)
def get_llm() -> LLMClient:
    # A little creative freedom when turning a request into a music prompt.
    return LLMClient(temperature=0.4, max_tokens=120)


st.title("🎹 Make Music")
st.caption("Describe any music in plain words — the AI writes a prompt and generates it on your GPU.")

if not os.getenv("ANTHROPIC_API_KEY"):
    st.error("No `ANTHROPIC_API_KEY` found. Add it to your `.env` file, then reload.")
    st.stop()

EXAMPLES = [
    "a traditional Arabic oud solo, slow and emotional",
    "lofi hip-hop with rain in the background",
    "epic orchestral battle music",
    "happy ukulele beach music",
]
st.write("**Try:** " + "  ·  ".join(f"`{e}`" for e in EXAMPLES))

with st.sidebar:
    st.header("🎧 Audio settings")
    clip_len = st.slider("Clip length (seconds)", MIN_SECONDS, MAX_SECONDS, DEFAULT_SECONDS, 1)

request = st.text_area(
    "What should I make?",
    placeholder="e.g. a calm oud melody for a desert night",
    height=90,
)

if st.button("🎬 Make it", type="primary"):
    if not request.strip():
        st.warning("Type a description first.")
    else:
        with st.spinner("Claude is writing a music prompt…"):
            prompt = music_prompt_from_text(request, llm=get_llm())
        st.markdown(f"**Prompt used:** _{prompt}_")
        with st.spinner("Generating audio on your GPU… (the first clip also loads the model)"):
            path = generate_clip(
                prompt,
                seconds=clip_len,
                out_path=os.path.join("outputs", "custom_clip.wav"),
                seed=None,  # fresh clip each time
            )
        st.audio(path)

st.divider()
st.caption(
    "MusicGen generates original **instrumental** music. It does not sing or copy "
    "any real person's voice — requests that name a real artist are turned into that "
    "style as an instrumental."
)
