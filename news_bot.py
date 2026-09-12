"""
Independent News Engine: safe, unique daily articles with source images and ChatBoss.
"""
from __future__ import annotations
import html, json, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from litellm import completion
from modules.config import BLOG_URL, DOCS_DIR, DATA_DIR, MODEL, TEMPERATURE, MAX_TOKENS, NEWS_SOURCES, NEWS_SAFETY_BLOCKLIST
from modules.product_manager import load_products, score_product

HEADERS={"User-Agent":"Mozilla/5.0 (compatible; MyAIBot/2.0)"}

def clean(s):
    return re.sub(r"\s+"," ",BeautifulSoup(s or "","html.parser").get_text(" ",strip=True)).strip()

def blocked(text):
    t=text.lower()
    return any(x in t for x in NEWS_SAFETY_BLOCKLIST)

def fetch_items():
    items=[]
    for source in NEWS_SOURCES:
        try:
            r=requests.get(source,headers=HEADERS,timeout=15); r.raise_for_status()
            soup=BeautifulSoup(r.content,"xml")
            for it in soup.find_all("item")[:20]:
                title=clean(it.title.text if it.title else "")
                url=clean(it.link.text if it.link else "")
                desc=clean(it.description.text if it.description else "")
                if title and url and not blocked(title+" "+desc):
                    items.append({"title":title,"url":url,"description":desc})
        except Exception:
            continue
    return items

def article_image(url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=15); r.raise_for_status()
        soup=BeautifulSoup(r.text,"html.parser")
        for attr,val in [("property","og:image"),("name","twitter:image")]:
            tag=soup.find("meta",attrs={attr:val})
            if tag and tag.get("content"): return tag["content"]
    except Exception:
        pass
    return ""

def ai_write(item,context):
    prompt=f"""Bạn là tổng biên tập một tờ báo số độc lập tiếng Việt.
Viết bài mới dựa trên nguồn bên dưới, không sao chép nguyên văn và không bịa dữ kiện.
TUYỆT ĐỐI không hướng dẫn/cổ súy hành vi vi phạm pháp luật, vũ khí, ma túy, lừa đảo,
xâm nhập trái phép, mã độc, khủng bố hoặc né tránh cơ quan chức năng.
Nếu chủ đề thuộc nhóm nguy hiểm, trả về đúng: BLOCKED.

Tiêu đề nguồn: {item['title']}
Mô tả nguồn: {item['description']}
URL nguồn: {item['url']}
Sản phẩm có thể giới thiệu cuối bài: {context}

Viết 700-1000 từ tiếng Việt. Dòng đầu là tiêu đề, sau đó các đoạn rõ ràng.
Có: Mở đầu; Điều đáng chú ý; Phân tích/ý nghĩa; Người đọc cần biết; Kết luận.
Cuối bài ghi: Nguồn tham khảo: {item['url']}
Không dùng markdown #."""
    r=completion(model=MODEL,messages=[{"role":"user","content":prompt}],temperature=TEMPERATURE,max_tokens=MAX_TOKENS)
    return r.choices[0].message.content.strip()

def history():
    p=DATA_DIR/"news_history.json"
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return []

def save_history(h):
    (DATA_DIR/"news_history.json").write_text(json.dumps(h[-500:],ensure_ascii=False,indent=2),encoding="utf-8")

def chatboss(product):
    purl=product.get("affiliate_url") or product.get("link") or "#"
    name=html.escape(product.get("name",""))
    return f"""<section class="chatboss"><div class="chatboss-head"><b>🤖 ChatBoss</b><span>Tư vấn bài báo</span></div><div class="chatboss-body"><div class="msg bot">Xin chào! Tôi có thể giải thích bài báo và tư vấn sản phẩm phù hợp.</div></div><div class="quick"><button data-q="Tóm tắt bài này">Tóm tắt</button><button data-q="Điểm chính là gì?">Điểm chính</button><button data-q="Tư vấn sản phẩm">Tư vấn sản phẩm</button></div><div class="input"><input placeholder="Hỏi ChatBoss..."><button>Gửi</button></div></section>
<script>
(()=>document.querySelectorAll('.chatboss').forEach(box=>{const body=box.querySelector('.chatboss-body');const input=box.querySelector('input');
function ask(q){{let a='Tôi có thể giải thích nội dung bài báo dựa trên thông tin đang hiển thị.';if(/sản phẩm|mua|giá/i.test(q))a='Gợi ý: <b>{name}</b><br><a href="{purl}" target="_blank" rel="nofollow sponsored">Xem sản phẩm/ưu đãi →</a>';body.insertAdjacentHTML('beforeend','<div class="msg user">'+q+'</div><div class="msg bot">'+a+'</div>');}}
box.querySelectorAll('[data-q]').forEach(b=>b.onclick=()=>ask(b.dataset.q));box.querySelector('.input button').onclick=()=>{{if(input.value.trim())ask(input.value.trim());input.value=''}};input.addEventListener('keydown',e=>{{if(e.key==='Enter')box.querySelector('.input button').click()}})}))();
</script>"""

def render(title,body,source,image,product,date,slug):
    img=f'<img class="hero-image" src="{html.escape(image,quote=True)}" alt="{html.escape(title,quote=True)}">' if image else ""
    purl=product.get("affiliate_url") or product.get("link") or "#"
    rec=f'<div class="recommend"><b>🛍️ Gợi ý</b><br>{html.escape(product.get("name",""))}<br><a href="{html.escape(purl,quote=True)}" target="_blank" rel="nofollow sponsored">Xem ưu đãi →</a></div>' if product.get("name") else ""
    paras="".join("<p>"+html.escape(x.strip())+"</p>" for x in re.split(r"\n\s*\n",body) if x.strip())
    css="""*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:#172033;font-family:Inter,system-ui,sans-serif}.wrap{max-width:900px;margin:auto;padding:18px}.mast{background:linear-gradient(135deg,#111827,#4338ca,#7c3aed);color:#fff;border-radius:26px;padding:30px;margin-bottom:20px}.mast h1{margin:0;font-size:28px}.article{background:#fff;border-radius:24px;padding:28px;box-shadow:0 12px 40px #11182712}.kicker{color:#4f46e5;font-weight:800;text-transform:uppercase;font-size:12px}.title{font-size:38px;line-height:1.15;margin:10px 0}.meta{color:#64748b}.hero-image{display:block;width:100%;max-height:470px;object-fit:cover;border-radius:18px;margin:22px 0}.body{font-size:18px;line-height:1.8}.body p{margin:0 0 18px}.recommend{margin-top:24px;padding:18px;border-radius:16px;background:#fff7ed;border:1px solid #fed7aa}.recommend a{color:#c2410c;font-weight:800;text-decoration:none}.chatboss{margin-top:28px;border:1px solid #e5e7eb;border-radius:20px;overflow:hidden;background:#fafafa}.chatboss-head{display:flex;justify-content:space-between;padding:15px 18px;background:#111827;color:#fff}.chatboss-head span{font-size:12px;opacity:.7}.chatboss-body{padding:14px;max-height:300px;overflow:auto}.msg{padding:10px 12px;border-radius:14px;margin:7px 0;max-width:90%}.msg.bot{background:#eef2ff}.msg.user{background:#e0e7ff;margin-left:auto}.quick{display:flex;gap:8px;padding:0 14px 12px;flex-wrap:wrap}.quick button,.input button{border:0;border-radius:10px;padding:9px 12px;cursor:pointer}.quick button{background:#e0e7ff;color:#3730a3}.input{display:flex;gap:8px;padding:14px;border-top:1px solid #e5e7eb}.input input{flex:1;border:1px solid #d1d5db;border-radius:12px;padding:11px}.input button{background:#4f46e5;color:#fff}@media(max-width:600px){.wrap{padding:10px}.article{padding:18px}.title{font-size:29px}.body{font-size:17px}}"""
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><meta name="description" content="{html.escape(title)}"><meta property="og:type" content="article"><meta property="og:title" content="{html.escape(title)}"><meta property="og:image" content="{html.escape(image,quote=True)}"><meta property="og:url" content="{BLOG_URL}/bai-{slug}.html"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{html.escape(image,quote=True)}"><style>{css}</style></head><body><main class="wrap"><header class="mast"><h1>Tờ Báo AI</h1><p>Tin tức độc lập • 3 số mỗi ngày</p></header><article class="article"><div class="kicker">Bản tin AI</div><h2 class="title">{html.escape(title)}</h2><div class="meta">📅 {date} • <a href="{html.escape(source,quote=True)}" rel="nofollow">Nguồn tham khảo</a></div>{img}<div class="body">{paras}</div><div class="meta">Bài được biên tập lại từ nguồn tham khảo; không sao chép nguyên văn.</div>{rec}{chatboss(product)}</article></main></body></html>"""

def main():
    h=history(); used={x.get("source_url") for x in h}; titles={x.get("title","").lower() for x in h}
    items=[x for x in fetch_items() if x["url"] not in used and x["title"].lower() not in titles]
    if not items:return
    products=sorted(load_products(),key=score_product,reverse=True); product=products[0] if products else {}
    context=product.get("name","")+" | "+(product.get("affiliate_url") or product.get("link",""))
    for item in items:
        if blocked(item["title"]+" "+item["description"]):continue
        text=ai_write(item,context)
        if text=="BLOCKED" or blocked(text):continue
        lines=[x.strip() for x in text.splitlines() if x.strip()]; title=lines[0].lstrip("#* ").strip(); body="\n\n".join(lines[1:])
        if title.lower() in titles:continue
        now=datetime.now(timezone(timedelta(hours=7))); slug=now.strftime("%Y-%m-%d-%H%M"); image=article_image(item["url"])
        page=render(title,body,item["url"],image,product,now.strftime("%d/%m/%Y %H:%M"),slug)
        for target in [DOCS_DIR/f"bai-{slug}.html",Path(f"bai-{slug}.html")]:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_text(page,encoding="utf-8")
        h.append({"slug":slug,"title":title,"source_url":item["url"],"image_url":image,"created_at":now.isoformat()});titles.add(title.lower());break
    save_history(h)

if __name__=="__main__":main()
