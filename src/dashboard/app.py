import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database import db_manager

# Page Config
st.set_page_config(
    page_title="VoxIntel Engine Dashboard",
    page_icon="🎙️",
    layout="wide",
)

# Initialize DB (just in case)
db_manager.init_db()

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #41444b;
        text-align: center;
    }
    .chat-container {
        height: 400px;
        overflow-y: auto;
        display: flex;
        flex-direction: column-reverse;
    }
    .user-msg {
        background-color: #2b313e;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        text-align: right;
    }
    .ai-msg {
        background-color: #1c2027;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        text-align: left;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("🎙️ VoxIntel-Engine | Live Sentiment Analysis")
st.markdown("Real-time Voice AI Agent Monitoring System")

# --- Layout: 2 Columns (Gauge vs Chat) ---
col1, col2 = st.columns([1, 2])

# Placeholder containers for auto-refresh
gauge_placeholder = col1.empty()
metrics_placeholder = col1.empty()
chat_placeholder = col2.empty()

def create_gauge(score):
    """
    Creates a vertical gauge chart using Plotly.
    Score: -1.0 (Red/Angry) to 1.0 (Blue/Calm)
    """
    # Map score (-1 to 1) to a 0-100 scale for easier visualization if needed,
    # or keep it raw. Let's keep raw but color coded.
    
    # Color logic
    if score < -0.3:
        bar_color = "red"
    elif score > 0.3:
        bar_color = "#00ccff" # Blue-ish
    else:
        bar_color = "gray" # Neutral

    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Live Sentiment", 'font': {'size': 24}},
        delta = {'reference': 0, 'increasing': {'color': "blue"}, 'decreasing': {'color': "red"}},
        gauge = {
            'axis': {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': bar_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [-1, -0.3], 'color': 'rgba(255, 0, 0, 0.3)'},
                {'range': [-0.3, 0.3], 'color': 'rgba(200, 200, 200, 0.3)'},
                {'range': [0.3, 1], 'color': 'rgba(0, 0, 255, 0.3)'}
            ],
        }
    ))
    
    fig.update_layout(
        height=500, 
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "white"}
    )
    return fig

# --- Main Loop ---
# Streamlit reruns the script on interaction, but for real-time without interaction
# we usually use st.empty() loops or st.rerun() with sleep.
# For a dashboard, a loop with sleep is common in simple prototypes.

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

if st.button("Pause/Resume Live Updates"):
    st.session_state.auto_refresh = not st.session_state.auto_refresh

while st.session_state.auto_refresh:
    # 1. Fetch Data
    latest_score = db_manager.get_latest_sentiment()
    logs = db_manager.get_recent_logs(limit=10) # Get last 10 logs
    
    # 2. Update Gauge
    with gauge_placeholder.container():
        fig = create_gauge(latest_score)
        st.plotly_chart(fig, use_container_width=True)
        
        # Extra Metrics
        st.info(f"Current VADER Score: {latest_score:.4f}")

    # 3. Update Chat History
    with chat_placeholder.container():
        st.subheader("Live Conversation Transcript")
        for timestamp, speaker, text, score in logs:
            # Color code the score in text
            emoji = "😐"
            if score > 0.3: emoji = "🙂"
            if score < -0.3: emoji = "😡"
            
            with st.chat_message(name=speaker.lower(), avatar="🤖" if speaker=="AI" else "👤"):
                st.markdown(f"**{speaker}** ({timestamp}) {emoji} `{score:.2f}`")
                st.write(text)
                st.divider()

    # Refresh rate
    time.sleep(1) 
    st.rerun()
