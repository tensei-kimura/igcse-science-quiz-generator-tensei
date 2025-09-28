import streamlit as st
import requests
import json
from typing import List, Dict, Any, Optional

# --- Configuration Constants ---
BASE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/"
MODEL_NAME = "gemini-2.5-flash" # Define the model name separately for clarity

# --- Page configuration ---
st.set_page_config(
    page_title="IGCSE Science Quiz Generator",
    page_icon="🤖",
    layout="wide"
)

# --- API Key Check ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("API key not found. Please check your `.streamlit/secrets.toml` file. "
             "It should contain a key named `GEMINI_API_KEY`.")
    st.stop()

# --- API call function ---
@st.cache_data(show_spinner="Generating questions... 🤔")
def generate_questions(
    topic: str,
    question_type: str,
    num_questions: int
) -> Optional[List[Dict[str, Any]]]:
    """
    Calls the Gemini API to generate multiple questions based on the specified topic and question type.
    """
    
    # 1. Construct the complete URL
    full_api_url = f"{BASE_API_URL}{MODEL_NAME}:generateContent?key={API_KEY}"

    # 2. Define the prompt based on question type
    if question_type == "Multiple Choice":
        prompt = f"""
        You are an IGCSE Science educator.
        Create {num_questions} unique multiple-choice questions on the topic of '{topic}' at the IGCSE level.

        For each question include:
        - "question": the question text
        - "options": list of 4 options (A, B, C, D)
        - "answer": the correct option letter
        - "explanation": a concise explanation

        Return the output strictly as a JSON array of objects. Do not include any surrounding markdown fences (```json) or prose.
        """
    else:  # Short Answer
        prompt = f"""
        You are an IGCSE Science educator.
        Create {num_questions} unique short-answer questions on the topic of '{topic}' at the IGCSE level.

        For each question include:
        - "question": the question text
        - "model_answer": a comprehensive model answer suitable for an IGCSE grading scheme.

        Return the output strictly as a JSON array of objects. Do not include any surrounding markdown fences (```json) or prose.
        """

    headers = {"Content-Type": "application/json"}
    
    # 3. Define the payload - ***CORRECTED FOR 400 ERROR***
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        # API parameters are placed at the root level alongside 'contents'
        "temperature": 0.9,
        "topP": 0.9,
        "maxOutputTokens": 2048
    }

    try:
        # 4. Make the API request
        response = requests.post(full_api_url, headers=headers, data=json.dumps(payload), timeout=90)
        
        # Check for HTTP errors (4xx or 5xx)
        response.raise_for_status()

        response_data = response.json()

        # 5. Extract content and parse JSON
        if "candidates" in response_data and len(response_data["candidates"]) > 0:
            response_content = response_data["candidates"][0]["content"]["parts"][0]["text"]

            # Robust cleanup for markdown fences
            if response_content.strip().startswith("```json"):
                response_content = response_content.strip()[len("```json"):].strip()
            if response_content.strip().endswith("```"):
                response_content = response_content.strip()[:-len("```")].strip()

            return json.loads(response_content)
        else:
            # Handle cases where the API call succeeds but returns no content 
            st.error("API call succeeded but returned no valid content. The response might have been blocked due to safety settings or was empty.")
            st.markdown(f"Raw response:\n```json\n{json.dumps(response_data, indent=2)}\n```")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"An **HTTP Error** occurred during the API call: {e}")
        st.info("💡 **Troubleshooting Tip:** For a **400 Bad Request**, check the request JSON payload structure. For other errors, ensure the API Key is valid and the model is correct.")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        st.error(f"Could not parse the JSON response from the model: {e}")
        st.markdown(f"Raw data (check for invalid JSON): \n```\n{response.text}\n```")
        return None

# --- Application Logic ---
# --- Session State for history ---
if "question_sets" not in st.session_state:
    st.session_state["question_sets"] = []

# --- Build the web interface ---
st.title("🤖 IGCSE Science Quiz Generator")
st.markdown("An AI tool to generate practice questions for IGCSE Science (Biology, Chemistry, Physics).")

# --- Sidebar for settings ---
with st.sidebar:
    st.header("Settings")
    topics = {
        "Biology": ["Cells", "Digestion", "Genetics", "Respiration", "Ecology"],
        "Chemistry": ["The Periodic Table", "Chemical Reactions", "Acids and Bases", "Organic Chemistry"],
        "Physics": ["Forces and Motion", "Electric Circuits", "Waves", "Energy", "Thermal Physics"]
    }
    selected_subject = st.selectbox("Select a subject", list(topics.keys()))
    
    # Ensure the topic list is dynamic based on the subject
    selected_topic = st.selectbox("Select a topic", topics.get(selected_subject, [])) 
    
    question_type = st.radio("Select question type", ["Multiple Choice", "Short Answer"])
    num_questions = st.slider("How many questions to generate?", 5, 15, 10)

# --- Generate question button ---
if st.button("Generate Questions", type="primary"):
    # Clear cache to ensure fresh generation if topic/settings changed
    generate_questions.clear() 
    
    questions = generate_questions(f"{selected_subject}: {selected_topic}", question_type, num_questions)

    if questions:
        # Use insert(0) to put new set at the top
        st.session_state["question_sets"].insert(0, { 
            "subject": selected_subject,
            "topic": selected_topic,
            "type": question_type,
            "questions": questions
        })

# --- Display generated sets ---
if st.session_state["question_sets"]:
    st.markdown("## Generated Quizzes")
    st.markdown("---")
    
    for set_idx, qset in enumerate(st.session_state["question_sets"], start=1):
        st.subheader(f"📚 Set {set_idx} - {qset['subject']}: {qset['topic']} ({qset['type']})")

        # Use st.container and st.expander for a clean display
        quiz_container = st.container(border=True)
        
        for idx, q in enumerate(qset["questions"], start=1):
            with quiz_container.expander(f"❓ Question {idx}"):
                st.markdown(f"**Question:** {q['question']}")

                if qset["type"] == "Multiple Choice":
                    # Display options clearly
                    for opt in q.get("options", []):
                        st.write(opt)
                    st.markdown(f"**--- Answer ---**")
                    st.markdown(f"**✅ Correct Option:** **{q.get('answer', 'N/A')}**")
                    st.markdown(f"**🧠 Explanation:** {q.get('explanation', 'No explanation provided.')}")
                else:
                    st.markdown(f"**--- Model Answer ---**")
                    st.markdown(f"**📝 Model Answer:** {q.get('model_answer', 'No model answer provided.')}")
        
        st.markdown("---")

else:
    st.info("Use the sidebar to select your subject and topic, then click 'Generate Questions' to begin!")

