import streamlit as st
import json
import openai

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(
    page_title="IGCSE Science Quiz Generator",
    page_icon="🤖",
    layout="wide"
)

# --- セッションステート初期化 ---
if "question_sets" not in st.session_state:
    st.session_state["question_sets"] = []

if "all_generated_questions" not in st.session_state:
    st.session_state["all_generated_questions"] = set()  # 過去に生成した全問題

# --- UI ---
st.title("🤖 IGCSE Science Quiz Generator (GPT-4o-mini)")
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
    num_questions = st.slider("Number of questions to generate", 3, 10, 5)

# --- GPT呼び出し ---
@st.cache_data(show_spinner="Generating questions... 🤔")
def generate_questions(prompt_text: str, max_tokens: int = 1000):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an IGCSE Science educator."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.8,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error calling GPT API: {e}")
        return None

# --- GPT出力クリーン ---
def clean_gpt_json(raw_text: str) -> str:
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

# --- 質問生成ボタン ---
if st.button("Generate Questions"):
    generate_questions.clear()

    if question_type == "Multiple Choice":
        prompt = f"""
        Generate {num_questions} unique multiple-choice questions on the topic '{selected_subject}: {selected_topic}'.
        Each question must be unique. Do NOT repeat any question that has been generated before.
        Include for each question:
        - "question": the question text
        - "options": a dictionary of 4 options A-D
        - "answer": the correct option letter
        - "explanation": a concise explanation
        Return ONLY a valid JSON array. Do NOT include any explanation, markdown, or extra text.
        """
    else:
        prompt = f"""
        Generate {num_questions} unique short-answer questions on the topic '{selected_subject}: {selected_topic}'.
        Each question must be unique. Do NOT repeat any question that has been generated before.
        Include for each question:
        - "question": the question text
        - "model_answer": a comprehensive model answer
        Return ONLY a valid JSON array. Do NOT include any explanation, markdown, or extra text.
        """

    result_text = generate_questions(prompt)
    if result_text:
        cleaned_text = clean_gpt_json(result_text)
        try:
            questions = json.loads(cleaned_text)
            # --- 過去の全問題と照合してユニーク化 ---
            unique_questions = []
            for q in questions:
                q_text = q.get("question", "").strip()
                if q_text not in st.session_state["all_generated_questions"]:
                    st.session_state["all_generated_questions"].add(q_text)
                    unique_questions.append(q)
            if not unique_questions:
                st.warning("All generated questions were duplicates of previously generated ones. Try again.")
            else:
                st.session_state["question_sets"].insert(0, {
                    "subject": selected_subject,
                    "topic": selected_topic,
                    "type": question_type,
                    "questions": unique_questions
                })
        except json.JSONDecodeError as e:
            st.error("Failed to parse JSON from GPT output.")
            st.text(f"GPT output:\n{result_text}")
            st.text(f"Error details: {e}")

# --- セット表示・削除ボタン ---
if st.session_state["question_sets"]:
    st.markdown("## Generated Quizzes")
    st.markdown("---")
    
    for set_idx, qset in enumerate(st.session_state["question_sets"], start=1):
        st.subheader(f"📚 Set {set_idx} - {qset['subject']}: {qset['topic']} ({qset['type']})")
        # 削除ボタンにユニークキーを付ける
        if st.button(f"Delete Set {set_idx}", key=f"delete_{set_idx}"):
            st.session_state["question_sets"].pop(set_idx-1)
            st.experimental_rerun()
        
        for idx, q in enumerate(qset["questions"], start=1):
            st.markdown(f"### ❓ Question {idx}")
            st.markdown(f"**Question:** {q.get('question', 'N/A')}")
            
            if qset["type"] == "Multiple Choice":
                for key, value in q.get("options", {}).items():
                    st.write(f"{key}: {value}")

            with st.expander("Show Answer"):
                if qset["type"] == "Multiple Choice":
                    st.markdown(f"**✅ Answer:** {q.get('answer', 'N/A')}")
                    st.markdown(f"**🧠 Explanation:** {q.get('explanation', 'N/A')}")
                else:
                    st.markdown(f"**📝 Model Answer:** {q.get('model_answer', 'N/A')}")
else:
    st.info("Use the sidebar to select your subject and topic, then click 'Generate Questions'.")
