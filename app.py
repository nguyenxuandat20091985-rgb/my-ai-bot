import os
import json
import requests
import streamlit as st
from bs4 import BeautifulSoup
from litellm import completion

# ---------- Nạp API Key ----------
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

st.set_page_config(page_title="AI Trợ Lý Công Việc", page_icon="🤖")

# ---------- GIAO DIỆN ĐẸP (CSS) ----------
st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
.stApp { background: linear-gradient(180deg, #eef2ff 0%, #ffffff 55%); }
.hero-title {
    font-size: 2.5rem; font-weight: 800; letter-spacing: -0.02em;
    background: linear-gradient(90deg, #4f46e5, #8b5cf6, #ec4899);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub { color:#64748b; margin: 0.3rem 0 0.8rem 0; }
.badge {
    display:inline-block; padding:0.25rem 0.75rem; margin-right:0.4rem;
    border-radius:999px; background:#eef2ff; color:#4f46e5;
    font-size:0.8rem; font-weight:600;
}
.badge.green { background:#ecfdf5; color:#059669; }
[data-testid="stChatInput"] textarea {
    border-radius: 16px !important; border: 1.5px solid #e2e8f0 !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color:#6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown('<div class="hero-title">🤖 AI Trợ Lý Công Việc</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Trợ lý ảo người Việt — tự lướt web, tự xử lý công việc cho bạn.</div>', unsafe_allow_html=True)
st.markdown('<span class="badge green">● Đang trực tuyến</span><span class="badge">⚡ Groq Llama 3.3</span><span class="badge">🌐 Tự lướt web</span>', unsafe_allow_html=True)

MODEL = "groq/llama-3.3-70b-versatile"

# ---------- Công cụ cào web ----------
def scrape_website(url: str) -> str:
    """Truy cập một đường link website để đọc nội dung văn bản."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.extract()
        return soup.get_text(separator=' ', strip=True)[:4000]
    except Exception as e:
        return f"Lỗi cào web: {str(e)}"

tools = [
    {
        "type": "function",
        "function": {
            "name": "scrape_website",
            "description": "Truy cập một đường link website để đọc nội dung văn bản.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "Đường link đầy đủ cần truy cập"}},
                "required": ["url"]
            }
        }
    }
]

# ---------- Vòng lặp Agent ----------
def run_agent(messages):
    while True:
        response = completion(model=MODEL, messages=messages, tools=tools, tool_choice="auto")
        msg = response.choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content
        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            if name == "scrape_website":
                result = scrape_website(args.get("url", ""))
                messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": name, "content": result})

# ---------- Khởi tạo bộ nhớ ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Bạn là AI trợ lý công việc người Việt. Khi cần đọc nội dung trang web, hãy dùng tool scrape_website. Luôn trả lời bằng tiếng Việt, rõ ràng, mạch lạc."}
    ]
if "pending" not in st.session_state:
    st.session_state.pending = None

# ---------- Bảng điều khiển bên hông ----------
with st.sidebar:
    st.markdown("### ⚙️ Bảng điều khiển")
    st.markdown("**🧠 Model:** Groq Llama 3.3 70B")
    st.markdown("**🛠️ Công cụ:** 🌐 scrape_website")
    st.divider()
    st.markdown("💡 *Mẹo:* Gửi cho AI một đường link bất kỳ, nó sẽ tự đọc và tóm tắt cho bạn.")
    if st.button("🧹 Bắt đầu trò chuyện mới"):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

# ---------- Nút thao tác nhanh ----------
c1, c2 = st.columns(2)
with c1:
    if st.button("📰 Tóm tắt tin công nghệ"):
        st.session_state.pending = "Hãy vào https://vnexpress.net và tóm tắt 3 tin công nghệ nổi bật nhất hôm nay."
        st.rerun()
with c2:
    if st.button("🔗 Tóm tắt một trang web"):
        st.session_state.pending = "Hãy đọc và tóm tắt nội dung chính của trang web này: "
        st.rerun()

# ---------- Hiển thị lịch sử trò chuyện ----------
for m in st.session_state.messages:
    if m["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(m["content"])
    elif m["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(m["content"])

# ---------- Ô nhắn tin ----------
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
        with st.spinner("🤖 Đang suy nghĩ và xử lý công việc..."):
            try:
                final_text = run_agent(list(st.session_state.messages))
            except Exception as e:
                final_text = f"❌ Lỗi hệ thống: {e}"
        st.markdown(final_text)
    st.session_state.messages.append({"role": "assistant", "content": final_text})