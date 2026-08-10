import os
import json
import requests
import streamlit as st
from bs4 import BeautifulSoup
from litellm import completion

# Nạp key
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

st.set_page_config(
    page_title="AI Trợ Lý Công Việc",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ========== CSS ==========
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
  font-family: 'Inter', system-ui, sans-serif;
}

#MainMenu, footer, header {visibility: hidden;}

.stApp {
  background: linear-gradient(180deg, #eef2ff 0%, #f8fafc 45%, #ffffff 100%);
}

.hero-title {
  font-size: 2.35rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(90deg, #4f46e5, #7c3aed, #ec4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.25rem;
}

.hero-sub {
  color: #64748b;
  font-size: 1.05rem;
  margin-bottom: 1.2rem;
}

.badge {
  display: inline-block;
  padding: 0.28rem 0.85rem;
  margin-right: 0.45rem;
  margin-bottom: 0.4rem;
  border-radius: 999px;
  background: #e0e7ff;
  color: #4338ca;
  font-size: 0.8rem;
  font-weight: 600;
}

.badge.green {
  background: #d1fae5;
  color: #047857;
}

[data-testid="stChatInput"] textarea {
  border-radius: 18px !important;
  border: 1.5px solid #e2e8f0 !important;
  font-size: 1rem !important;
}

[data-testid="stChatInput"] textarea:focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.18) !important;
}

div[data-testid="stSidebar"] {
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
}

.stButton > button {
  border-radius: 12px;
  font-weight: 600;
  border: 1px solid #e2e8f0;
  transition: all 0.15s ease;
}

.stButton > button:hover {
  border-color: #a5b4fc;
  background: #eef2ff;
}
</style>
""", unsafe_allow_html=True)

# ========== HEADER ==========
st.markdown('<div class="hero-title">🤖 AI Trợ Lý Công Việc</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Trợ lý người Việt — tự lướt web, tự xử lý công việc.</div>', unsafe_allow_html=True)
st.markdown(
    '<span class="badge green">● Trực tuyến</span>'
    '<span class="badge">⚡ Groq Llama 3.3</span>'
    '<span class="badge">🌐 Tự cào web</span>',
    unsafe_allow_html=True
)

MODEL = "groq/llama-3.3-70b-versatile"

def scrape_website(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.extract()
        text = soup.get_text(separator=" ", strip=True)
        return text[:4500]
    except Exception as e:
        return f"Lỗi cào web: {str(e)}"

tools = [{
    "type": "function",
    "function": {
        "name": "scrape_website",
        "description": "Truy cập một đường link website để đọc nội dung văn bản.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL đầy đủ cần đọc"}
            },
            "required": ["url"]
        }
    }
}]

def run_agent(messages: list) -> str:
    while True:
        response = completion(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not getattr(msg, "tool_calls", None):
            return msg.content

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            if name == "scrape_website":
                result = scrape_website(args.get("url", ""))
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": name,
                    "content": result
                })

# ========== Session ==========
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "system",
        "content": (
            "Bạn là AI trợ lý công việc người Việt. "
            "Khi cần đọc nội dung trang web hãy dùng tool scrape_website. "
            "Luôn trả lời bằng tiếng Việt, rõ ràng, mạch lạc, hữu ích."
        )
    }]

if "pending" not in st.session_state:
    st.session_state.pending = None

# ========== Sidebar ==========
with st.sidebar:
    st.markdown("### ⚙️ Bảng điều khiển")
    st.markdown("**Model:** Groq Llama 3.3 70B")
    st.markdown("**Công cụ:** scrape_website")
    st.divider()
    st.markdown("💡 Gửi link bất kỳ, AI sẽ tự đọc và tóm tắt.")
    if st.button("🧹 Bắt đầu trò chuyện mới", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

# ========== Quick actions ==========
c1, c2 = st.columns(2)
with c1:
    if st.button("📰 Tóm tắt tin công nghệ", use_container_width=True):
        st.session_state.pending = "Hãy vào https://vnexpress.net và tóm tắt 3 tin công nghệ nổi bật nhất hôm nay."
        st.rerun()
with c2:
    if st.button("🔗 Tóm tắt trang web", use_container_width=True):
        st.session_state.pending = "Hãy đọc và tóm tắt nội dung chính của trang web này: "
        st.rerun()

# ========== Chat history ==========
for m in st.session_state.messages:
    if m["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(m["content"])
    elif m["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(m["content"])

# ========== Input ==========
prompt = st.chat_input("Nhập công việc cần AI xử lý...")
if prompt:
    st.session_state.pending = prompt

if st.session_state.pending:
    user_text = st.session_state.pending
    st.session_state.pending = None

    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_text)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Đang suy nghĩ và xử lý..."):
            try:
                final_text = run_agent(list(st.session_state.messages))
            except Exception as e:
                final_text = f"❌ Lỗi hệ thống: {e}"
        st.markdown(final_text)

    st.session_state.messages.append({"role": "assistant", "content": final_text})