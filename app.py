import streamlit as st
import requests
import json

# --- Page configuration ---
st.set_page_config(
    page_title="IGCSE Science Quiz Generator",
    page_icon="🤖",
    layout="wide"
)

# --- Retrieve API info from Streamlit secrets ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]　
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key="
except KeyError:
    st.error("API key not found. Please check your `.streamlit/secrets.toml` file.")
    st.stop()

# --- API call function ---
@st.cache_data(show_spinner="Generating questions... 🤔")
def generate_questions(topic, question_type, num_questions=10):
    """
    Calls the Gemini API to generate multiple questions based on the specified topic and question type.
    """

    if question_type == "Multiple Choice":
        prompt = f"""
        You are an IGCSE Science educator.
        Create {num_questions} unique multiple-choice questions on the topic of '{topic}' at the IGCSE level.

        For each question include:
        - "question": the question text
        - "options": list of 4 options (A, B, C, D)
        - "answer": the correct option letter
        - "explanation": a concise explanation

        Return the output strictly as a JSON array of objects like this:
        [
            {{
                "question": "...",
                "options": ["A: ...", "B: ...", "C: ...", "D: ..."],
                "answer": "B",
                "explanation": "..."
            }},
            ...
        ]
        """
    else:  # Short Answer
        prompt = f"""
        You are an IGCSE Science educator.
        Create {num_questions} unique short-answer questions on the topic of '{topic}' at the IGCSE level.

        For each question include:
        - "question": the question text
        - "model_answer": a model answer

        Return the output strictly as a JSON array of objects like this:
        [
            {{
                "question": "...",
                "model_answer": "..."
            }},
            ...
        ]
        """

    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.9,
            "topP": 0.9,
            "maxOutputTokens": 2048
        }
    }

    try:
        full_api_url = API_URL + API_KEY
        response = requests.post(full_api_url, headers=headers, data=json.dumps(payload), timeout=90)
        response.raise_for_status()

        response_data = response.json()

        if "candidates" in response_data and len(response_data["candidates"]) > 0:
            response_content = response_data["candidates"][0]["content"]["parts"][0]["text"]

            # Remove markdown fences
            if response_content.strip().startswith("```json"):
                response_content = response_content.strip()[len("```json"):].strip()
            if response_content.strip().endswith("```"):
                response_content = response_content.strip()[:-len("```")].strip()

            return json.loads(response_content)
        else:
            st.error("API response was not in a valid format.")
            st.markdown(f"Raw data:\n```\n{response.text}\n```")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred during the API call: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        st.error(f"Could not parse the API response: {e}")
        st.markdown(f"Raw data:\n```\n{response.text}\n```")
        return None


# --- Build the web interface ---
st.title("🤖 IGCSE Science Quiz Generator")
st.markdown("An AI tool to generate practice questions for IGCSE Science (Biology, Chemistry, Physics).")

# Sidebar
with st.sidebar:
    st.header("Settings")
    topics = {
        "Biology": ["Cells", "Digestion", "Genetics", "Respiration", "Ecology"],
        "Chemistry": ["The Periodic Table", "Chemical Reactions", "Acids and Bases", "Organic Chemistry"],
        "Physics": ["Forces and Motion", "Electric Circuits", "Waves", "Energy", "Thermal Physics"]
    }
    selected_subject = st.selectbox("Select a subject", list(topics.keys()))
    selected_topic = st.selectbox("Select a topic", topics[selected_subject])
    question_type = st.radio("Select question type", ["Multiple Choice", "Short Answer"])
    num_questions = st.slider("How many questions to generate?", 5, 15, 10)

# --- Session State for history ---
if "question_sets" not in st.session_state:
    st.session_state["question_sets"] = []

# --- Generate question button ---
if st.button("Generate Questions", type="primary"):
    questions = generate_questions(f"{selected_subject}: {selected_topic}", question_type, num_questions)

    if questions:
        st.session_state["question_sets"].append({
            "subject": selected_subject,
            "topic": selected_topic,
            "type": question_type,
            "questions": questions
        })

# --- Display generated sets ---
for set_idx, qset in enumerate(st.session_state["question_sets"], start=1):
    st.divider()
    st.subheader(f"📚 Question Set {set_idx} - {qset['subject']}: {qset['topic']} ({qset['type']})")

    for idx, q in enumerate(qset["questions"], start=1):
        with st.expander(f"❓ Question {idx}"):
            st.markdown(f"**Question:** {q['question']}")

            if qset["type"] == "Multiple Choice":
                for opt in q["options"]:
                    st.write(opt)
                st.markdown(f"**✅ Answer:** {q['answer']}")
                st.markdown(f"**🧠 Explanation:** {q['explanation']}")
            else:
                st.markdown(f"**📝 Model Answer:** {q['model_answer']}")



