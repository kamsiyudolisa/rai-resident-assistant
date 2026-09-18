import base64
import hmac
import html
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

st.set_page_config(page_title="RAI", page_icon="🏠", layout="wide")

UPDATES = [
    {"Entry ID":"UPDATE01","Category":"Resident Announcements","Resident Question":"When can I register my vehicle with Space CT?","Correct Answer":"Space CT will be available tomorrow to register vehicles. Please stop by the leasing office between 10:00 AM and 4:00 PM.","Urgency":"Normal","Title":"Space CT Vehicle Registration","Details":"Tomorrow · 10:00 AM–4:00 PM · Leasing Office","Image":None,"Section":"Written"},
    {"Entry ID":"UPDATE02","Category":"Resident Announcements","Resident Question":"How do I submit a maintenance request?","Correct Answer":"All maintenance concerns must be submitted through the official maintenance-request QR code. Contact your RA if the request remains unresolved after three to five days.","Urgency":"Normal","Title":"Maintenance Requests","Details":"Use the official maintenance-request QR code.","Image":None,"Section":"Written"},
    {"Entry ID":"EVENT00","Category":"Resident Events","Resident Question":"What events and programs are coming up?","Correct Answer":"Cookies and Compliments will take place September 7, 9, and 11 from 3:00–6:00 PM in the leasing office. ICON Market will take place October 12 from 5:30–9:00 PM on the ICON 7th floor. Adulting 101: Money Edition will take place November 10 at 6:00 PM in the ICON Clubhouse.","Urgency":"Normal","Title":"Upcoming Resident Events","Details":"A summary of upcoming programs.","Image":None,"Section":"AI Only"},
    {"Entry ID":"EVENT01","Category":"Resident Events","Resident Question":"What event is happening this week?","Correct Answer":"Cookies and Compliments will take place September 7, 9, and 11 from 3:00–6:00 PM in the leasing office. Residents can write a kind note, take an encouraging note, and enjoy a cookie.","Urgency":"Normal","Title":"Cookies and Compliments","Details":"September 7, 9, and 11 · 3:00–6:00 PM · Leasing Office","Image":"assets/cookies_and_compliments.png","Section":"This Week"},
    {"Entry ID":"EVENT02","Category":"Resident Events","Resident Question":"When and where is the ICON Market?","Correct Answer":"ICON Market will take place October 12 from 5:30–9:00 PM on the ICON 7th floor. Registration closes September 27.","Urgency":"Normal","Title":"ICON Market","Details":"October 12 · 5:30–9:00 PM · ICON 7th Floor","Image":"assets/icon_market.png","Section":"Upcoming"},
    {"Entry ID":"EVENT03","Category":"Resident Events","Resident Question":"When and where is Adulting 101?","Correct Answer":"Adulting 101: Money Edition will take place November 10 at 6:00 PM in the ICON Clubhouse. The program covers credit, budgeting, saving, and investing.","Urgency":"Normal","Title":"Adulting 101: Money Edition","Details":"November 10 · 6:00 PM · ICON Clubhouse","Image":"assets/adulting_101.png","Section":"Upcoming"},
    {"Entry ID":"UPDATE03","Category":"Resident Announcements","Resident Question":"What do I need to do on move-out day?","Correct Answer":"Residents must completely move out by 12:00 PM on July 31 and check out with an RA before leaving. Improper or late checkout may result in additional fees.","Urgency":"Priority","Title":"Move-Out Day","Details":"Review the deadline and checkout requirements.","Image":"assets/move_out.png","Section":"Flyer"},
    {"Entry ID":"UPDATE04","Category":"Resident Support","Resident Question":"What should I do if I am locked out or cannot get into my room?","Correct Answer":"For lockout assistance, contact the on-call RA at 713-313-5033. Explain that you are locked out and provide your building and room information.","Urgency":"Priority","Title":"Room Lockout Assistance","Details":"Contact the on-call RA · 713-313-5033","Image":None,"Section":"AI Only"},
]

@st.cache_data
def load_knowledge_base():
    return pd.read_csv("ra_knowledge_base.csv")

knowledge_base = load_knowledge_base()

def inject_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Montserrat:wght@700;800&display=swap');
    :root {--maroon:#6f263d;--maroon-dark:#481526;--maroon-light:#963e5b;--charcoal:#171717;--gray:#e7e5e4;--soft-gray:#f5f4f2;--white:#ffffff;}
    .stApp {background-color:#f8f7f5;background-image:linear-gradient(45deg,rgba(111,38,61,.055) 25%,transparent 25%),linear-gradient(-45deg,rgba(111,38,61,.055) 25%,transparent 25%),linear-gradient(45deg,transparent 75%,rgba(86,86,86,.045) 75%),linear-gradient(-45deg,transparent 75%,rgba(86,86,86,.045) 75%);background-size:32px 32px;background-position:0 0,0 16px,16px -16px,-16px 0;font-family:'DM Sans',sans-serif;color:var(--charcoal);}
    .block-container {max-width:1280px;padding-top:2.25rem;padding-bottom:3rem;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,var(--maroon-dark) 0%,var(--maroon) 100%);border-right:1px solid rgba(255,255,255,.16);}
    [data-testid="stSidebar"] * {color:white;}
    [data-testid="stSidebar"] [role="radiogroup"] label {background:transparent;border:1px solid transparent;border-radius:10px;padding:10px 12px;margin:5px 0;transition:.2s ease;}
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {background:rgba(255,255,255,.08);}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#fff;border-color:#fff;box-shadow:0 6px 18px rgba(0,0,0,.18);}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {color:var(--maroon-dark)!important;font-weight:800;}
    .rai-logo {font-family:'Montserrat',sans-serif;font-size:56px;font-weight:800;line-height:1;color:#fff;letter-spacing:-4px;margin:14px 0 8px;}
    .rai-tagline {font-size:12px;letter-spacing:1.8px;text-transform:uppercase;color:rgba(255,255,255,.7);margin-bottom:30px;}
    .hero-title {font-family:'Montserrat',sans-serif;font-size:clamp(42px,5vw,70px);font-weight:800;line-height:1.02;color:var(--maroon-dark);letter-spacing:-3px;margin:12px 0 18px;}
    .hero-pill {display:inline-block;background:#fff;border:1px solid #d6d3d1;border-left:5px solid var(--maroon);border-radius:8px;padding:11px 18px;font-weight:600;box-shadow:0 5px 18px rgba(23,23,23,.07);margin-bottom:18px;color:#34302f;}
    h1,h2,h3 {font-family:'Montserrat',sans-serif!important;letter-spacing:-1px;color:var(--charcoal);}
    div[data-testid="stVerticalBlockBorderWrapper"] {background:rgba(255,255,255,.96);border:1px solid #d6d3d1!important;border-radius:16px;box-shadow:0 8px 24px rgba(23,23,23,.07);padding:4px;}
    .announcement {background:#fff;border-bottom:1px solid #e7e5e4;padding:16px 4px;}
    .announcement:last-child {border-bottom:none;}
    .announcement-title {font-weight:800;font-size:16px;margin-bottom:6px;color:var(--maroon-dark);}
    .announcement-copy {color:#4b5563;font-size:14px;line-height:1.45;}
    .section-ribbon {display:inline-block;background:var(--maroon);color:white;border:none;border-radius:8px;padding:9px 16px;font-family:'Montserrat',sans-serif;font-weight:800;font-size:23px;margin:7px 0 16px;box-shadow:0 5px 14px rgba(111,38,61,.17);}
    .section-ribbon.pink,.section-ribbon.green,.section-ribbon.yellow {background:var(--maroon);color:white;}
    .building-card {background:#fff;border:1px solid #d6d3d1;border-radius:16px;padding:10px;box-shadow:0 10px 28px rgba(23,23,23,.10);}
    .building-card img {width:100%;border-radius:11px;display:block;filter:saturate(.85) contrast(1.03);}
    .building-caption {font-family:'Montserrat',sans-serif;font-weight:800;text-align:center;padding:10px;color:var(--maroon-dark);}
    .contact-card {padding:15px;border:1px solid #d6d3d1;border-left:5px solid var(--maroon);border-radius:10px;background:#fafafa;margin:10px 0;font-weight:700;color:#262221;}
    .checker {height:38px;margin:44px -5rem -5rem;background-color:#d8d5d2;background-image:linear-gradient(45deg,var(--maroon) 25%,transparent 25%),linear-gradient(-45deg,var(--maroon) 25%,transparent 25%),linear-gradient(45deg,transparent 75%,var(--maroon) 75%),linear-gradient(-45deg,transparent 75%,var(--maroon) 75%);background-size:38px 38px;background-position:0 0,0 19px,19px -19px,-19px 0;}
    .scroll-section-marker {display:block;height:0;overflow:hidden;}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.scroll-section-marker) {padding:0!important;margin-bottom:28px;border-radius:24px!important;overflow:hidden;box-shadow:0 22px 55px rgba(72,21,38,.12);}
    @supports (animation-timeline: view()) {
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.scroll-section-marker) {animation:section-rise linear both;animation-timeline:view();animation-range:entry 4% cover 32%;}
        @keyframes section-rise {from{opacity:.12;transform:translateY(75px) scale(.975)}to{opacity:1;transform:translateY(0) scale(1)}}
    }
    .dashboard-hero {min-height:590px;position:relative;background:var(--maroon-dark);overflow:hidden;}
    .dashboard-hero:before {content:'';position:absolute;inset:0;z-index:1;background:linear-gradient(90deg,rgba(38,8,20,.94) 0%,rgba(72,21,38,.79) 38%,rgba(72,21,38,.30) 67%,rgba(23,10,15,.08) 100%);}
    .dashboard-hero-copy {min-height:590px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;padding:clamp(38px,6vw,82px);color:#fff;position:relative;z-index:2;max-width:920px;}
    .dashboard-hero-copy:after {content:'RAI';position:absolute;left:clamp(38px,6vw,82px);bottom:-42px;font-family:'Montserrat',sans-serif;font-size:155px;font-weight:800;color:rgba(255,255,255,.05);letter-spacing:-12px;z-index:-1;}
    .dashboard-kicker {font-family:'Montserrat',sans-serif;font-size:12px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:#e3c7cf;margin-bottom:18px;}
    .dashboard-hero h1 {font-family:'Montserrat',sans-serif!important;font-size:clamp(50px,5.2vw,76px);line-height:.98;letter-spacing:-4px;color:#fff;margin:0 0 24px;white-space:nowrap;text-shadow:0 5px 24px rgba(0,0,0,.32);}
    .dashboard-hero p {font-size:18px;line-height:1.55;color:#f3e9ec;max-width:420px;margin:0;}
    .dashboard-hero-image {position:absolute;inset:0;z-index:0;background:#d8d5d2;}
    .dashboard-hero-image img {width:100%;height:100%;object-fit:cover;object-position:center;display:block;filter:saturate(.82) contrast(1.04);}
    .dashboard-hero-image:after {content:'ICON Student Living';position:absolute;z-index:3;right:25px;bottom:22px;background:rgba(72,21,38,.92);color:#fff;padding:10px 15px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;}
    .wide-section {padding:clamp(34px,5vw,66px);background:#fff;min-height:390px;}
    .wide-section.maroon-wash {background:linear-gradient(135deg,#f8f1f3 0%,#fff 60%);}
    .section-number {font-family:'Montserrat',sans-serif;font-size:12px;font-weight:800;letter-spacing:2px;color:var(--maroon-light);text-transform:uppercase;margin-bottom:10px;}
    .wide-title {font-family:'Montserrat',sans-serif;font-size:clamp(34px,4vw,54px);font-weight:800;line-height:1;color:var(--maroon-dark);letter-spacing:-2px;margin:0 0 13px;}
    .wide-subtitle {color:#6b625f;font-size:16px;margin:0 0 30px;max-width:680px;}
    .announcement-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;}
    .announcement-tile {position:relative;background:#fff;border:1px solid #d8d3d1;border-radius:16px;padding:26px 24px 24px;box-shadow:0 10px 26px rgba(23,23,23,.06);overflow:hidden;}
    .announcement-tile:before {content:'';position:absolute;left:0;top:0;bottom:0;width:7px;background:var(--maroon);}
    .announcement-tile b {display:block;font-family:'Montserrat',sans-serif;color:var(--maroon-dark);font-size:18px;margin-bottom:10px;}
    .announcement-tile span {color:#554e4b;line-height:1.55;}
    .contact-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:24px;}
    .contact-panel {background:var(--maroon-dark);color:#fff;border-radius:18px;padding:30px;min-height:165px;display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 14px 30px rgba(72,21,38,.18);}
    .contact-panel.light {background:#ebe7e4;color:var(--maroon-dark);}
    .contact-panel small {font-family:'Montserrat',sans-serif;font-weight:800;letter-spacing:1.7px;text-transform:uppercase;opacity:.72;}
    .contact-panel strong {font-family:'Montserrat',sans-serif;font-size:clamp(27px,3vw,40px);letter-spacing:-1.5px;}
    .chart-shell {background:linear-gradient(145deg,#fff 0%,#faf6f7 100%);border:1px solid #ded8d6;border-radius:18px;padding:5px 14px 14px;box-shadow:0 12px 28px rgba(72,21,38,.07);margin-bottom:18px;}
    .chart-heading {font-family:'Montserrat',sans-serif;font-size:21px;font-weight:800;color:var(--maroon-dark);letter-spacing:-.6px;margin:6px 0 2px;}
    .chart-description {font-size:13px;color:#756d69;margin-bottom:10px;}
    @media(max-width:800px){.dashboard-hero{min-height:540px}.dashboard-hero:before{background:linear-gradient(90deg,rgba(38,8,20,.92),rgba(72,21,38,.55))}.dashboard-hero h1{white-space:normal;font-size:48px;letter-spacing:-3px}.announcement-grid,.contact-grid{grid-template-columns:1fr}.dashboard-hero-copy{min-height:540px;padding:42px 30px}.wide-section{padding:34px 24px}}
    .stButton>button,.stFormSubmitButton>button {background:var(--maroon)!important;color:white!important;border:1px solid var(--maroon-dark)!important;border-radius:9px!important;font-weight:800!important;box-shadow:0 5px 14px rgba(111,38,61,.18)!important;}
    .stButton>button:hover,.stFormSubmitButton>button:hover {background:var(--maroon-dark)!important;border-color:var(--maroon-dark)!important;}
    [data-testid="stTextInput"] input,[data-testid="stChatInput"] textarea {background:#fff!important;color:#171717!important;border-color:#a8a29e!important;}
    [data-testid="stChatInput"] {background:#fff!important;border:1px solid #c7c3c0!important;border-radius:12px!important;box-shadow:0 8px 22px rgba(23,23,23,.08)!important;}
    [data-testid="stChatInput"] textarea::placeholder {color:#6b6662!important;}
    .chat-card {max-width:86%;border:1px solid #d6d3d1;border-radius:14px;padding:14px 17px;margin:10px 0 16px;box-shadow:0 5px 16px rgba(23,23,23,.06);font-size:15px;line-height:1.55;color:#1f1d1c;}
    .chat-card.user {margin-left:auto;background:var(--maroon);color:#fff;border-color:var(--maroon);}
    .chat-card.rai {margin-right:auto;background:#fff;border-left:5px solid var(--maroon);}
    .chat-label {font-family:'Montserrat',sans-serif;font-size:11px;font-weight:800;letter-spacing:1.5px;margin-bottom:6px;opacity:.78;}
    .login-note {background:#fff;border:1px solid #d6d3d1;border-left:5px solid var(--maroon);border-radius:10px;padding:13px 16px;margin:2px 0 20px;color:#504a47;}
    [data-testid="stMetric"] {background:#fff;border:1px solid #d6d3d1;border-top:5px solid var(--maroon);padding:14px;border-radius:12px;box-shadow:0 6px 18px rgba(23,23,23,.06);}
    [data-testid="stMetric"] * {color:var(--maroon-dark)!important;}
    [data-testid="stMetricLabel"] p {color:#625956!important;font-weight:700!important;}
    [data-testid="stMetricValue"] {color:var(--maroon-dark)!important;font-family:'Montserrat',sans-serif!important;font-weight:800!important;}
    [data-testid="stDataFrame"] {border:1px solid #d6d3d1;border-radius:12px;overflow:hidden;}
    hr {border-color:#dedbd8;}
    </style>
    """, unsafe_allow_html=True)

def get_secret(name):
    try:
        return st.secrets[name]
    except (KeyError, FileNotFoundError):
        return os.getenv(name)

def build_catalog():
    lines = [f"{r['Entry ID']} | {r['Category']} | Question: {r['Resident Question']} | Verified answer: {r['Correct Answer']}" for _, r in knowledge_base.iterrows()]
    lines += [f"{r['Entry ID']} | {r['Category']} | Question: {r['Resident Question']} | Verified answer: {r['Correct Answer']}" for r in UPDATES]
    return "\n".join(lines)

def find_entry(entry_id):
    ids = knowledge_base["Entry ID"].astype(str).str.upper()
    if entry_id in set(ids):
        return knowledge_base[ids.eq(entry_id)].iloc[0]
    return next((u for u in UPDATES if u["Entry ID"] == entry_id), None)

def select_information(question):
    normalized = re.sub(r"[^a-z0-9 ]", " ", question.lower())
    normalized = " ".join(normalized.split())
    quick_routes = [
        (("locked out", "lock out", "get into my room", "getting into my room", "room key", "key not working"), "UPDATE04"),
        (("maintenance", "repair", "broken", "work order"), "UPDATE02"),
        (("register my car", "register my vehicle", "vehicle registration", "parking registration", "space ct"), "UPDATE01"),
        (("icon market",), "EVENT02"),
        (("adulting 101",), "EVENT03"),
        (("cookies and compliments", "event this week"), "EVENT01"),
        (("upcoming events", "what events", "resident events", "programs coming up"), "EVENT00"),
        (("move out", "moveout", "check out"), "UPDATE03"),
    ]
    for phrases, entry_id in quick_routes:
        if any(phrase in normalized for phrase in phrases):
            return find_entry(entry_id)

    key = get_secret("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Add OPENAI_API_KEY to .streamlit/secrets.toml before using RAI.")
    response = OpenAI(api_key=key).responses.create(
        model="gpt-5.6-luna",
        instructions="Route the resident message to exactly one verified Entry ID from the catalog. Match paraphrases, short messages, everyday language, and implied intent. A resident does not need to use the catalog's exact wording. Return UNKNOWN only when no catalog entry can answer the request without inventing facts. Return only the Entry ID or UNKNOWN.",
        input=f"VERIFIED CATALOG:\n{build_catalog()}\n\nRESIDENT MESSAGE:\n{question}",
    )
    entry_id = response.output_text.strip().upper()
    return None if entry_id == "UNKNOWN" else find_entry(entry_id)

def log_question(question, match):
    row = {"Timestamp":datetime.now(timezone.utc).isoformat(),"Resident Question":question,"Entry ID":"UNKNOWN" if match is None else match["Entry ID"],"Category":"Unknown" if match is None else match["Category"],"Urgency":"Unknown" if match is None else match["Urgency"],"Verified Answer Found":match is not None}
    pd.DataFrame([row]).to_csv("ra_question_log.csv",mode="a",header=not os.path.exists("ra_question_log.csv"),index=False)

def image64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

def carousel(items, height=520):
    cards = ""
    for item in items:
        cards += f'''<article class="card"><img src="data:image/png;base64,{image64(item['Image'])}" alt="{html.escape(item['Title'])}"><div><b>{html.escape(item['Title'])}</b><small>{html.escape(item['Details'])}</small></div></article>'''
    components.html(f'''<style>@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Montserrat:wght@700;800&display=swap');body{{margin:0;background:transparent;font-family:'DM Sans',sans-serif}}.row{{display:flex;gap:16px;overflow-x:auto;padding:5px 5px 20px;scroll-snap-type:x mandatory}}.row::-webkit-scrollbar{{height:8px}}.row::-webkit-scrollbar-track{{background:#e7e5e4;border-radius:10px}}.row::-webkit-scrollbar-thumb{{background:#6f263d;border-radius:10px}}.card{{flex:0 0 285px;background:#fff;border:1px solid #d6d3d1;border-radius:14px;overflow:hidden;box-shadow:0 8px 22px rgba(23,23,23,.10);scroll-snap-align:start}}.card img{{width:100%;height:395px;object-fit:contain;background:#fff;display:block;border-bottom:4px solid #6f263d}}.card div{{padding:14px;background:#fff}}b{{display:block;font-family:'Montserrat',sans-serif;font-size:16px;color:#481526}}small{{display:block;color:#57534e;margin-top:7px;line-height:1.4}}</style><div class="row">{cards}</div>''',height=height,scrolling=False)

def resident_dashboard():
    icon_image = image64("assets/icon_lofts.png")
    with st.container(border=True):
        st.markdown(
            f'''<span class="scroll-section-marker"></span>
            <section class="dashboard-hero">
                <div class="dashboard-hero-copy">
                    <div class="dashboard-kicker">Resident Life · Texas Southern University</div>
                    <h1>Welcome, Tigers.</h1>
                    <p>Everything you need for life at ICON, updates, events, support, and verified answers in one place.</p>
                </div>
                <div class="dashboard-hero-image"><img src="data:image/png;base64,{icon_image}" alt="ICON student housing"></div>
            </section>''',
            unsafe_allow_html=True,
        )

    announcements = "".join(
        f'<article class="announcement-tile"><b>{html.escape(item["Title"])}</b><span>{html.escape(item["Correct Answer"])}</span></article>'
        for item in UPDATES if item["Section"] == "Written"
    )
    with st.container(border=True):
        st.markdown(
            f'''<span class="scroll-section-marker"></span><section class="wide-section maroon-wash">
            <div class="section-number">01 · Stay informed</div><h2 class="wide-title">Important announcements</h2>
            <p class="wide-subtitle">The essential updates for right now .</p>
            <div class="announcement-grid">{announcements}</div></section>''',
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.markdown(
            '''<span class="scroll-section-marker"></span><div class="wide-section" style="min-height:0;padding-bottom:12px">
            <div class="section-number">02 · Happening now</div><h2 class="wide-title">Events this week</h2>
            <p class="wide-subtitle">Swipe through what is happening around ICON this week.</p></div>''',
            unsafe_allow_html=True,
        )
        carousel([u for u in UPDATES if u["Section"] == "This Week"])

    with st.container(border=True):
        st.markdown(
            '''<span class="scroll-section-marker"></span><div class="wide-section maroon-wash" style="min-height:0;padding-bottom:12px">
            <div class="section-number">03 · Plan ahead</div><h2 class="wide-title">Coming up at ICON</h2>
            <p class="wide-subtitle">Programs worth saving to your calendar.</p></div>''',
            unsafe_allow_html=True,
        )
        carousel([u for u in UPDATES if u["Section"] == "Upcoming"])

    with st.container(border=True):
        st.markdown(
            '''<span class="scroll-section-marker"></span><section class="wide-section">
            <div class="section-number">04 · Get support</div><h2 class="wide-title">Important contacts</h2>
            <p class="wide-subtitle">Save these numbers now so help is easy to reach when you need it.</p>
            <div class="contact-grid">
                <article class="contact-panel"><small>On-call resident assistant</small><strong>713-313-5033</strong></article>
                <article class="contact-panel light"><small>TSU Police Department</small><strong>713-313-7000</strong></article>
            </div></section>''',
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.markdown(
            '''<span class="scroll-section-marker"></span><div class="wide-section maroon-wash" style="min-height:0;padding-bottom:12px">
            <div class="section-number">05 · On the board</div><h2 class="wide-title">Resident flyers</h2>
            <p class="wide-subtitle">Deadlines, reminders, and notices—kept together for quick reference.</p></div>''',
            unsafe_allow_html=True,
        )
        carousel([u for u in UPDATES if u["Section"] == "Flyer"])
    st.markdown('<div class="checker"></div>',unsafe_allow_html=True)

def render_chat_message(role, content):
    role_class = "user" if role == "user" else "rai"
    label = "YOU" if role == "user" else "RAI"
    safe_content = html.escape(content).replace("\n", "<br>")
    st.markdown(
        f'<div class="chat-card {role_class}"><div class="chat-label">{label}</div>{safe_content}</div>',
        unsafe_allow_html=True,
    )

def assistant():
    st.markdown('<div class="hero-title">Ask RAI</div><div class="hero-pill">Verified answers for resident life.</div>',unsafe_allow_html=True)
    if "messages" not in st.session_state:
        st.session_state.messages=[]
    for message in st.session_state.messages:
        render_chat_message(message["role"], message["content"])
    question=st.chat_input("How can I help you?")
    if question:
        st.session_state.messages.append({"role":"user","content":question})
        render_chat_message("user",question)
        with st.spinner("Checking verified information..."):
            try:
                match=select_information(question); log_question(question,match)
                if match is None:
                    text="I couldn't find verified information for that question. Please contact your RA for assistance.\n\nCategory: Unknown\nUrgency: Unknown"
                else:
                    text=f'{match["Correct Answer"]}\n\nCategory: {match["Category"]}\nUrgency: {match["Urgency"]}'
                render_chat_message("assistant",text)
            except Exception as error:
                text="RAI couldn't connect to the language model. Check the API key and try again."
                st.error(text); st.caption(str(error))
        st.session_state.messages.append({"role":"assistant","content":text})

def ra_login():
    if st.session_state.get("ra_authenticated",False): return True
    st.markdown('<div class="hero-title">RA Login</div>',unsafe_allow_html=True)
    st.markdown('<div class="login-note">Authorized resident-assistant access only. Sign in to review resident-question trends and knowledge gaps.</div>',unsafe_allow_html=True)
    with st.form("ra_login"):
        password=st.text_input("Shared RA password",type="password")
        submitted=st.form_submit_button("Sign in",use_container_width=True)
    if submitted:
        correct=get_secret("RA_DASHBOARD_PASSWORD")
        if correct and hmac.compare_digest(password,correct): st.session_state.ra_authenticated=True; st.rerun()
        else: st.error("Incorrect password. Please try again.")
    return False

TSU_CHART_COLORS = ["#6f263d", "#963e5b", "#c59aa7", "#c8a96b", "#8b817c", "#d9c5cb", "#4b3038"]

def chart_config():
    return {
        "view": {"strokeWidth": 0},
        "axis": {
            "gridColor": "#eee8e6",
            "domain": False,
            "tickColor": "#d8cfcc",
            "labelColor": "#514947",
            "titleColor": "#6f263d",
            "labelFont": "DM Sans",
            "titleFont": "DM Sans",
        },
    }

def chart_header(title, description):
    st.markdown(
        f'<div class="chart-heading">{html.escape(title)}</div><div class="chart-description">{html.escape(description)}</div>',
        unsafe_allow_html=True,
    )

def insights():
    if not ra_login(): return
    a,b=st.columns([5,1])
    with a: st.markdown('<div class="hero-title">RA Insights</div>',unsafe_allow_html=True)
    with b:
        if st.button("Log out",use_container_width=True): st.session_state.ra_authenticated=False; st.rerun()
    if not os.path.exists("ra_question_log.csv"): st.info("No resident questions have been recorded yet."); return
    log=pd.read_csv("ra_question_log.csv")
    if log.empty: st.info("No resident questions have been recorded yet."); return
    verified=log["Verified Answer Found"].astype(str).str.lower().eq("true").sum()
    unanswered_count=len(log)-verified
    answer_rate=round((verified/len(log))*100) if len(log) else 0
    cols=st.columns(4)
    for col,label,value in zip(cols,["Total Questions","Verified Answers","Unanswered","Answer Rate"],[len(log),verified,unanswered_count,f"{answer_rate}%"]): col.metric(label,value)
    st.write("")
    c1,c2=st.columns(2)
    with c1:
        with st.container(border=True):
            chart_header("Questions by category", "See what residents need help with most.")
            category_data=log["Category"].fillna("Unknown").value_counts().rename_axis("Category").reset_index(name="Questions")
            st.vega_lite_chart(category_data,{"height":280,"mark":{"type":"bar","cornerRadiusEnd":9,"size":24},"encoding":{"x":{"field":"Questions","type":"quantitative","title":None,"axis":{"tickMinStep":1}},"y":{"field":"Category","type":"nominal","title":None,"sort":"-x","axis":{"labelLimit":170}},"color":{"field":"Category","type":"nominal","legend":None,"scale":{"range":TSU_CHART_COLORS}},"tooltip":[{"field":"Category","type":"nominal"},{"field":"Questions","type":"quantitative"}]},"config":chart_config()},use_container_width=True)
    with c2:
        with st.container(border=True):
            chart_header("Most-used answer entries", "Identify which verified resources residents rely on.")
            used_entries=log[~log["Entry ID"].eq("UNKNOWN")]["Entry ID"].value_counts().head(7).rename_axis("Entry").reset_index(name="Uses")
            if used_entries.empty:
                st.info("No verified answer entries have been used yet.")
            else:
                st.vega_lite_chart(used_entries,{"height":280,"layer":[{"mark":{"type":"bar","size":6,"color":"#d9c5cb","cornerRadiusEnd":4},"encoding":{"x":{"field":"Uses","type":"quantitative","title":None,"axis":{"tickMinStep":1}},"y":{"field":"Entry","type":"nominal","title":None,"sort":"-x"}}},{"mark":{"type":"point","filled":True,"size":230,"color":"#6f263d","stroke":"#f8eef1","strokeWidth":3},"encoding":{"x":{"field":"Uses","type":"quantitative"},"y":{"field":"Entry","type":"nominal","sort":"-x"},"tooltip":[{"field":"Entry","type":"nominal"},{"field":"Uses","type":"quantitative"}]}}],"config":chart_config()},use_container_width=True)
    c1,c2=st.columns(2)
    with c1:
        with st.container(border=True):
            chart_header("Questions over time", "Spot busy days and changes in resident demand.")
            timestamps=pd.to_datetime(log["Timestamp"],errors="coerce",utc=True)
            daily_questions=timestamps.dropna().dt.date.value_counts().sort_index().rename_axis("Date").reset_index(name="Questions")
            if daily_questions.empty:
                st.info("No valid timestamps are available yet.")
            else:
                daily_questions["Date"]=pd.to_datetime(daily_questions["Date"])
                time_encoding={"x":{"field":"Date","type":"temporal","title":None},"y":{"field":"Questions","type":"quantitative","title":None,"axis":{"tickMinStep":1}},"tooltip":[{"field":"Date","type":"temporal"},{"field":"Questions","type":"quantitative"}]}
                st.vega_lite_chart(daily_questions,{"height":280,"layer":[{"mark":{"type":"area","color":"#963e5b","opacity":.16},"encoding":time_encoding},{"mark":{"type":"line","color":"#6f263d","strokeWidth":3},"encoding":time_encoding},{"mark":{"type":"point","filled":True,"color":"#c8a96b","stroke":"#6f263d","strokeWidth":2,"size":90},"encoding":time_encoding}],"config":chart_config()},use_container_width=True)
    with c2:
        with st.container(border=True):
            chart_header("Most-asked questions", "Understand the exact wording residents use.")
            top_questions=log["Resident Question"].astype(str).value_counts().head(7).rename_axis("Question").reset_index(name="Times asked")
            st.vega_lite_chart(top_questions,{"height":280,"mark":{"type":"bar","cornerRadiusEnd":9,"size":23},"encoding":{"x":{"field":"Times asked","type":"quantitative","title":None,"axis":{"tickMinStep":1}},"y":{"field":"Question","type":"nominal","title":None,"sort":"-x","axis":{"labelLimit":190}},"color":{"field":"Times asked","type":"quantitative","legend":None,"scale":{"range":["#d9c5cb","#6f263d"]}},"tooltip":[{"field":"Question","type":"nominal"},{"field":"Times asked","type":"quantitative"}]},"config":chart_config()},use_container_width=True)
    st.markdown('<div class="section-ribbon yellow">Unanswered questions</div>',unsafe_allow_html=True)
    unanswered=log[log["Entry ID"].eq("UNKNOWN")][["Timestamp","Resident Question"]]
    if unanswered.empty:
        st.success("RAI found verified information for every recorded question.")
    else:
        st.dataframe(unanswered,use_container_width=True,hide_index=True)
    st.markdown('<div class="checker"></div>',unsafe_allow_html=True)

inject_style()
with st.sidebar:
    st.markdown('<div class="rai-logo">RAI</div>',unsafe_allow_html=True)
    st.markdown('<div class="rai-tagline">Resident AI Assistant</div>',unsafe_allow_html=True)
    page=st.radio("Navigation",["Resident Dashboard","Ask RAI","RA Insights"],label_visibility="collapsed")

if page=="Resident Dashboard": resident_dashboard()
elif page=="Ask RAI": assistant()
else: insights()
