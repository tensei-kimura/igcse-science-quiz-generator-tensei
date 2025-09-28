import streamlit as st
import requests
import json
from typing import List, Dict, Any, Optional

# --- Configuration ---
MODEL_NAME = "gemini-2.5-flash"
API_KEY = st.secrets["GEMINI_API_KEY"]
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

# --- Page configuration ---
st.set_page_config(
    page_title="IGCSE Science Quiz Generator",
    page_icon="🤖",
    layout="wide"
)

# --- API Call Function ---
@st.cache_data(show_spinner="Generating questions... 🤔")
def generate_questions(prompt_text: str, max_output_tokens: int = 2048) -> Optional[List[Dict[str, Any]]]:
    """
    Calls Gemini 2.5-flash API to generate questions from a prompt.
    """
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ],
        "temperature": 0.7,
        "topP": 0.9,
        "maxOutputTokens": max_output_tokens
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()

        # candidates からテキストを取得
        if "candidates" in data and len(data["candidates"]) > 0:
            response_content = data["candidates"][0]["content"]["parts"][0]["text"]

            # JSON出力の前処理（Markdown フェンス削除）
            if response_content.strip().startswith("```json"):
                response_content = response_content.strip()[len("```json"):].strip()
            if response_content.strip().endswith("```"):
                response_content = response_content.strip()[:-len("```")].strip()

            try:
                return json.loads(response_content)
            except json.JSONDecodeError:
                st.warning("API出力をJSONに変換できませんでした。生データを表示します。")
                st.text(response_content)
                return None
        else:
            st.error("APIから有効なコンテンツが返ってきませんでした。")
            st.text(json.dumps(data, indent=2))
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"HTTP Error: {e}")
        return None

# --- Session State ---
if "question_sets" not in st.session_state:
    st.session_state["question_sets"] = []

# --- UI ---
st.title("🤖 IGCSE Science Quiz Generator (Gemini 2.5-flash)")
st.markdown("Generate practice questions for IGCSE Science (Biology, Chemistry, Physics).")

with st.sidebar:
    st.header("Settings")
    topics = {
        "Biology": ["Cells", "Digestion", "Genetics", "Respiration", "Ecology"],
        "Chemistry": ["The Periodic Table", "Chemical Reactions", "Acids and Bases", "Organic Chemistry"],
        "Physics": ["Forces and Motion", "Electric Circuits", "Waves", "Energy", "Thermal Physics"]
    }

    selected_subject = st.selectbox("Select a subject", list(topics.keys()))
    selected_topic = st.selectbox("Select a topic", topics.get(selected_subject, []))
    question_type = st.radio("Select question type", ["Multiple Choice", "Short Answer"])
    num_questions = st.slider("How many questions to generate?", 5, 15, 10)

# --- Generate Questions ---
if st.button("Generate Questions", type="primary"):
    generate_questions.clear()  # clear cache
    prompt = ""
    if question_type == "Multiple Choice":
        prompt = f"""
        You are an IGCSE Science educator.
        Generate {num_questions} unique multiple-choice questions on the topic '{selected_subject}: {selected_topic}'.
        Include for each:
        - question
        - options: A, B, C, D
        - answer
        - explanation
        Return strictly as JSON array.
        """
    else:
        prompt = f"""
        You are an IGCSE Science educator.
        Generate {num_questions} unique short-answer questions on the topic '{selected_subject}: {selected_topic}'.
        Include for each:
        - question
        - model_answer
        Return strictly as JSON array.
        """

    questions = generate_questions(prompt)
    if questions:
        st.session_state["question_sets"].insert(0, {
            "subject": selected_subject,
            "topic": selected_topic,
            "type": question_type,
            "questions": questions
        })

# --- Display Generated Sets ---
if st.session_state["question_sets"]:
    st.markdown("## Generated Quizzes")
    st.markdown("---")
    for set_idx, qset in enumerate(st.session_state["question_sets"], start=1):
        st.subheader(f"📚 Set {set_idx} - {qset['subject']}: {qset['topic']} ({qset['type']})")
        for idx, q in enumerate(qset["questions"], start=1):
            with st.expander(f"❓ Question {idx}"):
                st.markdown(f"**Question:** {q.get('question', 'N/A')}")
                if qset["type"] == "Multiple Choice":
                    for opt in q.get("options", []):
                        st.write(opt)
                    st.markdown(f"**✅ Answer:** {q.get('answer', 'N/A')}")
                    st.markdown(f"**🧠 Explanation:** {q.get('explanation', 'N/A')}")
                else:
                    st.markdown(f"**📝 Model Answer:** {q.get('model_answer', 'N/A')}")
else:
    st.info("Use the sidebar to select your subject and topic, then click 'Generate Questions' to begin!")
