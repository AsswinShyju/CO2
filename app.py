import streamlit as st
import streamlit.components.v1 as components
from streamlit_local_storage import LocalStorage
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import time
import random
import gc

# -------- CONFIG & CONSTANTS -------- #
st.set_page_config(
    page_title="Carbon Wise — Household Waste CO₂ Calculator",
    page_icon="♻️",
    layout="centered",
)

# Enhanced animations CSS
st.markdown("""
<style>
    /* Smooth transitions for all elements */
    * {
        transition: all 0.3s ease;
    }
    
    /* Button hover animations */
    .stButton > button {
        transition: all 0.3s ease;
        border-radius: 8px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Form animations */
    .stSelectbox > div, .stNumberInput > div {
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div:hover, .stNumberInput > div:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Metric card animations */
    [data-testid="metric-container"] {
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* Table animations */
    .dataframe {
        transition: all 0.3s ease;
    }
    
    .dataframe:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Connection status styling */
    .connection-status {
        padding: 10px 20px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .connected {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .disconnected {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .connecting {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    /* Fade in animation */
    @keyframes fadeIn {
        from { 
            opacity: 0; 
            transform: translateY(20px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Slide in from left */
    @keyframes slideInLeft {
        from { 
            opacity: 0; 
            transform: translateX(-30px); 
        }
        to { 
            opacity: 1; 
            transform: translateX(0); 
        }
    }
    
    .slide-in-left {
        animation: slideInLeft 0.5s ease-out;
    }
    
    /* Scale in animation */
    @keyframes scaleIn {
        from { 
            opacity: 0; 
            transform: scale(0.9); 
        }
        to { 
            opacity: 1; 
            transform: scale(1); 
        }
    }
    
    .scale-in {
        animation: scaleIn 0.4s ease-out;
    }
    
    /* Pulse animation */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    /* Blink animation for live indicator */
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
    
    .live-indicator {
        animation: blink 1.5s infinite;
        color: #ff4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

EMISSION_FACTORS = {
    "Plastic": 6.0,
    "Paper": 1.2,
    "Food Waste": 1.9,
    "Glass": 0.85,
    "Cardboard": 1.0,
    "Textiles": 5.0,
    "Metal": 2.5,
}

COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1',
          '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']

# -------- LOCAL STORAGE -------- #


@st.cache_resource
def get_local_storage():
    return LocalStorage()


ls = get_local_storage()
HIST_KEY = "carbonwise_history_v3"


def get_history():
    try:
        raw = ls.getItem(HIST_KEY)
        return raw if isinstance(raw, dict) else {}
    except:
        return {}


def save_history(hist):
    try:
        ls.setItem(HIST_KEY, hist)
    except:
        pass


def clear_storage():
    try:
        ls.deleteItem(HIST_KEY)
    except:
        try:
            ls.setItem(HIST_KEY, {})
        except:
            pass


def get_month_label():
    return datetime.now().strftime("%B %Y")


def calculate_emissions(items):
    """Calculate emissions from items list"""
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


def simulate_esp32_reading():
    """Simulate ESP32 CO2 sensor reading"""
    # Simulate realistic CO2 readings (400-2000 ppm)
    base_reading = 450 + random.uniform(-50, 150)
    variation = random.uniform(-20, 30)
    return max(350, min(2000, base_reading + variation))


def create_co2_gauge_component(co2_value):
    """Create HTML component CO2 gauge using streamlit.components"""
    # Calculate needle angle (-90 to 90 degrees for 0-2000 ppm)
    needle_angle = -90 + (co2_value / 2000) * 180

    # Determine status
    if co2_value < 600:
        status = "🟢 Good"
        status_color = "#4CAF50"
    elif co2_value < 1000:
        status = "🟡 Moderate"
        status_color = "#FFC107"
    else:
        status = "🔴 High"
        status_color = "#F44336"

    gauge_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1e1e1e, #2d2d2d);
                display: flex;
                flex-direction: column;
                align-items: center;
                border-radius: 20px;
            }}
            
            .gauge-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 20px;
            }}
            
            .gauge-title {{
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }}
            
            .gauge {{
                position: relative;
                width: 300px;
                height: 200px;
                margin: 20px 0;
            }}
            
            .gauge-bg {{
                width: 100%;
                height: 100%;
                background: conic-gradient(from 180deg, 
                    #4CAF50 0deg 108deg,
                    #FFC107 108deg 180deg, 
                    #F44336 180deg 252deg,
                    #333 252deg 360deg);
                border-radius: 150px 150px 0 0;
                position: relative;
                overflow: hidden;
            }}
            
            .gauge-bg::before {{
                content: '';
                position: absolute;
                top: 30px;
                left: 30px;
                right: 30px;
                bottom: -15px;
                background: linear-gradient(135deg, #1e1e1e, #2d2d2d);
                border-radius: 120px 120px 0 0;
            }}
            
            .gauge-needle {{
                position: absolute;
                top: 50%;
                left: 50%;
                width: 4px;
                height: 120px;
                background: linear-gradient(to top, #fff, #ff4444);
                transform-origin: bottom center;
                transform: translate(-50%, -100%) rotate({needle_angle}deg);
                border-radius: 2px;
                transition: transform 0.5s ease-in-out;
                z-index: 10;
                box-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
            }}
            
            .gauge-needle::after {{
                content: '';
                position: absolute;
                bottom: -10px;
                left: 50%;
                width: 20px;
                height: 20px;
                background: #ff4444;
                border-radius: 50%;
                transform: translateX(-50%);
                box-shadow: 0 0 15px rgba(255, 68, 68, 0.7);
            }}
            
            .gauge-labels {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
            }}
            
            .gauge-label {{
                position: absolute;
                color: white;
                font-weight: bold;
                font-size: 14px;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
            }}
            
            .label-0 {{ bottom: 10px; left: 20px; }}
            .label-600 {{ top: 50px; left: 50%; transform: translateX(-50%); }}
            .label-1000 {{ top: 20px; right: 50px; }}
            .label-2000 {{ bottom: 10px; right: 20px; }}
            
            .co2-reading {{
                font-size: 48px;
                font-weight: bold;
                color: white;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                margin: 20px 0 10px 0;
                text-align: center;
            }}
            
            .co2-unit {{
                font-size: 18px;
                color: #ccc;
                margin-left: 5px;
            }}
            
            .co2-status {{
                font-size: 20px;
                font-weight: bold;
                margin: 10px 0;
                padding: 15px 30px;
                border-radius: 10px;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
                background: {status_color};
                color: white;
                text-align: center;
            }}
            
            .timestamp {{
                color: #ccc;
                font-size: 14px;
                margin-top: 15px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="gauge-container">
            <div class="gauge-title">Live CO₂ Reading</div>
            
            <div class="gauge">
                <div class="gauge-bg">
                    <div class="gauge-labels">
                        <div class="gauge-label label-0">0</div>
                        <div class="gauge-label label-600">600</div>
                        <div class="gauge-label label-1000">1000</div>
                        <div class="gauge-label label-2000">2000</div>
                    </div>
                </div>
                <div class="gauge-needle"></div>
            </div>
            
            <div class="co2-reading">
                {int(co2_value)}<span class="co2-unit">ppm</span>
            </div>
            
            <div class="co2-status">
                {status}
            </div>
            
            <div class="timestamp">
                Last updated: {datetime.now().strftime("%H:%M:%S")}
            </div>
        </div>
    </body>
    </html>
    """

    return gauge_html


def create_simple_pie_chart(categories, values, title):
    """Create a simple, memory-efficient pie chart"""
    fig, ax = plt.subplots(figsize=(6, 6))

    wedges, texts = ax.pie(
        values,
        labels=None,
        colors=COLORS[:len(categories)],
        startangle=90,
        wedgeprops=dict(width=0.6, edgecolor='white', linewidth=2)
    )

    for i, (cat, wedge) in enumerate(zip(categories, wedges)):
        angle = (wedge.theta2 + wedge.theta1) / 2
        x = np.cos(np.radians(angle)) * 1.1
        y = np.sin(np.radians(angle)) * 1.1

        ax.text(x, y, f'{cat}\n{values[i]:.1f} kg',
                ha='center', va='center', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=COLORS[i % len(COLORS)],
                          alpha=0.8, edgecolor='white'))

    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()

    return fig


# -------- SESSION STATE -------- #
if "waste_items" not in st.session_state:
    st.session_state.waste_items = []
if "calculation_result" not in st.session_state:
    st.session_state.calculation_result = {}
if "show_result" not in st.session_state:
    st.session_state.show_result = False
if "esp32_connected" not in st.session_state:
    st.session_state.esp32_connected = False
if "esp32_connecting" not in st.session_state:
    st.session_state.esp32_connecting = False
if "co2_readings" not in st.session_state:
    st.session_state.co2_readings = []
if "current_co2" not in st.session_state:
    st.session_state.current_co2 = 420

# -------- MAIN APP -------- #
st.markdown('<div class="fade-in">', unsafe_allow_html=True)
st.title("♻️ Carbon Wise — Household Waste CO₂ Calculator")
st.markdown("Track your household waste and calculate your carbon footprint")
st.markdown('</div>', unsafe_allow_html=True)

# -------- TABS -------- #
tab1, tab2, tab3, tab4 = st.tabs(
    ["📝 Calculator", "📊 Dashboard", "📋 History", "🔌 Connect Device"])

# -------- TAB 1: CALCULATOR -------- #
with tab1:
    st.markdown('<div class="scale-in">', unsafe_allow_html=True)
    st.header("Add Waste Items")

    with st.form("add_item_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            category = st.selectbox(
                "Select Waste Category",
                list(EMISSION_FACTORS.keys())
            )

        with col2:
            quantity = st.number_input(
                "Quantity (kg)",
                min_value=0.0,
                step=0.1,
                format="%.2f"
            )

        submitted = st.form_submit_button("➕ Add Item", type="primary")

        if submitted:
            if quantity > 0:
                new_item = {
                    "category": category,
                    "quantity": quantity,
                    "id": len(st.session_state.waste_items)
                }
                st.session_state.waste_items.append(new_item)
                st.toast(f"✅ Added {quantity} kg of {category}", icon="✅")
                st.rerun()
            else:
                st.toast("⚠️ Please enter a valid quantity", icon="⚠️")

    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.waste_items:
        st.markdown('<div class="slide-in-left">', unsafe_allow_html=True)
        st.subheader("Current Items")

        table_col, action_col = st.columns([5, 1])

        with table_col:
            df_items = []
            for i, item in enumerate(st.session_state.waste_items):
                emission = item["quantity"] * \
                    EMISSION_FACTORS[item["category"]]
                df_items.append({
                    "Category": item["category"],
                    "Quantity (kg)": f"{item['quantity']:.2f}",
                    "CO₂ Emission (kg)": f"{emission:.2f}"
                })

            df = pd.DataFrame(df_items)
            st.dataframe(df, use_container_width=True, hide_index=True)

        with action_col:
            st.write("**🗑️**")
            st.write("")

            for i, item in enumerate(st.session_state.waste_items):
                if st.button("🗑️",
                             key=f"remove_{i}_{item.get('id', i)}",
                             help=f"Remove {item['category']}",
                             use_container_width=True):
                    st.session_state.waste_items.pop(i)
                    st.toast(f"🗑️ Removed {item['category']}", icon="🗑️")
                    st.rerun()

        if st.session_state.waste_items:
            total_quantity = sum(item["quantity"]
                                 for item in st.session_state.waste_items)
            total_emission = sum(item["quantity"] * EMISSION_FACTORS[item["category"]]
                                 for item in st.session_state.waste_items)

            st.markdown("**Summary:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Items", len(st.session_state.waste_items))
            with col2:
                st.metric("Total Weight", f"{total_quantity:.2f} kg")
            with col3:
                st.metric("Total CO₂", f"{total_emission:.2f} kg")

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("💡 No items added yet. Add some waste items above!")

    st.markdown('<div class="scale-in">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🧮 Calculate CO₂ Emissions", type="primary", use_container_width=True):
            if st.session_state.waste_items:
                with st.spinner("Calculating emissions..."):
                    time.sleep(0.8)

                    result = calculate_emissions(st.session_state.waste_items)
                    st.session_state.calculation_result = result

                    history = get_history()
                    month_label = get_month_label()
                    history[month_label] = result
                    save_history(history)

                    st.session_state.show_result = True
                    st.toast("💾 Calculation complete and saved!", icon="💾")
                    st.rerun()
            else:
                st.toast("⚠️ No items to calculate", icon="⚠️")

    with col2:
        if st.button("🗑️ Clear All Items", use_container_width=True):
            if st.session_state.waste_items:
                st.session_state.waste_items = []
                st.session_state.show_result = False
                st.session_state.calculation_result = {}
                st.toast("🧹 All items cleared", icon="🗑️")
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.calculation_result and st.session_state.show_result:
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        total = st.session_state.calculation_result["total"]
        st.metric(
            label="🌍 Total CO₂ Emissions",
            value=f"{total} kg",
            help="Based on standard emission factors"
        )

        if st.session_state.calculation_result.get("by_category"):
            st.subheader("📊 Breakdown by Category")

            for cat, emission in st.session_state.calculation_result["by_category"].items():
                progress_value = emission / total if total > 0 else 0
                st.write(f"**{cat}**: {emission:.2f} kg CO₂")
                st.progress(progress_value,
                            text=f"{progress_value*100:.1f}% of total")

        st.markdown('</div>', unsafe_allow_html=True)

# -------- TAB 2: DASHBOARD -------- #
with tab2:
    st.header("📊 Emissions Dashboard")

    history = get_history()

    if not history:
        st.warning(
            "📈 No calculation history yet. Please make a calculation first.")
    else:
        latest_month = sorted(history.keys())[-1]
        latest_data = history[latest_month]

        if not latest_data.get("by_category"):
            if latest_data.get("items"):
                latest_data = calculate_emissions(latest_data["items"])
                history[latest_month] = latest_data
                save_history(history)

        if latest_data.get("by_category"):
            categories = list(latest_data["by_category"].keys())
            values = list(latest_data["by_category"].values())

            st.subheader(f"Latest Calculation: {latest_month}")

            with st.spinner("Loading chart..."):
                fig = create_simple_pie_chart(
                    categories, values, f'CO₂ Emissions Breakdown - {latest_month}')
                st.pyplot(fig, clear_figure=True, use_container_width=True)
                plt.close(fig)
                gc.collect()

            st.markdown('<div class="pulse">', unsafe_allow_html=True)
            st.metric(
                label="Total Monthly Emissions",
                value=f"{latest_data['total']} kg CO₂",
                delta=f"From {len(latest_data.get('items', []))} items"
            )
            st.markdown('</div>', unsafe_allow_html=True)

# -------- TAB 3: HISTORY -------- #
with tab3:
    st.header("📋 Calculation History")

    history = get_history()

    if not history:
        st.info(
            "📚 No calculation history yet. Your monthly summaries will appear here.")
    else:
        for i, (month, data) in enumerate(sorted(history.items(), reverse=True)):
            if not data.get("by_category") and data.get("items"):
                data = calculate_emissions(data["items"])
                history[month] = data
                save_history(history)

            with st.expander(f"📅 {month} — {data.get('total', 0)} kg CO₂", expanded=(i == 0)):
                if data.get("items"):
                    st.write("**Items Added:**")

                    history_df = []
                    for item in data["items"]:
                        emission = item["quantity"] * \
                            EMISSION_FACTORS[item["category"]]
                        history_df.append({
                            "Category": item["category"],
                            "Quantity (kg)": f"{item['quantity']:.2f}",
                            "CO₂ Emission (kg)": f"{emission:.2f}"
                        })

                    if history_df:
                        st.dataframe(pd.DataFrame(history_df),
                                     use_container_width=True, hide_index=True)

                if data.get("by_category"):
                    st.write("**Category Breakdown:**")
                    breakdown_df = []
                    total = data.get("total", 1)
                    for cat, emission in data["by_category"].items():
                        percentage = (emission / total) * \
                            100 if total > 0 else 0
                        breakdown_df.append({
                            "Category": cat,
                            "Total Emission (kg CO₂)": f"{emission:.2f}",
                            "Percentage": f"{percentage:.1f}%"
                        })

                    if breakdown_df:
                        st.dataframe(pd.DataFrame(breakdown_df),
                                     use_container_width=True, hide_index=True)

    if history:
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        if st.button("🗑️ Clear All History", type="secondary"):
            clear_storage()
            st.toast("🧹 History cleared successfully", icon="🗑️")
            time.sleep(0.5)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# -------- TAB 4: CONNECT DEVICE (FIXED GAUGE) -------- #
with tab4:
    st.header("🔌 Connect ESP32 Device")

    # Connection Status
    if st.session_state.esp32_connecting:
        st.markdown(
            '<div class="connection-status connecting">🔄 Connecting to ESP32...</div>', unsafe_allow_html=True)
    elif st.session_state.esp32_connected:
        st.markdown(
            '<div class="connection-status connected">✅ ESP32 Connected - Live Data</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="connection-status disconnected">❌ ESP32 Disconnected</div>', unsafe_allow_html=True)

    # Connection Controls
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔌 Connect ESP32", type="primary", disabled=st.session_state.esp32_connected or st.session_state.esp32_connecting):
            st.session_state.esp32_connecting = True
            st.rerun()

    with col2:
        if st.button("🔄 Refresh", disabled=not st.session_state.esp32_connected):
            if st.session_state.esp32_connected:
                st.session_state.current_co2 = simulate_esp32_reading()
                st.toast("🔄 Data refreshed", icon="🔄")
                st.rerun()

    with col3:
        if st.button("❌ Disconnect", type="secondary", disabled=not st.session_state.esp32_connected):
            st.session_state.esp32_connected = False
            st.session_state.esp32_connecting = False
            st.toast("❌ ESP32 disconnected", icon="❌")
            st.rerun()

    # Handle connection process
    if st.session_state.esp32_connecting and not st.session_state.esp32_connected:
        with st.spinner("Connecting to ESP32..."):
            time.sleep(2)
            st.session_state.esp32_connected = True
            st.session_state.esp32_connecting = False
            st.session_state.current_co2 = simulate_esp32_reading()
            st.toast("✅ ESP32 connected successfully!", icon="✅")
            st.rerun()

    # Live CO2 Display with Fixed HTML Component
    if st.session_state.esp32_connected:
        # Update CO2 reading
        if 'last_update' not in st.session_state:
            st.session_state.last_update = time.time()

        if time.time() - st.session_state.last_update > 5:
            st.session_state.current_co2 = simulate_esp32_reading()
            st.session_state.last_update = time.time()
            st.session_state.co2_readings.append({
                'time': datetime.now().strftime("%H:%M:%S"),
                'co2': st.session_state.current_co2
            })
            if len(st.session_state.co2_readings) > 10:
                st.session_state.co2_readings = st.session_state.co2_readings[-10:]

        # Display live indicator
        st.markdown('<p class="live-indicator">🔴 LIVE</p>',
                    unsafe_allow_html=True)

        # Display gauge using components.html (this will definitely work!)
        gauge_html = create_co2_gauge_component(st.session_state.current_co2)
        components.html(gauge_html, height=500)

        # Recent readings table
        if st.session_state.co2_readings:
            st.subheader("📊 Recent Readings")
            recent_df = pd.DataFrame(st.session_state.co2_readings[-5:])
            recent_df['CO₂ (ppm)'] = recent_df['co2'].round(0).astype(int)
            recent_df['Time'] = recent_df['time']
            st.dataframe(
                recent_df[['Time', 'CO₂ (ppm)']],
                use_container_width=True,
                hide_index=True
            )

        time.sleep(2)
        st.rerun()

    else:
        st.info("🔌 Connect your ESP32 device to see live CO₂ readings")

        st.markdown("""
        ### 📋 ESP32 Setup Instructions:
        
        1. **Flash your ESP32** with the CO₂ sensor firmware
        2. **Connect CO₂ sensor** (MH-Z19B or similar) to your ESP32
        3. **Ensure WiFi connection** on your ESP32 device
        4. **Click Connect** to establish connection
        5. **View live readings** in the odometer display
        
        ### 📊 CO₂ Levels Guide:
        - **🟢 350-600 ppm**: Good air quality
        - **🟡 600-1000 ppm**: Moderate air quality  
        - **🔴 1000+ ppm**: Poor air quality - ventilation needed
        """)

# -------- FOOTER INFO -------- #
st.markdown('<div class="fade-in">', unsafe_allow_html=True)
with st.expander("ℹ️ Emission Factors Used"):
    st.write("**CO₂ emissions per kg of waste:**")
    factors_df = []
    for category, factor in EMISSION_FACTORS.items():
        factors_df.append({
            "Category": category,
            "Emission Factor": f"{factor} kg CO₂/kg"
        })

    st.dataframe(pd.DataFrame(factors_df),
                 use_container_width=True, hide_index=True)
    st.write("*Note: These are standard emission factors and may vary by region and waste management practices.*")
st.markdown('</div>', unsafe_allow_html=True)
