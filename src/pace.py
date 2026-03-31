import datetime
import streamlit as st

def ask_pace(df):
    st.subheader("🎯 Calcul des temps de passage")
    st.markdown("**Entrez votre allure cible (en minutes par kilomètre) pour estimer vos temps de passage aux points clés du parcours.**")

    cols = st.columns([0.6, 0.3, 0.6, 4])
    
    with cols[0]:
        pace_min = st.number_input("Min", min_value=3, value=6, step=1, 
                                   key="pace_min", label_visibility="collapsed")
    with cols[1]:
        # On ajoute un padding vertical pour aligner le texte avec le champ
        st.markdown("<div style='line-height: 2.5;'>min</div>", unsafe_allow_html=True)
        
    with cols[2]:
        pace_sec = st.number_input("Sec", min_value=0, max_value=59, value=0, step=1, 
                                   key="pace_sec", label_visibility="collapsed")
    with cols[3]:
        st.markdown("<div style='line-height: 2.5;'>sec / km</div>", unsafe_allow_html=True)

    dist = df['cum_distance'].max()
    pace = datetime.timedelta(minutes=pace_min, seconds=pace_sec)
    estimated_running_time = pace * dist

    return estimated_running_time, pace

def estimated_arrival_time_at_checkpoints(pace):
    ravitos = st.session_state.ravitos if "ravitos" in st.session_state else []
    bases_vie = st.session_state.bases_vie if "bases_vie" in st.session_state else []

    checkpoints = sorted(ravitos + bases_vie)
    lst_of_arrival_time = []

    for c in checkpoints:
        lst_of_arrival_time.append((pace * c).total_seconds())

    return lst_of_arrival_time
