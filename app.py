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
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key="
except KeyError:
    st.error("API key not found. Please check your `.streamlit/secrets.toml` file.")
    st.stop()

# --- API call function ---
@st.cache_data(show_spinner="Generating question... 🤔")
def generate_question(topic, question_type):
    """
    Calls the Gemini API to generate a question based on the specified topic and question type.
    """
    
    # Create the prompt in English
    if question_type == "Multiple Choice":
        prompt = f"""
        You are an IGCSE Science educator.
        Create one multiple-choice question on the topic of '{topic}' at the IGCSE level.
        
        - Question
        - 4 options (A, B, C, D)
        - The correct answer (e.g., D)
        - A concise explanation
        
        Please format the output as a JSON object:
        {{
            "question": "...",
            "options": ["A: ...", "B: ...", "C: ...", "D: ..."],
            "answer": "D",
            "explanation": "..."
        }}
        """
    else: # Short Answer
        prompt = f"""
        You are an IGCSE Science educator.
        Create one short-answer question on the topic of '{topic}' at the IGCSE level.
        
        - Question
        - A model answer
        
        Please format the output as a JSON object:
        {{
            "question": "...",
            "model_answer": "..."
        }}
        """
    
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    try:
        full_api_url = API_URL + API_KEY
        response = requests.post(full_api_url, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status() 
        
        response_data = response.json()
        
        if 'candidates' in response_data and len(response_data['candidates']) > 0:
            response_content = response_data['candidates'][0]['content']['parts'][0]['text']
            
            # Remove markdown formatting more robustly
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
st.markdown("An AI tool to help with your IGCSE Science studies (Biology, Chemistry, Physics).")

# Sidebar
with st.sidebar:
    st.header("Settings")
    topics = {
        "Biology": ["Cells", "Digestion", "Genetics"],
        "Chemistry": ["The Periodic Table", "Chemical Reactions"],
        "Physics": ["Forces and Motion", "Electric Circuits"]
    }
    selected_subject = st.selectbox("Select a subject", list(topics.keys()))
    selected_topic = st.selectbox("Select a topic", topics[selected_subject])
    question_type = st.radio("Select question type", ["Multiple Choice", "Short Answer"])

# Generate question button
if st.button("Generate Question", type="primary"):
    problem_data = generate_question(f"{selected_subject}: {selected_topic}", question_type)
    
    if problem_data:
        st.divider()
        st.subheader(f"💡 Generated Question - {selected_subject}: {selected_topic}")
        
        if question_type == "Multiple Choice":
            st.markdown(f"**Question:** {problem_data['question']}")
            for option in problem_data['options']:
                st.write(option)
            
            with st.expander("Show Answer and Explanation 👀"):
                st.success(f"The correct answer is {problem_data['answer']}.")
                st.markdown(f"**Explanation:** {problem_data['explanation']}")
        else:
            st.markdown(f"**Question:** {problem_data['question']}")
            with st.expander("Show Model Answer 📝"):
                st.markdown(f"**Model Answer:** {problem_data['model_answer']}")
