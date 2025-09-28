import streamlit as st
import json
import requests

# --- 設定 ---
MODEL_NAME = "gemini-2.5-flash"
API_KEY = st.secrets["GEMINI_API_KEY"]
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

# --- ページ設定 ---
st.set_page_config(
    page_title="IGCSE サイエンス クイズジェネレーター",
    page_icon="🤖",
    layout="wide"
)

# --- API 呼び出し関数 ---
@st.cache_data(show_spinner="クイズを生成中... 🤔")
def generate_questions(prompt_text: str, max_output_tokens: int = 2048):
    """
    Gemini 2.5‑flash API を呼び出し、プロンプトからクイズを生成する関数。
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

# --- セッション状態 ---
if "question_sets" not in st.session_state:
    st.session_state["question_sets"] = []

# --- UI ---
st.title("🤖 IGCSE サイエンス クイズジェネレーター (Gemini 2.5‑flash)")
st.markdown("IGCSE サイエンス（生物、化学、物理）の練習問題を生成します。")

with st.sidebar:
    st.header("設定")
    topics = {
        "生物学": ["細胞", "消化", "遺伝学", "呼吸", "生態学"],
        "化学": ["周期表", "化学反応", "酸と塩基", "有機化学"],
        "物理学": ["力と運動", "電気回路", "波", "エネルギー", "熱物理学"]
    }

    selected_subject = st.selectbox("教科を選択", list(topics.keys()))
    selected_topic = st.selectbox("トピックを選択", topics.get(selected_subject, []))
    question_type = st.radio("問題の種類を選択", ["選択式", "記述式"])
    num_questions = st.slider("生成する問題数", 5, 15, 10)

# --- 問題生成 ---
if st.button("問題を生成", type="primary"):
    generate_questions.clear()  # キャッシュをクリア
    prompt = ""
    if question_type == "選択式":
        prompt = f"""
        あなたは IGCSE サイエンスの教育者です。
        トピック「{selected_subject}: {selected_topic}」に関する {num_questions} 問のユニークな選択式問題を生成してください。
        各問題には以下を含めてください：
        - 問題文
        - 選択肢：A, B, C, D
        - 正解
        - 解説
        出力は JSON 配列形式で厳密に返してください。
        """
    else:
        prompt = f"""
        あなたは IGCSE サイエンスの教育者です。
        トピック「{selected_subject}: {selected_topic}」に関する {num_questions} 問のユニークな記述式問題を生成してください。
        各問題には以下を含めてください：
        - 問題文
        - 模範解答
        出力は JSON 配列形式で厳密に返してください。
        """

    questions = generate_questions(prompt)
    if questions:
        st.session_state["question_sets"].insert(0, {
            "subject": selected_subject,
            "topic": selected_topic,
            "type": question_type,
            "questions": questions
        })

# --- 生成されたセットの表示 ---
if st.session_state["question_sets"]:
    st.markdown("## 生成されたクイズ")
    st.markdown("---")
    for set_idx, qset in enumerate(st.session_state["question_sets"], start=1):
        st.subheader(f"📚 セット {set_idx} - {qset['subject']}: {qset['topic']} ({qset['type']})")
        for idx, q in enumerate(qset["questions"], start=1):
            with st.expander(f"❓ 問題 {idx}"):
                st.markdown(f"**問題文:** {q.get('question', 'N/A')}")
                if qset["type"] == "選択式":
                    for opt in q.get("options", []):
                        st.write(opt)
                    st.markdown(f"**✅ 正解:** {q.get('answer', 'N/A')}")
                    st.markdown(f"**🧠 解説:** {q.get('explanation', 'N/A')}")
                else:
                    st.markdown(f"**📝 模範解答:** {q.get('model_answer', 'N/A')}")
else:
    st.info("サイドバーで教科とトピックを選択し、「問題を生成」をクリックしてください。")
