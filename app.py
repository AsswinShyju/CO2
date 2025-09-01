import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
import os
import numpy as np
from datetime import datetime
history_file = "history.csv"

# ------------------- Page Config -------------------
st.set_page_config(page_title="Carbon Wise", page_icon="♻️", layout="centered")

st.title("♻️ Carbon Wise — Household Waste CO₂ Calculator")
st.caption("Estimate and reduce your carbon footprint from household waste.")

# ------------------- Default Factors -------------------
DEFAULT_FACTORS = {
    "Plastic": 6.0,
    "Paper": 1.2,
    "Food Waste": 1.9,
    "Glass": 0.85,
    "Cardboard": 1.0,
    "Textiles": 5.0,
    "Metal": 2.5,
}

# ------------------- Session State -------------------
if "factors" not in st.session_state:
    st.session_state.factors = DEFAULT_FACTORS.copy()
if "waste_items" not in st.session_state:
    st.session_state.waste_items = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None


# ------------------- Toast Function -------------------
def show_toast(message, color="#2e7d32", seconds=4):
    key = f"toast-{time.time()}"
    st.markdown(f"""
    <div id="{key}" class="toast">{message}</div>
    <style>
    .toast {{
        position: fixed;
        top: 30px;
        left: 50%;
        transform: translateX(-50%);
        background: {color};
        color: white;
        padding: 14px 24px;
        border-radius: 10px;
        font-size: 18px;
        font-weight: 600;
        box-shadow: 0px 6px 18px rgba(0,0,0,0.25);
        opacity: 0;
        animation: fadein 0.4s forwards, fadeout 0.5s {seconds-0.5}s forwards;
        z-index: 999999;
    }}
    @keyframes fadein {{
        from {{opacity: 0; transform: translate(-50%, -20px);}}
        to   {{opacity: 1; transform: translate(-50%, 0);}}
    }}
    @keyframes fadeout {{
        from {{opacity: 1; transform: translate(-50%, 0);}}
        to   {{opacity: 0; transform: translate(-50%, -20px);}}
    }}
    </style>
    """, unsafe_allow_html=True)


# ------------------- Input Section -------------------
st.header("📝 Add Waste Item")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    category = st.selectbox("Waste Category", options=list(
        st.session_state.factors.keys()))
with col2:
    kg = st.number_input("Quantity (kg)", min_value=0.0,
                         step=0.1, format="%.2f")
with col3:
    st.write("")
    if st.button("➕ Add to List"):
        if kg > 0:
            st.session_state["waste_items"].append(
                {"category": category, "kg": float(kg)})
            show_toast(f"✅ Added {kg:.2f} kg of {category} ♻️",
                       color="#2e7d32", seconds=4)
        else:
            show_toast("⚠️ Enter a valid quantity", color="#b71c1c", seconds=4)


# ------------------- Items Table -------------------
if st.session_state.waste_items:
    st.subheader("📋 Your Items")
    items_df = pd.DataFrame(st.session_state.waste_items)
    items_df["Factor (kg CO₂/kg)"] = items_df["category"].map(st.session_state.factors)
    items_df["Emissions (kg CO₂)"] = items_df["kg"] * \
        items_df["Factor (kg CO₂/kg)"]
    st.table(items_df)

    colA, colB = st.columns(2)

    with colA:
        if st.button("📊 Calculate Total"):
            total = float(items_df["Emissions (kg CO₂)"].sum())
            st.session_state.last_result = total

            # Current month-year
            month = datetime.now().strftime("%B %Y")

            # Create record DataFrame
            record = pd.DataFrame([{
                "Month": month,
                "Total Emissions (kg CO₂)": total
            }])

            # Save to CSV
            if os.path.exists(history_file):
                record.to_csv(history_file, mode="a",
                              header=False, index=False)
            else:
                record.to_csv(history_file, index=False)

            # ✅ This line MUST be inside the button block
            st.success(f"✅ Calculation complete! Data saved for {month}")

    with colB:
        if st.button("🗑️ Clear List"):
            st.session_state.waste_items = []
            st.session_state.last_result = None
            show_toast("🗑️ All items cleared", color="#444", seconds=3)

else:
    st.info("No items yet. Add waste items to calculate emissions.")


# ------------------- Results Section -------------------
if st.session_state.last_result is not None:
    st.subheader("✅ Results")
    st.metric("Total Emissions", f"{st.session_state.last_result:.2f} kg CO₂")

    # Pie chart
    by_cat = pd.DataFrame(st.session_state.waste_items).groupby(
        "category")["kg"].sum()
    factors = st.session_state.factors
    emissions = by_cat * by_cat.index.map(factors)
    # Pie Chart with arrow-style labels
    bg_color = "#0E1117"  # Match Streamlit dark theme

    fig, ax = plt.subplots(facecolor=bg_color)
    ax.set_facecolor(bg_color)

    colors = ["#5DADE2", "#3498DB", "#85C1E9", "#AED6F1"]

    wedges, texts, autotexts = ax.pie(
        emissions,
        autopct="%1.1f%%",       # show percent
        pctdistance=0.7,         # % stays inside
        labeldistance=1.2,       # labels pulled further out
        colors=colors,
        textprops={"color": "white"},
    )

    # Add arrow-like connection lines
    for t in texts:
        t.set_color("white")  # labels outside in white
    for a in autotexts:
        a.set_color("white")  # % inside in white

    # Draw leader lines (annotations with arrows)
    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        x = np.cos(np.deg2rad(ang))
        y = np.sin(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        ax.annotate(
            emissions.index[i],
            xy=(x, y), xytext=(1.4*np.sign(x), 1.2*y),
            horizontalalignment=horizontalalignment,
            color="white",
            arrowprops=dict(
                arrowstyle="-", connectionstyle="arc3,rad=0.3", color="white")
        )

    ax.set_title("Contribution by Waste Type", color="white")
    st.pyplot(fig)

    # Feedback
    total = st.session_state.last_result
    if total < 20:
        st.success("🌱 Low footprint. Great job! Keep reducing waste.")
    elif total < 50:
        st.warning("♻️ Moderate footprint. Try recycling more.")
    else:
        st.error("🔥 High footprint. Focus on cutting plastics and composting.")

st.divider()
st.caption("Made with ❤️ in Python + Streamlit")

st.subheader("📅 Monthly History")

if os.path.exists("history.csv"):
    history_df = pd.read_csv("history.csv")
    st.table(history_df)
else:
    st.info("No history yet. Perform a calculation to save monthly data.")
