import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import time
from streamlit_local_storage import LocalStorage

# ---------------- CONFIG ---------------- #
st.set_page_config(
    page_title="Carbon Wise — Household Waste CO₂ Calculator",
    page_icon="♻",
    layout="centered",
)

st.title("♻ Carbon Wise — Household Waste CO₂ Calculator")
st.caption("Track your household waste and calculate your carbon footprint")

# ---------------- EMISSION FACTORS ---------------- #
EMISSION_FACTORS = {
    "Plastic": 6.0,
    "Paper": 1.2,
    "Food Waste": 1.9,
    "Glass": 0.85,
    "Cardboard": 1.0,
    "Textiles": 5.0,
    "Metal": 2.5,
}

COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1",
          "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8"]

# ---------------- LOCAL STORAGE ---------------- #
storage = LocalStorage()

if "waste_items" not in st.session_state:
    st.session_state.waste_items = []

if "calculation_result" not in st.session_state:
    st.session_state.calculation_result = {}

if "show_result" not in st.session_state:
    st.session_state.show_result = False

if "history" not in st.session_state:
    # Try to load from localStorage
    saved = storage.getItem("carbon_wise_history")
    if saved:
        st.session_state.history = eval(saved)  # convert string back to dict
    else:
        st.session_state.history = {}

# ---------------- HELPERS ---------------- #


def get_month_label():
    return datetime.now().strftime("%B %Y")


def calculate_emissions(items):
    emissions_by_cat = {}
    total_emissions = 0
    for item in items:
        cat = item["category"]
        emission = item["quantity"] * EMISSION_FACTORS[cat]
        emissions_by_cat[cat] = emissions_by_cat.get(cat, 0) + emission
        total_emissions += emission
    return {
        "total": round(total_emissions, 2),
        "by_category": emissions_by_cat,
        "items": items
    }


def create_pie_chart(categories, values, title):
    # Detect Streamlit theme background
    bg_color = "#0E1117" if st.get_option("theme.base") == "dark" else "white"
    text_color = "white" if st.get_option("theme.base") == "dark" else "black"

    fig, ax = plt.subplots(figsize=(6, 6), facecolor=bg_color)
    ax.set_facecolor(bg_color)

    wedges, texts, autotexts = ax.pie(
        values,
        autopct="%1.1f%%",  # keep % inside slices
        startangle=90,
        colors=COLORS[:len(categories)],
        textprops={"color": text_color},
    )

    # Arrow-style labels: only item names
    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
        x = np.cos(np.deg2rad(ang))
        y = np.sin(np.deg2rad(ang))

        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        ax.annotate(
            f"{categories[i]}",
            xy=(x, y),
            xytext=(1.4 * np.sign(x), 1.2 * y),
            horizontalalignment=horizontalalignment,
            color=text_color,
            fontsize=11,
            arrowprops=dict(
                arrowstyle="-", connectionstyle="arc3,rad=0.3", color=text_color
            ),
        )

    ax.set_title(title, color=text_color, fontsize=14,
                 fontweight="bold", pad=20)
    plt.tight_layout()
    return fig


# ---------------- TABS ---------------- #
tab1, tab2, tab3 = st.tabs(["📝 Calculator", "📊 Dashboard", "📋 History"])

# -------- TAB 1: CALCULATOR -------- #
with tab1:
    st.header("Add Waste Items")
    col1, col2 = st.columns([2, 1])

    with col1:
        category = st.selectbox("Select Waste Category",
                                list(EMISSION_FACTORS.keys()))
    with col2:
        quantity = st.number_input(
            "Quantity (kg)", min_value=0.0, step=0.1, format="%.2f")

    if st.button("➕ Add Item", type="primary"):
        if quantity > 0:
            st.session_state.waste_items.append(
                {"category": category, "quantity": quantity})
            st.toast(f"✅ Added {quantity} kg of {category}", icon="✅")
        else:
            st.toast("⚠ Enter a valid quantity", icon="⚠")

    if st.session_state.waste_items:
        st.subheader("Current Items")
        df = pd.DataFrame([{
            "Category": item["category"],
            "Quantity (kg)": f"{item['quantity']:.2f}",
            "CO₂ Emission (kg)": f"{item['quantity']*EMISSION_FACTORS[item['category']]:.2f}"
        } for item in st.session_state.waste_items])
        st.table(df)

        colA, colB = st.columns(2)

        with colA:
            if st.button("🧮 Calculate CO₂ Emissions", type="primary"):
                result = calculate_emissions(st.session_state.waste_items)
                st.session_state.calculation_result = result
                st.session_state.show_result = True

                # Save to history
                month = get_month_label()
                st.session_state.history[month] = result
                storage.setItem("carbon_wise_history",
                                str(st.session_state.history))

                st.toast("💾 Calculation complete & saved!", icon="💾")

        with colB:
            if st.button("🗑 Clear Items"):
                st.session_state.waste_items = []
                st.session_state.show_result = False
                st.session_state.calculation_result = {}
                st.toast("🧹 Items cleared", icon="🗑")

    if st.session_state.show_result and st.session_state.calculation_result:
        total = st.session_state.calculation_result["total"]
        st.metric("🌍 Total CO₂ Emissions", f"{total} kg")

# -------- TAB 2: DASHBOARD -------- #
with tab2:
    st.header("📊 Dashboard")
    if st.session_state.history:
        latest_month = sorted(st.session_state.history.keys())[-1]
        latest_data = st.session_state.history[latest_month]
        st.subheader(f"Latest Calculation — {latest_month}")

        categories = list(latest_data["by_category"].keys())
        values = list(latest_data["by_category"].values())

        fig = create_pie_chart(
            categories, values, f"CO₂ Breakdown — {latest_month}")
        st.pyplot(fig)

        st.metric("Total Emissions", f"{latest_data['total']} kg CO₂")
    else:
        st.info("No history yet. Make a calculation first!")

# -------- TAB 3: HISTORY -------- #
with tab3:
    st.header("📋 Your History")
    if st.session_state.history:
        for month, data in sorted(st.session_state.history.items(), reverse=True):
            with st.expander(f"📅 {month} — {data['total']} kg CO₂"):
                df = pd.DataFrame([{
                    "Category": item["category"],
                    "Quantity (kg)": f"{item['quantity']:.2f}",
                    "CO₂ Emission (kg)": f"{item['quantity']*EMISSION_FACTORS[item['category']]:.2f}"
                } for item in data["items"]])
                st.table(df)

        # Clear with confirmation
        if st.button("🗑 Clear All History"):
            confirm = st.checkbox(
                "⚠ Yes, I am sure I want to delete all history")
            if confirm:
                st.session_state.history = {}
                storage.setItem("carbon_wise_history", str({}))
                st.toast("🧹 All history cleared!", icon="🗑")
                time.sleep(1)
                st.rerun()
    else:
        st.info("No saved history yet.")
