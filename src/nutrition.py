import streamlit as st
import pandas as pd
from itertools import accumulate

from src.utils import format_pace
from src.pace import estimated_arrival_time_at_checkpoints


def calculate_carb_needs(total_time):
    st.subheader("🍽️ Planification nutritionnelle")
    cols = st.columns(2)
    with cols[0]:
        tolerance_to_carbs = st.slider("Votre tolérance aux glucides (g/h)", min_value=0, max_value=150, value=60, step=5, width=300)
    with cols[1]:
        carbs_needed = (total_time.total_seconds() / 3600) * tolerance_to_carbs
        encadre = st.container(border=True, horizontal=True, vertical_alignment="center", horizontal_alignment="center", width="content")
        encadre.markdown(f"**Glucides nécessaires pour la course : {carbs_needed:.0f} g**")
    return tolerance_to_carbs

def get_consumed_food():
    st.markdown("#### 🍫 Aliments consommés")
    list_of_food = ["Gels", "Barres", "Boisson isotonique", "Compotes", "Pâtes de fruit", "Autres"]
    selected_food = st.multiselect("**Entrez les aliments que vous prévoyez de consommer pendant la course pour calculer votre apport en glucides.**",
                                  list_of_food, default=[])
    cols = st.columns(max(len(selected_food), 1))
    carbs_by_item = {}
    list_of_items = [item[:-1] if item.endswith('s') else item for item in selected_food]
    for i, item in enumerate(list_of_items):
        with cols[i]:
            carbs = st.number_input(f"Glucides par {item} (g)", min_value=0, max_value=100, value=0, step=1, key=f"carbs_{item}")
            carbs_by_item[item] = carbs
    return carbs_by_item

def get_nutritional_strategy(estimated_running_time, pace, carbs_by_item, tolerance_to_carbs):
    # Create list of checkpoints for display within the nutritional strategy
    ravitos = st.session_state.get('ravitos', [])
    bases_vie = st.session_state.get('bases_vie', [])

    checkpoints = sorted(ravitos + bases_vie)

    lst_time_to_checkpoints = estimated_arrival_time_at_checkpoints(pace)

    total_carbs_target = (estimated_running_time.total_seconds() / 3600) * tolerance_to_carbs

    iso_carbs = carbs_by_item.get("Boisson isotonique", 0)

    nutritional_plan = []

    ##### Create different scenarios 
    # Scenario 1: iso is enough for the race:
    if iso_carbs*(len(checkpoints)+1) > total_carbs_target:
        st.write("La boisson isotonique peut suffire à couvrir vos besoins en la remplissant à nouveau aux ravitaillements. Vous pouvez également alterner avec des barres, gels ou autres en fonction de vos envies.")
        return nutritional_plan
    
    # Scenario 2: there is only iso, but without enough carbs
    elif carbs_by_item.keys() == "Boisson isotonique":
        st.write("Si vous considérez consommer uniquement de la boisson isotonique, essayez d'augmenter le dosage pour atteindre vos besoins en glucides. Vous pouvez également considérer d'autres sources de glucides.")
        return nutritional_plan

    
    # Scenario 3: Others
    else:
        carbs_needed = total_carbs_target - iso_carbs*(len(checkpoints)+1) # Carbs still needed after iso
        items_to_rotate = [it for it in carbs_by_item if "iso" not in it.lower()] # Get all items
        if items_to_rotate == []: # To avoid dividing by zero in the next steps
            st.write("Veuillez renseigner les glucides pour chaque aliment que vous prévoyez de consommer pendant la course pour calculer votre stratégie nutritionnelle.")
            return nutritional_plan
        
        items_to_eat = []
        carbs_consumed = []
        i = 0
        while carbs_needed >= 0:
            eaten_item = items_to_rotate[i%len(items_to_rotate)]
            
            items_to_eat.append(eaten_item)
            carbs_consumed.append(carbs_by_item[eaten_item])
            
            carbs_needed -= carbs_by_item[eaten_item]
            
            i+=1
        
        interval = estimated_running_time.total_seconds() / (len(items_to_eat) + 1)
        lst_time_to_eat = [interval*(j+1) for j in range(len(items_to_eat))]
        
        # Add iso drank between checkpoints
        lst_time_to_eat_w_checkpoints = lst_time_to_eat + lst_time_to_checkpoints + [estimated_running_time.total_seconds()]
        items_to_eat_w_checkpoints = items_to_eat + ["Ravitaillement - iso terminée 🧃"] * (len(checkpoints)+1)
        carbs_consumed_w_checkpoints = carbs_consumed + [iso_carbs] * (len(checkpoints)+1)

        nutritional_plan = pd.DataFrame({
            "sec": lst_time_to_eat_w_checkpoints,
            "Aliment": items_to_eat_w_checkpoints,
            "Glucides": carbs_consumed_w_checkpoints,
        })
        print(nutritional_plan["sec"])
        nutritional_plan = nutritional_plan.sort_values(by="sec").reset_index(drop=True)
        nutritional_plan["Total cumulé"] = nutritional_plan["Glucides"].cumsum()

        nutritional_plan["Tps de course"] = nutritional_plan["sec"].apply(lambda x: format_pace(x))
        
        nutritional_plan = nutritional_plan[["Tps de course", "Aliment", "Glucides", "Total cumulé"]]

        st.markdown("**Cette stratégie suppose que vous remplissiez une flasque de boisson isotonique à chaque ravitaillement ⛽️.**")

    return nutritional_plan