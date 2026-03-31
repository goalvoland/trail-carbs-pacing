import streamlit as st
import os
import plotly.graph_objects as go

from src.utils import configure_page
from src.gpx_engine import show_gpx_stats, load_gpx_file
from src.pace import ask_pace
from src.nutrition import calculate_carb_needs, get_consumed_food, get_nutritional_strategy



def add_ravito(col_r, df):
    if 'ravitos' not in st.session_state:
        st.session_state.ravitos = []
    with col_r:
        st.subheader("🧃 Ravitos")
        dist_r = st.number_input("Distance du ravitaillement du départ (km)", min_value=0.0, max_value=float(df['cum_distance'].max()), key="in_r")
        button_add_ravito = st.button("Ajouter un Ravitaillement")
        if button_add_ravito and dist_r not in st.session_state.ravitos :
            st.session_state.ravitos.append(dist_r)
            st.session_state.ravitos.sort()
            st.rerun()

def show_ravitos_in_sidebar():
    if "ravitos" in st.session_state and st.session_state.ravitos:
        st.sidebar.caption("🧃 Ravitaillements")
        for i, d in enumerate(st.session_state.ravitos):
            cols = st.sidebar.columns([2, 1, 1])
            cols[0].write(f"Ravito {i+1}")
            cols[1].write(f"km {d:.1f}")
            if cols[2].button("❌", key=f"del_r_{i}"):
                st.session_state.ravitos.pop(i)
                st.rerun()

def add_base_vie(col_b, df):
    if 'bases_vie' not in st.session_state:
        st.session_state.bases_vie = []
    with col_b:
        st.subheader("🛌 Bases Vie")
        dist_b = st.number_input("Distance de la base vie du départ (km)", min_value=0.0, max_value=float(df['cum_distance'].max()), key="in_b")
        button_add_base_vie = st.button("Ajouter une Base Vie")
        if button_add_base_vie and dist_b not in st.session_state.bases_vie:
            st.session_state.bases_vie.append(dist_b)
            st.session_state.bases_vie.sort()
            st.rerun()

def show_bases_vie_in_sidebar():
    if "bases_vie" in st.session_state:
        st.sidebar.caption("🛌 Bases Vie")
        for i, d in enumerate(st.session_state.bases_vie):
            cols = st.sidebar.columns([2, 1, 1])
            cols[0].write(f"Base vie {i+1}")
            cols[1].write(f"km {d:.1f}")
            if cols[2].button("❌", key=f"del_b_{i}"):
                st.session_state.bases_vie.pop(i)
                st.rerun()

def add_button_drop_interest_points():
    if st.sidebar.button("❌ Tout effacer"):
        st.session_state.ravitos = []
        st.session_state.bases_vie = []
        st.rerun()


def add_ravitos_in_fig(show_ravitos, fig):
    if show_ravitos:
        for i, d in enumerate(st.session_state.ravitos):
            fig.add_vline(
                x=d,
                line_width=2,
                line_color="#0a694f",
                annotation_text=f"🧃 Ravito {i+1}",
            )


def add_bases_vie_in_fig(show_bases, fig):
    if show_bases:
        for i, d in enumerate(st.session_state.bases_vie):
            fig.add_vline(
                x=d,
                line_width=2,
                line_color="#061851",
                annotation_text=f"🛌 Base vie {i+1}",
            )


def show_interest_points(df, fig):
    ######## GESTION DES POINTS D'INTÉRÊT ########
    st.sidebar.header("📍 Points de passage")

    # st.sidebar.markdown("" \
    #     "Ajoutez des points de ravitaillement 🧃 et des bases vie 🛌 " \
    #     "le long de votre parcours. Ils seront affichés sur le graphique " \
    #     "pour vous aider à planifier votre stratégie de course."
    # )

    pt_passage = st.sidebar.multiselect("Ajouter des points de passage", ["Ravitaillement", "Base vie"], default=[])

    # 2. Interface d'ajout
    cols = st.sidebar.columns(max(len(pt_passage), 1))

    if "Ravitaillement" in pt_passage and "Base vie" in pt_passage:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Affichage sur la carte")
        col_r, col_b = cols[0], cols[1]
        add_ravito(col_r, df)
        show_ravitos = st.sidebar.checkbox("Afficher les Ravitaillements 🧃", value=True)
        show_bases = st.sidebar.checkbox("Afficher les Bases Vie 🛌", value=True)
        add_base_vie(col_b, df)
    elif "Ravitaillement" in pt_passage:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Affichage sur la carte")
        col_r = cols[0]
        add_ravito(col_r, df)
        show_ravitos = st.sidebar.checkbox("Afficher les Ravitaillements 🧃", value=True)
        show_bases = None
    elif "Base vie" in pt_passage:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Affichage sur la carte")
        col_b = cols[0]
        add_base_vie(col_b, df)
        show_ravitos = None
        show_bases = st.sidebar.checkbox("Afficher les Bases Vie 🛌", value=True)
    else:
        show_ravitos = None
        show_bases = None

    # Récapitulatif interactif avec suppression
    if ("ravitos" in st.session_state and "bases_vie" in st.session_state) and (st.session_state.ravitos != [] or st.session_state.bases_vie != []):
        st.sidebar.markdown("---")
        st.sidebar.subheader("📋 Récapitulatif des points de ravitaillement")
        # Bouton de drop des points d'intérêt
        add_button_drop_interest_points()
    
    # Affichage Ravitos sur la sidebar
    show_ravitos_in_sidebar()

    # Affichage Bases Vie sur la sidebar
    show_bases_vie_in_sidebar()

    # Affichage sur le graphique
    add_ravitos_in_fig(show_ravitos, fig)
    add_bases_vie_in_fig(show_bases, fig)

    return fig


def run_app():
    ###### Configuration de la page ######
    configure_page()

    ###### Import du GPX ######
    st.subheader("📂 Import du GPX")
    source = st.radio("Source de la trace :", ["Fichier local (Dossier Data)", "Charger mon propre GPX"])
    # Chargement du fichier GPX
    # Ou affichage de la trace par défaut si aucun fichier n'est chargé
    df = load_gpx_file(source)

    ###### Affichage de la trace et des stats ######
    if df is None:
        st.warning("Aucune donnée à afficher. Veuillez charger un fichier gpx.")
        return
    else:
        ###### Calcul des temps de passage ######
        estimated_running_time, pace = ask_pace(df)
        fig = show_gpx_stats(df, estimated_running_time)
        fig_w_interest_points = show_interest_points(df, fig)

        st.plotly_chart(fig_w_interest_points, width='stretch')

        ####### Planification nutritionnelle ######
        tolerance_to_carbs = calculate_carb_needs(estimated_running_time)
        carbs_by_item = get_consumed_food()
        st.markdown("#### 🧾 Stratégie nutritionnelle")
        if not all(carbs_by_item.values()): # Compute only if all values are filled
            st.info("Veuillez renseigner les glucides pour chaque aliment que vous prévoyez de consommer pendant la course pour calculer votre stratégie nutritionnelle.")
        else:
            df_plan = get_nutritional_strategy(estimated_running_time, pace, carbs_by_item, tolerance_to_carbs)
            st.table(df_plan)
        