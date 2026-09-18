"""
Independent News Engine: safe, unique daily articles with source images and ChatBoss.
"""
from __future__ import annotations
import html, json, re
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from litellm import completion
from modules.config import BLOG_URL, DOCS_DIR, DATA_DIR, MODEL, TEMPERATURE, MAX_TOKENS, NEWS_SOURCES, NEWS_SAFETY_BLOCKLIST
from modules.product_manager import load_products, score_product
from modules.accesstrade import client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

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

def ai_write(product):
    name=product.get("name","")
    highlights=product.get("highlights","")
    audience=product.get("audience","")
    prompt=f"""Bạn là biên tập viên của Tờ Báo AI chuyên viết bài tiêu dùng và review sản phẩm.
Bài báo phải xoay quanh đúng sản phẩm bên dưới. Không viết tin thời sự chung và không biến thành trang Chợ Deal.
Không bịa thông số, giá, giảm giá, thương hiệu, công dụng hoặc trải nghiệm chưa được cung cấp.
Chỉ sử dụng các dữ kiện trong tên, điểm nổi bật và đối tượng phù hợp.
Không đưa ra cam kết sức khỏe, tài chính hoặc hiệu quả tuyệt đối.
Sản phẩm:
- Tên: {name}
- Điểm nổi bật được cung cấp: {highlights}
- Đối tượng phù hợp: {audience}

Viết 700-1000 từ tiếng Việt theo phong cách một bài báo tiêu dùng dễ đọc.
Cấu trúc: tiêu đề hấp dẫn nhưng trung thực; mở bài; sản phẩm giải quyết nhu cầu nào; các điểm đáng chú ý; ai phù hợp; điều cần kiểm tra trước khi mua; kết luận.
Không dùng markdown #, không chèn link và không tự tạo thông tin ngoài dữ liệu trên.
"""
    r=completion(model=MODEL,messages=[{"role":"user","content":prompt}],temperature=TEMPERATURE,max_tokens=MAX_TOKENS)
    return r.choices[0].message.content.strip()

def _fingerprint(text):
    import hashlib
    normalized=re.sub(r"[^a-z0-9\\s]"," ",(text or "").lower())
    normalized=re.sub(r"\\s+"," ",normalized).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20]

def _topic_key(title):
    words=re.findall(r"[a-zA-ZÀ-ỹĐđ0-9]{4,}",(title or "").lower())
    return " ".join(sorted(set(words))[:8])

def history():
    p=DATA_DIR/"news_fingerprints.json"
    try:
        data=json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data,list) else []
    except Exception:
        return []

def save_history(h):
    # Chỉ lưu dấu vết chống trùng: hash tiêu đề/nguồn + chủ đề; KHÔNG lưu nội dung bài.
    (DATA_DIR/"news_fingerprints.json").write_text(json.dumps(h[-1000:],ensure_ascii=False,indent=2),encoding="utf-8")

def chatboss(product):
    purl=product.get("affiliate_url") or product.get("link") or "#"
    name=html.escape(product.get("name",""))
    # Không dùng f-string cho JavaScript để tránh Python hiểu nhầm { } của JS.
    js = """<script>
(()=>document.querySelectorAll('.chatboss').forEach(box=>{
  const body=box.querySelector('.chatboss-body');
  const input=box.querySelector('input');
  function ask(q){
    let a='Tôi có thể giải thích nội dung bài báo dựa trên thông tin đang hiển thị.';
    if(/sản phẩm|mua|giá/i.test(q)){
      a='Gợi ý: <b>__PRODUCT_NAME__</b><br><a href="__PRODUCT_URL__" target="_blank" rel="nofollow sponsored">Xem sản phẩm/ưu đãi →</a>';
    }
    body.insertAdjacentHTML('beforeend','<div class="msg user">'+q+'</div><div class="msg bot">'+a+'</div>');
  }
  box.querySelectorAll('[data-q]').forEach(b=>b.onclick=()=>ask(b.dataset.q));
  box.querySelector('.input button').onclick=()=>{
    if(input.value.trim()) ask(input.value.trim());
    input.value='';
  };
  input.addEventListener('keydown',e=>{
    if(e.key==='Enter') box.querySelector('.input button').click();
  });
}));
</script>"""
    return """<section class="chatboss"><div class="chatboss-head"><b>🤖 ChatBoss</b><span>Tư vấn bài báo</span></div><div class="chatboss-body"><div class="msg bot">Xin chào! Tôi có thể giải thích bài báo và tư vấn sản phẩm phù hợp.</div></div><div class="quick"><button data-q="Tóm tắt bài này">Tóm tắt</button><button data-q="Điểm chính là gì?">Điểm chính</button><button data-q="Tư vấn sản phẩm">Tư vấn sản phẩm</button></div><div class="input"><input placeholder="Hỏi ChatBoss..."><button>Gửi</button></div></section>""" + js.replace("__PRODUCT_NAME__", name).replace("__PRODUCT_URL__", html.escape(purl,quote=True))

def render(title,body,source,image,product,date,slug):
    img=f'<img class="hero-image" src="{html.escape(image,quote=True)}" alt="{html.escape(title,quote=True)}">' if image else ""
    purl=product.get("affiliate_url") or product.get("link") or "#"
    rec=f'<div class="recommend"><b>🛍️ Gợi ý</b><br>{html.escape(product.get("name",""))}<br><a href="{html.escape(purl,quote=True)}" target="_blank" rel="nofollow sponsored">Xem ưu đãi →</a></div>' if product.get("name") else ""
    paras="".join("<p>"+html.escape(x.strip())+"</p>" for x in re.split(r"\n\s*\n",body) if x.strip())
    css="""*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:#172033;font-family:Inter,system-ui,sans-serif}.wrap{max-width:900px;margin:auto;padding:18px}.mast{background:linear-gradient(135deg,#111827,#4338ca,#7c3aed);color:#fff;border-radius:26px;padding:30px;margin-bottom:20px}.mast h1{margin:0;font-size:28px}.article{background:#fff;border-radius:24px;padding:28px;box-shadow:0 12px 40px #11182712}.kicker{color:#4f46e5;font-weight:800;text-transform:uppercase;font-size:12px}.title{font-size:38px;line-height:1.15;margin:10px 0}.meta{color:#64748b}.hero-image{display:block;width:100%;max-height:470px;object-fit:cover;border-radius:18px;margin:22px 0}.body{font-size:18px;line-height:1.8}.body p{margin:0 0 18px}.recommend{margin-top:24px;padding:18px;border-radius:16px;background:#fff7ed;border:1px solid #fed7aa}.recommend a{color:#c2410c;font-weight:800;text-decoration:none}.chatboss{margin-top:28px;border:1px solid #e5e7eb;border-radius:20px;overflow:hidden;background:#fafafa}.chatboss-head{display:flex;justify-content:space-between;padding:15px 18px;background:#111827;color:#fff}.chatboss-head span{font-size:12px;opacity:.7}.chatboss-body{padding:14px;max-height:300px;overflow:auto}.msg{padding:10px 12px;border-radius:14px;margin:7px 0;max-width:90%}.msg.bot{background:#eef2ff}.msg.user{background:#e0e7ff;margin-left:auto}.quick{display:flex;gap:8px;padding:0 14px 12px;flex-wrap:wrap}.quick button,.input button{border:0;border-radius:10px;padding:9px 12px;cursor:pointer}.quick button{background:#e0e7ff;color:#3730a3}.input{display:flex;gap:8px;padding:14px;border-top:1px solid #e5e7eb}.input input{flex:1;border:1px solid #d1d5db;border-radius:12px;padding:11px}.input button{background:#4f46e5;color:#fff}@media(max-width:600px){.wrap{padding:10px}.article{padding:18px}.title{font-size:29px}.body{font-size:17px}}"""
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><meta name="description" content="{html.escape(title)}"><meta property="og:type" content="article"><meta property="og:title" content="{html.escape(title)}"><meta property="og:image" content="{html.escape(image,quote=True)}"><meta property="og:url" content="{BLOG_URL}/bai-{slug}.html"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{html.escape(image,quote=True)}"><style>{css}</style></head><body><main class="wrap"><header class="mast"><h1>Tờ Báo AI</h1><p>Tin tức độc lập • 3 số mỗi ngày</p></header><article class="article"><div class="kicker">Bản tin AI</div><h2 class="title">{html.escape(title)}</h2><div class="meta">📅 {date} • <a href="{html.escape(source,quote=True)}" rel="nofollow">Nguồn tham khảo</a></div>{img}<div class="body">{paras}</div><div class="meta">Bài được biên tập lại từ nguồn tham khảo; không sao chép nguyên văn.</div>{rec}{chatboss(product)}</article></main></body></html>"""

def sync_accesstrade():
    try:
        campaigns=client.get_campaigns()
        (DATA_DIR/"accesstrade_campaigns.json").write_text(json.dumps(campaigns,ensure_ascii=False,indent=2),encoding="utf-8")
        promos=client.get_promos()
        (DATA_DIR/"accesstrade_promos.json").write_text(json.dumps(promos,ensure_ascii=False,indent=2),encoding="utf-8")
        return campaigns, promos
    except Exception:
        return [], []

def render_home(articles):
    cards=[]
    for x in articles:
        title=html.escape(x.get("title","Bản tin"))
        image=x.get("image_url","")
        body=x.get("body","")
        paras="".join("<p>"+html.escape(p.strip())+"</p>" for p in re.split(r"\\n\\s*\\n",body) if p.strip())
        img=f'<img src="{html.escape(image,quote=True)}" alt="{title}" loading="lazy">' if image else ""
        source=html.escape(x.get("source_url",""),quote=True)
        product_name=html.escape(x.get("product_name",""))
        product_url=html.escape(x.get("product_url",""),quote=True)
        product_box=(f'<div class="product-box"><b>🛍️ Sản phẩm trong bài</b><br>{product_name}<br><a href="{product_url}" target="_blank" rel="nofollow sponsored">XEM SẢN PHẨM →</a></div>' if product_name and product_url else "")
        cards.append(f'<article><div class="kicker">Báo sản phẩm</div><h2>{title}</h2><div class="meta">📅 {x.get("created_at","")}</div>{img}<div class="body">{paras}</div>{product_box}<p class="source">Tờ Báo AI viết độc lập dựa trên thông tin sản phẩm đã cung cấp.</p></article>')
    css="""*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:#172033;font-family:Inter,system-ui,sans-serif}.wrap{max-width:1000px;margin:auto;padding:18px}.mast{background:linear-gradient(135deg,#111827,#4338ca,#7c3aed);color:#fff;border-radius:26px;padding:30px;margin-bottom:20px}.mast h1{margin:0;font-size:30px}.mast p{margin-bottom:0;opacity:.85}.grid{display:grid;gap:20px}.article{background:#fff;border-radius:24px;padding:26px;box-shadow:0 12px 40px #11182712}.kicker{color:#4f46e5;font-weight:800;text-transform:uppercase;font-size:12px}.article h2{font-size:30px;line-height:1.2;margin:8px 0}.meta,.source{color:#64748b;font-size:13px}.hero{display:block;width:100%;max-height:430px;object-fit:cover;border-radius:18px;margin:18px 0}.body{font-size:17px;line-height:1.8}.body p{margin:0 0 16px}.source a{color:#4338ca;word-break:break-all}.product-box{margin-top:20px;padding:16px;border:1px solid #fed7aa;border-radius:16px;background:#fff7ed}.product-box a{display:inline-block;margin-top:8px;color:#c2410c;font-weight:800;text-decoration:none}@media(max-width:600px){.wrap{padding:10px}.article{padding:18px}.article h2{font-size:25px}}"""
    page=f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tờ Báo AI</title><style>{css}</style></head><body><main class="wrap"><header class="mast"><h1>📰 Tờ Báo AI</h1><p>Báo chuyên sản phẩm • mỗi số tập trung một sản phẩm • Chợ Deal hoạt động riêng tại market.html</p></header><section class="grid">{"".join(cards)}</section></main></body></html>'
    DOCS_DIR.mkdir(parents=True,exist_ok=True)
    (DOCS_DIR/"index.html").write_text(page,encoding="utf-8")

def main():
    # Tờ Báo và Chợ Deal là hai khu riêng:
    # Tờ Báo chỉ xuất bản bài viết chuyên sâu về sản phẩm và gắn link sản phẩm.
    # Chợ Deal vẫn dùng market.html và không được trộn vào nội dung báo.
    products=sorted(load_products(),key=score_product,reverse=True)
    safe_products=[p for p in products if not blocked(p.get("name","")+" "+p.get("highlights","")) and not any(k in (p.get("name","")+" "+p.get("highlights","")).lower() for k in ["vay ","tín dụng","protein","tinh bột nghệ","viên bổ sung"])]
    if not safe_products:
        logger.info("Không có sản phẩm an toàn để viết báo.")
        return

    h=history()
    used_products={x.get("product_id") for x in h}
    product=next((p for p in safe_products if p.get("id") not in used_products),safe_products[0])
    text=ai_write(product)
    if text=="BLOCKED" or blocked(text):
        logger.warning("Bài bị chặn bởi bộ lọc an toàn.")
        return

    lines=[x.strip() for x in text.splitlines() if x.strip()]
    title=lines[0].lstrip("#* ").strip()
    body="\n\n".join(lines[1:])
    title_hash=_fingerprint(title)
    if title_hash in {x.get("title_hash") for x in h}:
        logger.warning("AI tạo tiêu đề trùng; bỏ bài để tránh lặp.")
        return

    now=datetime.now(timezone(timedelta(hours=7)))
    image=product.get("image_url","")
    article={
        "title":title,
        "body":body,
        "source_url":product.get("link",""),
        "image_url":image,
        "created_at":now.strftime("%d/%m/%Y %H:%M"),
        "product_name":product.get("name",""),
        "product_url":product.get("link","")
    }
    render_home([article])
    h.append({
        "product_id":product.get("id"),
        "title_hash":title_hash,
        "created_at":now.isoformat()
    })
    save_history(h)
    logger.info("Đã xuất bản bài báo sản phẩm vào docs/index.html; link sản phẩm lấy trực tiếp từ products.json. Chợ Deal không được trộn vào báo.")

if __name__=="__main__":
    try:
        main()
        logger.info("🎉 Hoàn thành! Tờ báo đã cập nhật bài mới.")
    except Exception as e:
        logger.error(f"Lỗi hệ thống: {e}")
        raise
