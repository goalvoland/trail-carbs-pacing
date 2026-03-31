import streamlit as st

def configure_page():
    st.set_page_config(page_title="Trail Race Planner", layout="wide", page_icon="🏃")
    st.title("🏃 Trail Race Planner - Carbs Pacer")

def format_pace(td):
    total_min = int(td // 60)
    hours = total_min // 60
    minutes = total_min % 60
    
    if hours > 0:
        return f"{hours} h {minutes:02d} min" if minutes > 0 else f"{hours} h"
    return f"{minutes} min"