import streamlit as st
import streamlit.components.v1 as components
import time
import sys
import os
import subprocess
import signal

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database import db_manager

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="VoxIntel | AI Voice Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize DB
db_manager.init_db()

# --- ENGINE CONTROL LOGIC ---
PID_FILE = "engine.pid"

def is_engine_running():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return True, pid
        except (OSError, ValueError):
            return False, None
    return False, None

def start_engine():
    if is_engine_running()[0]:
        st.toast("Engine is already running!", icon="⚠️")
        return
    
    # --- CLEAR DB ON START ---
    db_manager.clear_logs()
    st.toast("Session cleared. Starting fresh...", icon="🧹")
    # -------------------------

    python_exe = sys.executable
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../core/audio_engine.py'))
    with open("engine_stdout.log", "w") as out, open("engine_stderr.log", "w") as err:
        proc = subprocess.Popen([python_exe, script_path], stdout=out, stderr=err, preexec_fn=os.setsid)
    with open(PID_FILE, 'w') as f:
        f.write(str(proc.pid))
    st.toast("Engine Started Successfully!", icon="🚀")
    time.sleep(1)
    st.rerun()

def stop_engine():
    running, pid = is_engine_running()
    if running and pid:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            st.toast("Engine Stopped.", icon="🛑")
        except Exception as e:
            st.error(f"Error stopping engine: {e}")
        finally:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            time.sleep(1)
            st.rerun()
    else:
        st.toast("Engine is not running.", icon="ℹ️")

# --- CUSTOM CSS (Styles & Animations) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    /* Reset */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Animated Gradient Background (Deep Space) */
    .stApp {
        background: linear-gradient(-45deg, #020024, #040429, #081b4b, #020024);
        background-size: 400% 400%;
        animation: gradientBG 20s ease infinite;
    }
    
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Start/Stop Button Customization */
    .stButton > button {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 40px !important;
        padding: 15px 40px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-5px) scale(1.05) !important;
        background: rgba(255, 255, 255, 0.25) !important;
        box-shadow: 0 15px 35px rgba(0,212,255, 0.3) !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
    }

    /* Hide Streamlit UI */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


# --- DATA FETCHING ---
# Fetch AVERAGE User sentiment for the gauge (Cumulative)
latest_score = db_manager.get_average_sentiment(speaker_filter="User")
logs = db_manager.get_recent_logs(limit=1)
is_speaking = False
last_speaker = "AI"
if logs:
    last_speaker = logs[0][1]
    is_speaking = True


# --- INTERACTIVE ROBOT FACE (CENTERED & SCALED UP) ---
def render_interactive_ui(score, is_active, speaker):
    if score < -0.3:
        mood_color = "#ff453a"
        eye_expression = "angry"
    elif score > 0.3:
        mood_color = "#32d74b"
        eye_expression = "happy"
    else:
        mood_color = "#ffffff"
        eye_expression = "neutral"

    robot_speaking = is_active and speaker == "AI"
    wave_state = "running" if robot_speaking else "paused"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0; overflow: hidden; background: transparent;
            font-family: 'Inter', sans-serif;
            height: 600px; /* Taller canvas */
            display: flex; justify-content: center; align-items: center;
            position: relative;
        }}
        #canvas-bg {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; opacity: 0.6; pointer-events: none; }}
        
        .robot-wrapper {{
            position: relative; z-index: 10; 
            width: 350px; height: 350px; /* Scaled Up */
            background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(30px);
            border-radius: 80px; border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 30px 60px rgba(0,0,0,0.4);
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            transition: transform 0.1s ease-out;
        }}
        .robot-wrapper::before {{
            content: ''; position: absolute; inset: -2px; border-radius: 82px;
            background: linear-gradient(45deg, {mood_color}, transparent, {mood_color});
            z-index: -1; opacity: 0.3; filter: blur(25px);
            animation: glowPulse 3s infinite alternate;
        }}
        @keyframes glowPulse {{ 0% {{ opacity: 0.2; filter: blur(25px); }} 100% {{ opacity: 0.6; filter: blur(40px); }} }}
        
        .face {{ display: flex; flex-direction: column; align-items: center; gap: 50px; }}
        .eyes {{ display: flex; gap: 80px; }}
        
        .eye {{
            width: 60px; height: 90px; /* Scaled Up */
            background: {mood_color}; border-radius: 30px;
            box-shadow: 0 0 25px {mood_color}; transition: all 0.5s ease;
            animation: blink 4s infinite;
        }}
        .eye.angry {{ height: 60px; border-radius: 10px 10px 30px 30px; transform: rotate(15deg); }}
        .eye.angry:nth-child(2) {{ transform: rotate(-15deg); }}
        .eye.happy {{ height: 70px; border-radius: 30px 30px 10px 10px; }}
        @keyframes blink {{ 0%, 48%, 52%, 100% {{ transform: scaleY(1); }} 50% {{ transform: scaleY(0.1); }} }}
        
        .mouth {{ display: flex; align-items: center; gap: 8px; height: 50px; }}
        .bar {{
            width: 8px; height: 8px; /* Scaled Up */
            background: {mood_color}; border-radius: 8px;
            animation: wave 0.8s ease-in-out infinite; animation-play-state: {wave_state};
        }}
        .bar:nth-child(1) {{ animation-delay: 0.0s; }}
        .bar:nth-child(2) {{ animation-delay: 0.1s; }}
        .bar:nth-child(3) {{ animation-delay: 0.2s; }}
        .bar:nth-child(4) {{ animation-delay: 0.3s; }}
        .bar:nth-child(5) {{ animation-delay: 0.2s; }}
        @keyframes wave {{ 0%, 100% {{ height: 8px; opacity: 0.5; }} 50% {{ height: 50px; opacity: 1; }} }}
    </style>
    </head>
    <body>
        <canvas id="canvas-bg"></canvas>
        <div class="robot-wrapper" id="robot">
            <div class="face">
                <div class="eyes"><div class="eye {eye_expression}"></div><div class="eye {eye_expression}"></div></div>
                <div class="mouth"><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div></div>
            </div>
        </div>
        <script>
            const robot = document.getElementById('robot');
            document.addEventListener('mousemove', (e) => {{
                const x = (window.innerWidth / 2 - e.pageX) / 35;
                const y = (window.innerHeight / 2 - e.pageY) / 35;
                robot.style.transform = `rotateY(${{x}}deg) rotateX(${{y}}deg)`;
            }});
            const canvas = document.getElementById('canvas-bg');
            const ctx = canvas.getContext('2d');
            let width, height, particles = [];
            let mx = 0, my = 0;
            document.addEventListener('mousemove', e => {{ mx = e.clientX; my = e.clientY; }});
            function resize() {{ width = window.innerWidth; height = window.innerHeight; canvas.width = width; canvas.height = height; }}
            window.addEventListener('resize', resize); resize();
            class Particle {{
                constructor() {{
                    this.x = Math.random() * width; this.y = Math.random() * height;
                    this.vx = (Math.random() - 0.5) * 2.0; this.vy = (Math.random() - 0.5) * 2.0; // Faster speed
                    this.size = Math.random() * 3; 
                    this.baseSize = this.size;
                    this.alpha = Math.random() * 0.6 + 0.2; // Brighter
                }}
                update() {{
                    this.x += this.vx; this.y += this.vy;
                    
                    // Wrap around screen
                    if (this.x < 0) this.x = width;
                    if (this.x > width) this.x = 0;
                    if (this.y < 0) this.y = height;
                    if (this.y > height) this.y = 0;
                    
                    const dx = mx - this.x; const dy = my - this.y;
                    const dist = Math.sqrt(dx*dx + dy*dy);
                    
                    // Gentle Anti-Gravity Repel (Reduced Force)
                    if (dist < 250) {{
                        const force = (250 - dist) / 250;
                        this.size = this.baseSize + force * 5; 
                        this.x -= (dx / dist) * force * 5; // Much gentler push
                        this.y -= (dy / dist) * force * 5;
                    }} else {{ 
                        this.size = this.baseSize; 
                    }}
                }}
                draw() {{ 
                    // Insane Glow (Sci-Fi Spheres)
                    ctx.fillStyle = `rgba(100, 200, 255, ${{this.alpha}})`; 
                    ctx.shadowBlur = 30; // Massive Glow
                    ctx.shadowColor = "rgba(50, 150, 255, 0.9)";
                    ctx.beginPath(); 
                    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2); 
                    ctx.fill(); 
                    ctx.shadowBlur = 0; 
                }}
            }}
            function init() {{ particles = []; for(let i=0; i<400; i++) particles.push(new Particle()); }}
            init();
            function animate() {{ ctx.clearRect(0, 0, width, height); particles.forEach(p => {{ p.update(); p.draw(); }}); requestAnimationFrame(animate); }}
            animate();
        </script>
    </body>
    </html>
    """
    # Increase height to cover more screen area
    components.html(html_code, height=800)


# --- LAYOUT CONSTRUCTION (CENTERED) ---

# 1. Top Button (Centered)
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    running, pid = is_engine_running()
    if running:
        if st.button("🔴 Stop Engine", use_container_width=True):
            stop_engine()
    else:
        if st.button("✨ Start Engine", use_container_width=True):
            start_engine()

# 2. Main Robot (Full Width)
render_interactive_ui(latest_score, is_speaking, last_speaker)

# 3. Sentiment Bar (Centered below robot)
sent_label = "Neutral"
sent_color = "white"
if latest_score > 0.3: sent_label = "Positive"; sent_color = "#32d74b"
if latest_score < -0.3: sent_label = "Negative"; sent_color = "#ff453a"

c_left, c_mid, c_right = st.columns([1, 2, 1])
with c_mid:
    st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 30px;
            margin-top: -50px; 
            text-align: center;
            position: relative;
            z-index: 20;
        ">
            <div style="font-size: 14px; opacity: 0.6; text-transform: uppercase; letter-spacing: 2px;">Session Mood</div>
            <div style="font-size: 32px; font-weight: 700; color: {sent_color}; margin: 10px 0;">{sent_label}</div>
            <div style="background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; width: 100%; overflow: hidden;">
                <div style="width: {int((latest_score + 1) * 50)}%; height: 100%; background: {sent_color}; transition: width 0.8s ease;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Auto Refresh Loop
time.sleep(1)
st.rerun()
