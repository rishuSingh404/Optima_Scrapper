# streamlit_app.py

import os
import json
import tempfile
from pathlib import Path

import streamlit as st
from streamlit_option_menu import option_menu

from scraper_module import run_scraper_and_return_dict


st.set_page_config(
    page_title="Optima QEA Scraper",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #121212;
        color: #EEE;
    }
    [data-testid="stSidebar"] {
        background-color: #1F1F1F;
        padding-top: 1rem;
    }
    header {
        visibility: hidden;
    }
    .block-container {
        padding-top: 0rem;
    }
    button[kind="primary"] {
        background-color: #9C27B0 !important;
        color: white !important;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 0.6em 1.4em;
        transition: background-color 0.3s ease, transform 0.2s ease;
    }
    button[kind="primary"]:hover {
        background-color: #BA68C8 !important;
        transform: scale(1.03);
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background-color: #212121;
        color: #EEE;
        border: 1px solid #444;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;flex-direction:column;align-items:center;margin-bottom:1rem;">
            <img src="https://raw.githubusercontent.com/your-repo/your-logo-path/main/logo.png" width="150" alt="Optima Logo">
        </div>
        <div style="color:white;">
            <h3 style="margin-bottom:0.2em;">Optima QEA Scraper</h3>
            <p style="margin-top:0; font-size:0.9em;">Enter parameters below and generate JSON</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected = option_menu(
        menu_title=None,
        options=["Scrape Questions"],
        icons=["cloud-download"],
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding": "0", "background-color": "#1F1F1F"},
            "icon": {"font-size": "20px", "color": "#9C27B0"},
            "nav-link": {"font-size": "16px", "color": "#ECECEC", "text-align": "left"},
            "nav-link-selected": {"background-color": "#9C27B0", "color": "#FFF", "font-weight": "bold"},
        },
    )

if selected == "Scrape Questions":
    st.header("📥 Scrape Optima QEA Questions JSON")

    st.markdown(
        """
        Enter the exact values you see on the Optima/QEA website for each field below,
        then click **Run Scraper**. The app will run a headless browser in the background,
        log in automatically, navigate to your chapter, scrape all questions, and return a
        downloadable JSON file that includes question text, options (A–D), correct answers,
        and any embedded images (as base64).
        """
    )

    AREA_TEXT = st.text_input(
        label="AREA_TEXT",
        value="Quantitative Ability",
        help="E.g., “Quantitative Ability” or “Verbal Ability”"
    )

    LEVEL = st.number_input(
        label="LEVEL (integer)",
        min_value=1,
        value=1,
        step=1,
        help="Enter 1 for Level 1, 2 for Level 2, etc."
    )

    CHAPTER_NAME = st.text_input(
        label="CHAPTER_NAME",
        value="Quadratic Equations",
        help="Exact chapter name as shown on the website"
    )

    DIFFICULTY = st.text_input(
        label="DIFFICULTY",
        value="Foundation (Topic-based)",
        help="E.g., “Foundation (Topic-based)” or “Advanced”"
    )

    run_button = st.button("Run Scraper", type="primary")

    if run_button:
        missing = []
        if not AREA_TEXT.strip():
            missing.append("AREA_TEXT")
        if not CHAPTER_NAME.strip():
            missing.append("CHAPTER_NAME")
        if not DIFFICULTY.strip():
            missing.append("DIFFICULTY")

        if missing:
            st.error(f"Please fill in: {', '.join(missing)}")
            st.stop()

        with st.spinner("Launching headless browser and scraping…"):
            try:
                results = run_scraper_and_return_dict(
                    area_text=AREA_TEXT,
                    level=int(LEVEL),
                    chapter_name=CHAPTER_NAME,
                    difficulty=DIFFICULTY
                )

                tmp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix="_optima.json",
                    mode="w",
                    encoding="utf-8"
                )
                json.dump(results, tmp_file, ensure_ascii=False, indent=2)
                tmp_file.close()

            except Exception as e:
                st.error(f"❌ Scraping failed: {e}")
                st.stop()

        st.success("✅ Scraping completed!")

        if len(results) > 0:
            st.markdown("**Preview of first 3 questions:**")
            st.json(results[:3])

        with open(tmp_file.name, "rb") as f:
            st.download_button(
                label="⬇️ Download JSON",
                data=f,
                file_name=f"{CHAPTER_NAME.replace(' ', '_')}_level{LEVEL}.json",
                mime="application/json",
            )
