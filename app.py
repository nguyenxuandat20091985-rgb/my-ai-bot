import os
import json
import requests
import streamlit as st
from bs4 import BeautifulSoup
from litellm import completion

# Nạp API Key từ Streamlit Secrets
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

st.set_page_config(page_title="AI Trợ Lý Công Việc", page_icon="🤖")
st.title("🤖 AI Trợ Lý Công Việc")
st.caption("Agent Groq Llama 3.3 • Tự lướt web xử lý công việc cho anh")

MODEL = "groq/llama-3.3-70b-versatile"

# ---------- Công cụ cào web của Agent ----------
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
                "properties": {
                    "url": {"type": "string", "description": "Đường link đầy đủ cần truy cập"}
                },
                "required": ["url"]
            }
        }
    }
]

# ---------- Vòng lặp Agent (tự suy nghĩ + tự dùng tool) ----------
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

# ---------- Lịch sử hội thoại ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Bạn là AI trợ lý công việc người Việt. Khi cần đọc nội dung trang web, hãy dùng tool scrape_website. Luôn trả lời bằng tiếng Việt, rõ ràng, mạch lạc."}
    ]

for m in st.session_state.messages:
    if m["role"] in ("user", "assistant"):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# ---------- Ô nhắn tin ----------
if prompt := st.chat_input("Nhập công việc cần AI xử lý..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Đang suy nghĩ và xử lý công việc..."):
            try:
                final_text = run_agent(list(st.session_state.messages))
            except Exception as e:
                final_text = f"❌ Lỗi hệ thống: {str(e)}"
        st.markdown(final_text)
    st.session_state.messages.append({"role": "assistant", "content": final_text})