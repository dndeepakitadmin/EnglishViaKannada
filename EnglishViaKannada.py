import streamlit as st
from deep_translator import GoogleTranslator
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from aksharamukha.transliterate import process as aksharamukha_process
from gtts import gTTS
from io import BytesIO
import unicodedata
import time

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(
    page_title="Kannada → English (Reverse)",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------- HIDE TOOLBAR ---------------- #
hide_streamlit_style = """
<style>
#MainMenu {visibility:hidden;}
header {visibility:hidden;}
footer {visibility:hidden;}
[data-testid="stToolbar"] {visibility:hidden !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---------------- HELPERS ---------------- #
def make_audio_bytes(text: str, lang: str = "en") -> bytes:
    fp = BytesIO()
    tts = gTTS(text=text, lang=lang)
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()

def safe_aksharamukha(src: str, tgt: str, text: str) -> str:
    """Robust wrapper around aksharamukha.process with fallback to original text."""
    if not text:
        return ""
    txt = unicodedata.normalize("NFC", text)
    variants_src = [src, src.capitalize(), src.upper(), src.title(), "Latin", "ISO"]
    variants_tgt = [tgt, tgt.capitalize(), tgt.upper(), tgt.title()]
    for s in variants_src:
        for t in variants_tgt:
            try:
                out = aksharamukha_process(s, t, txt)
                if out and out.strip():
                    return out
            except Exception:
                continue
    return text  # fallback

def itrans_to_english_pron(x: str) -> str:
    """
    Convert ITRANS-like string (from Kannada) into a friendly ASCII English pronunciation.
    Heuristic rules only — intended for readable pronunciations (not phonetic dictionary).
    """
    if not x:
        return ""
    y = x.replace("A", "aa").replace("I", "ee").replace("U", "oo")
    y = y.replace("E", "ee").replace("O", "oo")
    y = y.replace(".", "")     # remove diacritic dots
    y = y.replace("M", "n").replace("H", "h")
    # common clusters
    y = y.replace("sh", "sh").replace("Sh", "sh")
    y = y.replace("Dh", "dh").replace("Th", "th")
    y = y.replace("Ch", "ch")
    return " ".join(part.lower() for part in y.split())

# ---------------- UI ---------------- #
st.title("📝 Learn English using Kannada Input")
st.subheader("ಕನ್ನಡ → English (Reverse)")

st.markdown(
    "Enter a Kannada sentence. The app will translate to English, show English in Kannada script (phonetic),\n"
    "produce a readable English pronunciation, and provide sentence + per-word audio and flashcards."
)

kannada_text = st.text_area(
    "Enter Kannada text here:",
    height=160,
    placeholder="ಉದಾಹರಣೆ: 나는 잘 지내요 (replace with Kannada) — e.g., ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ"
)

if st.button("Translate"):
    if not kannada_text.strip():
        st.warning("Please enter some Kannada text to translate.")
    else:
        try:
            kannada_norm = unicodedata.normalize("NFC", kannada_text.strip())

            # ---------- Sentence-level translation ----------
            english_sentence = GoogleTranslator(source="kn", target="en").translate(kannada_norm)

            # English in Kannada script (phonetic) using Aksharamukha
            # try Latin->Kannada / ISO->Kannada variants via safe wrapper
            english_in_kannada = safe_aksharamukha("Latin", "Kannada", english_sentence)

            # To produce a readable English phonetic:
            # 1) take english_in_kannada (Kannada script)
            # 2) transliterate Kannada -> ITRANS
            # 3) convert ITRANS -> friendly ASCII
            itr_raw = transliterate(english_in_kannada, sanscript.KANNADA, sanscript.ITRANS)
            english_readable = itrans_to_english_pron(itr_raw)

            # Sentence audio (English)
            sentence_audio = make_audio_bytes(english_sentence, lang="en")

            # ---------- Display sentence outputs ----------
            st.markdown("## 🔹 Translation Results (Sentence)")
            st.write("**Kannada Input:**")
            st.write(kannada_norm)

            st.write("**English (Translation):**")
            st.write(english_sentence)

            st.write("**English (in Kannada script - phonetic):**")
            st.write(english_in_kannada)

            st.write("**Readable English Pronunciation:**")
            st.code(english_readable)

            st.markdown("### 🔊 English Audio (Sentence)")
            st.audio(sentence_audio, format="audio/mp3")
            st.download_button("Download English sentence audio", sentence_audio, "english_sentence.mp3", mime="audio/mpeg")

            # ---------- Word-by-word flashcards ----------
            st.markdown("---")
            st.markdown("## 🃏 Flashcards — Word-by-Word (Current Input Only)")

            kannada_words = [w for w in kannada_norm.split() if w.strip()]
            if not kannada_words:
                st.info("No tokens found in Kannada input for word-level flashcards.")
            else:
                # Translate each Kannada word individually for accurate flashcards
                english_words_by_token = []
                for w in kannada_words:
                    try:
                        ew = GoogleTranslator(source="kn", target="en").translate(w)
                    except Exception:
                        ew = ""
                    english_words_by_token.append(ew)
                    time.sleep(0.05)

                for i, k_word in enumerate(kannada_words):
                    e_word = english_words_by_token[i] if i < len(english_words_by_token) else ""

                    # English in Kannada script (per word)
                    e_in_kannada = safe_aksharamukha("Latin", "Kannada", e_word) if e_word else ""

                    # Readable phonetic per word
                    itr_word = transliterate(e_in_kannada, sanscript.KANNADA, sanscript.ITRANS) if e_in_kannada else ""
                    e_readable = itrans_to_english_pron(itr_word) if itr_word else ""

                    # Word audio
                    e_word_audio = make_audio_bytes(e_word, lang="en") if e_word else b""

                    with st.expander(f"Word {i+1}: Kannada → {k_word}", expanded=False):
                        st.write("**Kannada word:**", k_word)
                        st.write("**English word:**", e_word if e_word else "(no single-word translation)")
                        st.write("**English (in Kannada script):**", e_in_kannada)
                        st.write("**Readable Pronunciation:**")
                        st.code(e_readable)

                        if e_word_audio:
                            st.audio(e_word_audio, format="audio/mp3")
                            st.download_button(
                                label=f"Download audio (word {i+1})",
                                data=e_word_audio,
                                file_name=f"eng_word_{i+1}.mp3",
                                mime="audio/mpeg"
                            )
                        else:
                            st.write("_No audio available for this token._")

        except Exception as err:
            st.error(f"Error during processing: {err}")
