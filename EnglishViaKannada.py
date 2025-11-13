import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
from io import BytesIO
import unicodedata
import time

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(
    page_title="Kannada → English Learning (Reverse)",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------- HIDE UI ---------------- #
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

# ---------------- UI ---------------- #
st.title("📝 Learn English using Kannada Input")
st.subheader("ಕನ್ನಡ → English (Reverse)")

st.markdown(
    "Enter Kannada text. You will get:\n"
    "- English translation (sentence)\n"
    "- Sentence audio\n"
    "- Word-by-word flashcards (Kannada → English)\n"
    "- Word-level audio\n"
)

kannada_text = st.text_area(
    "Enter Kannada text here:", height=150,
    placeholder="ಉದಾಹರಣೆ: ನಾನು ಹೋಟೆಲ್ಗೆ ಹೋಗುತ್ತಿದ್ದೇನೆ"
)

if st.button("Translate"):
    if not kannada_text.strip():
        st.warning("Please enter some Kannada text.")
    else:
        try:
            kannada_norm = unicodedata.normalize("NFC", kannada_text.strip())

            # ---------- Sentence Translation ----------
            english_sentence = GoogleTranslator(source="kn", target="en").translate(kannada_norm)

            # Sentence audio
            audio_sentence = make_audio_bytes(english_sentence, lang="en")

            # ---------- DISPLAY MAIN OUTPUT ----------
            st.markdown("## 🔹 Translation Results")
            st.write("### Kannada Input:")
            st.write(kannada_norm)

            st.write("### English Translation:")
            st.write(english_sentence)

            st.write("### 🔊 English Audio (Sentence)")
            st.audio(audio_sentence, format="audio/mp3")
            st.download_button(
                "Download English Audio",
                audio_sentence,
                "english_sentence.mp3",
                mime="audio/mpeg"
            )

            # ---------- Flashcards ----------
            st.markdown("---")
            st.markdown("## 🃏 Flashcards — Word-by-Word")

            kannada_words = kannada_norm.split()
            english_words = []

            # Per-word translation
            for w in kannada_words:
                try:
                    ew = GoogleTranslator(source="kn", target="en").translate(w)
                except:
                    ew = ""
                english_words.append(ew)
                time.sleep(0.05)

            for i, k_word in enumerate(kannada_words):
                e_word = english_words[i]

                # Word audio
                e_audio = make_audio_bytes(e_word, lang="en") if e_word else b""

                with st.expander(f"Word {i+1}: {k_word}", expanded=False):
                    st.write("**Kannada:**", k_word)
                    st.write("**English:**", e_word)

                    if e_audio:
                        st.audio(e_audio, format="audio/mp3")
                        st.download_button(
                            f"Download Audio (Word {i+1})",
                            e_audio,
                            f"eng_word_{i+1}.mp3",
                            mime="audio/mpeg"
                        )
                    else:
                        st.write("_No audio available._")

        except Exception as e:
            st.error(f"Error: {e}")
