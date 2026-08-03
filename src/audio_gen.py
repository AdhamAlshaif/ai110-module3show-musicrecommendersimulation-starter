"""
AI audio generation — turn a recommended song's *vibe* into an actual audio clip.

This is the showcase feature: the recommender doesn't just talk about music, it
*makes* a short original instrumental that matches the mood/genre/energy of a
pick, using Meta's MusicGen model running locally on the GPU.

We use the Hugging Face `transformers` MusicGen (not Meta's `audiocraft` package)
because it installs cleanly on Windows + modern PyTorch and needs no extra deps —
audio is written to WAV with scipy, which is already installed.

Model is chosen with the MUSICGEN_MODEL env var (default facebook/musicgen-small,
~2 GB, a few seconds per clip on a decent GPU). Clips land in outputs/ (gitignored).

Smoke test:  python -m src.audio_gen
"""

from __future__ import annotations

import os
import re
from typing import Dict, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
DEFAULT_MODEL = os.getenv("MUSICGEN_MODEL", "facebook/musicgen-small")

# MusicGen produces audio tokens at ~50 Hz, so seconds * 50 ~= max_new_tokens.
TOKENS_PER_SECOND = 50
# MusicGen is trained on ~30s windows; going past that hurts quality, so we clamp.
MIN_SECONDS = 4
MAX_SECONDS = 30
DEFAULT_SECONDS = 15

# Lazily-loaded (model, processor, sampling_rate, device) so importing is cheap.
_bundle: Optional[Tuple] = None


def _get_model():
    """Load MusicGen once, on the GPU when available."""
    global _bundle
    if _bundle is None:
        import torch
        from transformers import AutoProcessor, MusicgenForConditionalGeneration

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading MusicGen '{DEFAULT_MODEL}' on {device} (first run downloads the model)...")
        processor = AutoProcessor.from_pretrained(DEFAULT_MODEL)
        model = MusicgenForConditionalGeneration.from_pretrained(DEFAULT_MODEL).to(device)
        sampling_rate = model.config.audio_encoder.sampling_rate
        _bundle = (model, processor, sampling_rate, device)
    return _bundle


def describe_vibe(song: Dict) -> str:
    """Build a MusicGen text prompt from a song's attributes."""
    genre = song.get("genre", "pop")
    mood = song.get("mood", "upbeat")
    energy = float(song.get("energy", 0.6))
    tempo = int(float(song.get("tempo_bpm", 110)))

    if energy >= 0.7:
        energy_words = "high-energy and intense"
    elif energy < 0.45:
        energy_words = "mellow, calm and relaxed"
    else:
        energy_words = "medium-energy and steady"

    texture = (
        "acoustic with organic instruments"
        if float(song.get("acousticness", 0.0)) > 0.6
        else "modern and electronic-produced"
    )
    return (
        f"A {mood} {genre} instrumental, {energy_words}, {texture}, "
        f"around {tempo} BPM. Clean, catchy, and well-mixed."
    )


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "clip"


def _write_wav(path: str, audio, sampling_rate: int) -> None:
    """Write a mono float waveform to a 16-bit PCM WAV file."""
    import numpy as np
    from scipy.io import wavfile

    arr = np.asarray(audio, dtype="float32").squeeze()
    arr = np.clip(arr, -1.0, 1.0)
    pcm = (arr * 32767.0).astype("int16")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wavfile.write(path, sampling_rate, pcm)


def generate_clip(
    prompt: str,
    seconds: int = DEFAULT_SECONDS,
    out_path: Optional[str] = None,
    seed: Optional[int] = 0,
) -> str:
    """
    Generate an instrumental clip for `prompt` and save it as a WAV.

    `seconds` is clamped to [MIN_SECONDS, MAX_SECONDS] (MusicGen's usable range).
    Returns the path to the written file. `seed` makes generation reproducible;
    pass None for a fresh clip each call.
    """
    import torch

    seconds = max(MIN_SECONDS, min(int(seconds), MAX_SECONDS))
    model, processor, sampling_rate, device = _get_model()
    if seed is not None:
        torch.manual_seed(seed)

    inputs = processor(text=[prompt], padding=True, return_tensors="pt").to(device)
    max_new_tokens = int(seconds * TOKENS_PER_SECOND)

    with torch.no_grad():
        audio_values = model.generate(
            **inputs,
            do_sample=True,
            guidance_scale=3.0,
            max_new_tokens=max_new_tokens,
        )

    waveform = audio_values[0, 0].detach().cpu().numpy()
    out_path = out_path or os.path.join(OUTPUT_DIR, f"{_slug(prompt)[:40]}.wav")
    _write_wav(out_path, waveform, sampling_rate)
    print(f"Wrote {len(waveform) / sampling_rate:.1f}s clip -> {out_path}")
    return out_path


def generate_for_song(song: Dict, seconds: int = DEFAULT_SECONDS, seed: Optional[int] = 0) -> str:
    """Convenience: describe a song's vibe and generate a clip named after it."""
    prompt = describe_vibe(song)
    name = _slug(f"{song.get('title', 'clip')}_{song.get('genre', '')}")
    out_path = os.path.join(OUTPUT_DIR, f"{name}.wav")
    print(f"Vibe prompt: {prompt}")
    return generate_clip(prompt, seconds=seconds, out_path=out_path, seed=seed)


if __name__ == "__main__":
    # Phase 5 smoke test: generate one clip from a sample "happy pop" vibe.
    demo_song = {
        "title": "Sunrise City", "genre": "pop", "mood": "happy",
        "energy": 0.82, "tempo_bpm": 118, "acousticness": 0.18,
    }
    path = generate_for_song(demo_song, seconds=DEFAULT_SECONDS)
    print(f"\nPhase 5 OK - generated audio at: {path}")
    print("Open it in any media player to listen.")
