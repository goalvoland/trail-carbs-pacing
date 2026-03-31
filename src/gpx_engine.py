import gpxpy
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import streamlit as st
import os
import plotly.graph_objects as go

def parse_gpx(file):
    """Transforme un fichier GPX en DataFrame avec distances et D+ cumulés."""
    gpx = gpxpy.parse(file)
    data = []
    
    for track in gpx.tracks:
        for segment in track.segments:
            nb_dizaines_milliers_points = len(segment.points) // 10_000
            for point in segment.points[::nb_dizaines_milliers_points]:  # Prendre max 10k points pour éviter les ralentissements
                data.append({
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation,
                    'time': point.time
                })
    
    df = pd.DataFrame(data)
    
    # Calcul des distances entre points successifs (en km)
    coords = list(zip(df['latitude'], df['longitude']))
    distances = [0]
    for i in range(1, len(coords)):
        dist = geodesic(coords[i-1], coords[i]).km
        distances.append(dist)
    
    df['distance_step'] = distances
    df['cum_distance'] = df['distance_step'].cumsum().round(2)
    
    # Calcul du Dénivelé Positif (D+) cumulé
    df['elev_diff'] = df['elevation'].diff().fillna(0)
    df['cum_dplus'] = df['elev_diff'].apply(lambda x: x if x > 0 else 0).cumsum()
    df['cum_dminus'] = df['elev_diff'].apply(lambda x: x if x < 0 else 0).abs().cumsum()
    df['hypothenuse'] = np.sqrt(df['elev_diff']**2 + (df['distance_step']*1000)**2)
    df['slope'] = (100*df['elev_diff'] / df['hypothenuse']).fillna(0)
    # df['slope_smooth'] = df['slope'].rolling(window=10, center=True).mean().fillna(0)
    df['slope_abs'] = df['slope'].abs()

    return df


def load_gpx_file(source):
    # Dossier où se trouve votre fichier GPX
    DATA_DIR = "data"
    DEFAULT_FILE = "ecotrail_45km.gpx" # Remplacez par le nom exact de votre fichier

    df = None

    if source == "Charger mon propre GPX":
        uploaded_file = st.file_uploader("Importez votre GPX", type="gpx")
        if uploaded_file:
            df = parse_gpx(uploaded_file)
    else:
        # Chemin complet vers le fichier dans votre dossier data
        file_path = os.path.join(DATA_DIR, DEFAULT_FILE)
        
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                df = parse_gpx(f)
            st.success(f"Affichage de la trace par défaut : {DEFAULT_FILE}")
        else:
            st.error(f"Le fichier {DEFAULT_FILE} est introuvable dans le dossier /data")

    return df

def show_gpx_stats(df, est_running_time):
    # --- Affichage des stats rapides ---
    # df = df.iloc[::10]
    st.subheader("🏔️ Profil de la course")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Distance Totale", f"{df['cum_distance'].iloc[-1]:.2f} km")
    col2.metric("D+ Total", f"{int(df['cum_dplus'].iloc[-1])} m")
    col3.metric("D- Total", f"{int(df['cum_dminus'].iloc[-1])} m")
    col4.metric("Temps estimé", f"{est_running_time.seconds//3600}h {(est_running_time.seconds%3600)//60}min")
    st.markdown("**Veuillez indiquer les différents ravitaillements tout au long du parcours pour les voir appraître sur le profil de course.**")

    # --- Graphique Interactif avec Plotly ---
    fig = go.Figure()
    
    # Trace du profil d'élévation
    fig.add_trace(go.Scatter(
        x=df['cum_distance'],
        y=df['elevation'],
        mode='lines+markers',
        name='Pente (%)',
        line=dict(color='lightgray', width=1), 
        hovertemplate=(
            "<b>Distance:</b> %{x:.2f} km<br>" +
            "<b>Alt:</b> %{y:.0f} m<br>" +
            "<extra></extra>" 
        ),
        marker=dict(
            size=4,
            color=df['slope_abs'], # La couleur dépend de la pente
            colorscale='RdYlGn',   # Échelle Rouge-Jaune-Vert
            reversescale=True,     # On inverse pour avoir Vert (bas) -> Rouge (haut)
            cmin=0,                # 0% = Vert
            cmax=20                # 20% = Rouge
        ),
        fill='tozeroy',
        fillcolor='rgba(168, 216, 234, 0.2)' 
    ))

    fig.update_layout(
        title="Profil altimétrique",
        xaxis_title="Distance (km)",
        yaxis_title="Altitude (m)",
        # hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=12)
    )
    return fig