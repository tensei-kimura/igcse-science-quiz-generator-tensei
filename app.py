import streamlit as st
import openai
import json

# --- OpenAI API Key ---
openai.api_key = st.secrets["OPENAI_API_KEY"]  # secrets.toml に設定

# --- ページ設定 ---
st.set_page_config(
    page_title="IGCSE Science Quiz Generator",
    page_icon="🤖",
    layout="wide"
)

# --- セッション状態 ---
if "question_sets" not in st.session_state:
    st.session_state["question_sets"] = []

# --- UI ---
st.title("🤖 IGCSE Science Quiz Generator (GPT-4)")
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
    num_questions = st.slider("Number of questions to generate", 5, 15, 10)

# --- API呼び出し関数 ---
@st.cache_data(show_spinner="Generating questions... 🤔")
def generate_questions(prompt_text: str, max_tokens: int = 1500):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.7,
            max_tokens=max_tokens
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Error calling GPT API: {e}")
        return None

# --- 問題生成 ---
if st.button("Generate Questions"):
    generate_questions.clear()  # キャッシュクリア

    prompt = ""
    if question_type == "Multiple Choice":
        prompt = f"""
        You are an IGCSE Science educator.
        Generate {num_questions} unique multiple-choice questions on the topic '{selected_subject}: {selected_topic}'.
        Include for each question:
        - "question": the question text
        - "options": list of 4 options A-D
        - "answer": the correct option letter
        - "explanation": a concise explanation
        Return strictly as a JSON array of objects, without any extra text.
        """
    else:
        prompt = f"""
        You are an IGCSE Science educator.
        Generate {num_questions} unique short-answer questions on the topic '{selected_subject}: {selected_topic}'.
        Include for each question:
        - "question": the question text
        - "model_answer": a comprehensive model answer
        Return strictly as a JSON array of objects, without any extra text.
        """

    result_text = generate_questions(prompt)
    if result_text:
        try:
            questions = json.loads(result_text)
            st.session_state["question_sets"].insert(0, {
                "subject": selected_subject,
                "topic": selected_topic,
                "type": question_type,
                "questions": questions
            })
        except json.JSONDecodeError:
            st.error("Failed to parse JSON from GPT output.")
            st.text(result_text)

# --- 生成済みクイズ表示 ---
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
    st.info("Use the sidebar to select your subject and topic, then click 'Generate Questions'.")

