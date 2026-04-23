import streamlit as st
import pandas as pd
import plotly.express as px
import cohere
import os

st.set_page_config(page_title="Agri Price Analytics", layout="wide")

# ================= ADVANCED PREMIUM UI =================
st.markdown("""
<style>

/* ===== GLOBAL ===== */
.main {
    background: linear-gradient(135deg, #f8fafc, #eef2ff);
    font-family: 'Inter', sans-serif;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* ===== HEADINGS ===== */
h1 {
    font-size: 2.2rem;
    font-weight: 700;
    color: #111827;
}

h2, h3 {
    color: #1f2937;
    font-weight: 600;
}

/* ===== KPI CARDS ===== */
[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.75);
    border: 1px solid rgba(229, 231, 235, 0.6);
    backdrop-filter: blur(8px);
    padding: 16px;
    border-radius: 14px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

/* ===== BUTTON ===== */
.stButton>button {
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 18px;
    font-weight: 600;
}

.stButton>button:hover {
    transform: scale(1.03);
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
}

/* ===== TABS ===== */
button[data-baseweb="tab"] {
    font-size: 15px;
    font-weight: 600;
    color: #6b7280;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #2563eb;
    border-bottom: 2px solid #2563eb;
}

/* ===== COLORED AI INSIGHTS ===== */
.blue-box {
    background-color: #eff6ff;
    border-left: 6px solid #3b82f6;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 10px;
}

.red-box {
    background-color: #fef2f2;
    border-left: 6px solid #ef4444;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 10px;
}

.orange-box {
    background-color: #fff7ed;
    border-left: 6px solid #f97316;
    padding: 12px;
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)
# ---------------- COHERE CLIENT ----------------
co = cohere.Client(os.getenv("COHERE_API_KEY"))

# ---------------- NAVIGATION ----------------
page = st.sidebar.radio("📌 Navigation", ["📘 Description", "📊 Analysis", "🌱 Crop Planning"])

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    fact = pd.read_csv("FINAL_Fact_Mandi.csv")
    geo = pd.read_csv("FINAL_Dim_Geography.csv")
    com = pd.read_csv("FINAL_Dim_Commodity.csv")
    cal = pd.read_csv("FINAL_Dim_Calendar.csv")
    cost = pd.read_csv("FINAL_Fact_Cost.csv")

    fact["Arrival_Date_ID"] = pd.to_datetime(fact["Arrival_Date_ID"])
    cal["Date"] = pd.to_datetime(cal["Date"])

    df = (
        fact.merge(geo, on="Mandi_ID", how="left")
            .merge(com, on="Commodity_ID", how="left")
            .merge(cost, left_on="Commodity_ID", right_on="Crop_ID", how="left")
            .merge(cal, left_on="Arrival_Date_ID", right_on="Date", how="left")
    )

    if "Total_Input_Cost" not in df.columns:
        cost_col = [c for c in df.columns if "Cost" in c][0]
        df.rename(columns={cost_col: "Total_Input_Cost"}, inplace=True)

    df["Profit"] = df["Modal_Price"] - df["Total_Input_Cost"]

    if "Month" not in df.columns:
        df["Month"] = df["Arrival_Date_ID"].dt.month_name()

    return df

df = load_data()

def format_quintals(x):
    if x >= 100000:
        return f"{round(x/100000,2)} Lakh Quintals"
    elif x >= 1000:
        return f"{round(x/1000,2)} K Quintals"
    else:
        return f"{round(x,2)} Quintals"

# ---------------- AI ----------------
@st.cache_data(ttl=600)
def get_ai_insights(price, cost, profit, dod, volume, mandi, commodity):

    trend = "increasing" if dod > 0 else "decreasing"

    prompt = f"""
    Commodity: {commodity}
    Mandi: {mandi}
    Price: ₹{price}
    Cost: ₹{cost}
    Profit: ₹{profit}
    Trend: {trend}
    Volume: {volume}

    Give output strictly in this format:

    Causes:
    -
    -

    Insights:
    -
    -

    Recommendation:
    -
    """

    try:
        response = co.chat(model="command-r7b-12-2024", message=prompt)
        return response.text if hasattr(response, "text") else response.message.content
    except:
        return "AI unavailable"

# ---------------- CROP ----------------
@st.cache_data(ttl=600)
def recommend_crop(df, state, district, month):
    df_filtered = df[(df["State"]==state)&(df["District"]==district)&(df["Month"]==month)]
    if df_filtered.empty:
        return None
    crop_profit = df_filtered.groupby("Commodity_Name",as_index=False)["Profit"].mean()
    return crop_profit.sort_values("Profit",ascending=False).head(3)

# =========================================================
# 📘 DESCRIPTION PAGE
# =========================================================
if page == "📘 Description":

    st.title("🌾 Agri Price Analytics")

    st.markdown("""
    ## 📌 Problem Statement

    Farmers in India lose 15–25% of their income because:

    - They don’t have clear information about market prices  
    - Prices change a lot during harvest time  
    - They don’t know which mandi gives better prices  

    Government websites have a lot of data, but they are hard to understand.

    Because of this, farmers struggle to:

    - Know the best time to sell  
    - Choose the best market (mandi)  
    - Understand price changes  

    So, many farmers are forced to sell at low prices to middlemen.

    ---

    ## 🎯 Solution

    This system helps farmers by giving simple and useful insights:

    - Compare prices across different mandis.  
    - See price trends over months.  
    - Know if they are making profit or loss.  
    - Get suggestions for better selling decisions.  

    ---

    ## 🚀 Key Benefits

    - Helps farmers earn better income.  
    - Makes selling decisions easier.  
    - Uses data to guide farmers in a simple way.
    """)

# ---------------- ANALYSIS ----------------
if page == "📊 Analysis":

    # ------------------ DARK THEME CSS ------------------
    st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: white;
    }
    .css-1d391kg, .css-1v0mbdj {
        background-color: #161b22;
    }
    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 8px;
        padding: 10px;
    }
    .stSuccess {
        background-color: #0f5132 !important;
        color: #d1e7dd !important;
    }
    .stError {
        background-color: #842029 !important;
        color: #f8d7da !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Market Analysis Dashboard")

    # ------------------ SIDEBAR ------------------
    state = st.sidebar.selectbox("🌍 State", sorted(df["State"].dropna().unique()))
    df_state = df[df["State"] == state]

    district = st.sidebar.selectbox("🏙️ District", sorted(df_state["District"].dropna().unique()))
    df_sd = df_state[df_state["District"] == district]

    commodity = st.sidebar.selectbox("🌾 Commodity", sorted(df_sd["Commodity_Name"].dropna().unique()))
    df_sdc = df_sd[df_sd["Commodity_Name"] == commodity]

    mandi = st.sidebar.selectbox("🏪 Mandi", sorted(df_sdc["Mandi_Name"].dropna().unique()))

    if not st.sidebar.button("🔍 Analyze"):
        st.stop()

    df = df_sdc[df_sdc["Mandi_Name"] == mandi]

    # ------------------ KPI CALCULATIONS ------------------
    latest = df["Arrival_Date_ID"].max()
    today_price = df[df["Arrival_Date_ID"] == latest]["Modal_Price"].mean()
    profit = df["Profit"].mean()
    break_even = df["Total_Input_Cost"].mean()
    volume = df["Arrival_Volume_Qty"].sum()

    ## ------------------ KPI CARDS (ENHANCED UI) ------------------

    def kpi_card(title, value, color):
            st.markdown(f"""
            <div style="
                background: linear-gradient(145deg, #161b22, #0e1117);
                padding: 18px;
                border-radius: 12px;
                border-left: 6px solid {color};
                box-shadow: 0 4px 15px rgba(0,0,0,0.4);
                text-align: center;
            ">
                <div style="font-size:14px; color:#8b949e;">{title}</div>
                <div style="font-size:26px; font-weight:bold; color:{color};">
                    {value}
                </div>
            </div>
            """, unsafe_allow_html=True)


        # Dynamic colors
    price_color = "#58a6ff"
    profit_color = "#2ea043" if profit > 0 else "#f85149"
    volume_color = "#d29922"
    breakeven_color = "#ff7b72"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
            kpi_card("💰 Market Price", f"₹ {round(today_price,2)}", price_color)

    with col2:
            kpi_card("📈 Profit", f"₹ {round(profit,2)}", profit_color)

    with col3:
            kpi_card("📦 Arrival Volume", format_quintals(volume), volume_color)

    with col4:
            kpi_card("⚖️ Break-even", f"₹ {round(break_even,2)}", breakeven_color)
            st.markdown("---")

    # ------------------ DECISION BOX ------------------
    if profit > 0:
        st.success("🟢 PROFIT ZONE → Ideal time to SELL in this mandi.")
    else:
        st.error("🔴 LOSS ZONE → Better to HOLD and wait for price increase.")

    st.info("💡 Insight: Decision is based on comparison between market price and total input cost.")

    st.markdown("---")

    # ------------------ TABS ------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🗺️ Map", "📈 Price Trend", "💰 Break-even", "📍 Best Mandi", "🤖 AI Insights"]
    )

    # ------------------ MAP ------------------
    with tab1:
        st.subheader("🗺️ Geographical Distribution")

        if "Latitude" in df.columns:
            fig = px.scatter_mapbox(
                df,
                lat="Latitude",
                lon="Longitude",
                color="Profit",
                size="Arrival_Volume_Qty",
                zoom=5
            )
            fig.update_layout(
                mapbox_style="carto-darkmatter",
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117"
            )
            st.plotly_chart(fig, use_container_width=True)

    # ------------------ PRICE TREND ------------------
    with tab2:
        st.subheader("📈 Monthly Price Trend")

        month_order = ["January","February","March","April","May","June",
                       "July","August","September","October","November","December"]

        df_trend = df.groupby("Month", as_index=False)["Modal_Price"].mean()
        df_trend = pd.DataFrame({"Month": month_order}).merge(df_trend, on="Month", how="left").fillna(0)

        fig = px.line(df_trend, x="Month", y="Modal_Price", markers=True)
        fig.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ------------------ BREAK EVEN ------------------
    with tab3:
        st.subheader("💰 Price vs Break-even")

        df_pc = df.groupby("Month", as_index=False)["Modal_Price"].mean()
        df_pc = pd.DataFrame({"Month": month_order}).merge(df_pc, on="Month", how="left").fillna(0)

        fig = px.line(df_pc, x="Month", y="Modal_Price", markers=True)
        fig.add_hline(y=break_even, line_dash="dash", line_color="red")

        fig.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ------------------ BEST MANDI ------------------
    with tab4:
        st.subheader("📍 Best Performing Mandi")

        best = df_sd.groupby("Mandi_Name")["Profit"].mean().reset_index().sort_values("Profit", ascending=False).iloc[0]

        st.success(f"🏆 Best Mandi: {best['Mandi_Name']}")
        st.write(f"💰 Avg Profit: ₹ {round(best['Profit'],2)}")

    # ------------------ AI INSIGHTS ------------------
    with tab5:
        
        st.subheader("🤖 AI-Based Recommendation")

        # ------------------ STYLE ------------------
        st.markdown("""
        <style>
        .ai-card {
            padding: 18px;
            border-radius: 12px;
            margin-top: 15px;
            font-size: 15px;
            line-height: 1.6;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        }

        .causes {
            background-color: #1f2937;
            border-left: 6px solid #60a5fa;
            color: #e5e7eb;
        }

        .insights {
            background-color: #052e16;
            border-left: 6px solid #22c55e;
            color: #bbf7d0;
        }

        .recommendation {
            background-color: #3b0764;
            border-left: 6px solid #a855f7;
            color: #e9d5ff;
        }

        .ai-buttons button {
            width: 100%;
            height: 45px;
            border-radius: 10px !important;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)

        # ------------------ GET AI TEXT ------------------
        ai_text = get_ai_insights(
            today_price,
            break_even,
            profit,
            0,
            volume,
            mandi,
            commodity
        )
        # ------------------ PARSE OUTPUT ------------------
        def extract_section(text, section):
            try:
                part = text.split(section + ":")[1]
                next_sections = ["Causes:", "Insights:", "Recommendation:"]
                for sec in next_sections:
                    if sec != section + ":" and sec in part:
                        part = part.split(sec)[0]
                return part.strip()
            except:
                return "No data available"
        causes_text = extract_section(ai_text, "Causes")
        insights_text = extract_section(ai_text, "Insights")
        recommend_text = extract_section(ai_text, "Recommendation")

        # ------------------ DISPLAY ------------------
        
        def to_bullets(text):
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            bullets = "".join([f"<li>{line.replace('-', '').strip()}</li>" for line in lines])
            return f"<ul>{bullets}</ul>"


        st.markdown(f"""
            <div class="ai-card causes">
                <b>📌 Causes Affecting Price</b><br><br>
                {to_bullets(causes_text)}
            
            """, unsafe_allow_html=True)
        
        def to_bullets(text):
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            bullets = "".join([f"<li>{line.replace('-', '').strip()}</li>" for line in lines])
            return f"<ul>{bullets}</ul>"

        
        st.markdown(f"""
            <div class="ai-card insights">
                <b>📊 Market Insights</b><br><br>
                {to_bullets(insights_text)}
            
            """, unsafe_allow_html=True)

        
        def to_bullets(text):
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            bullets = "".join([f"<li>{line.replace('-', '').strip()}</li>" for line in lines])
            return f"<ul>{bullets}</ul>"


        st.markdown(f"""
         <div class="ai-card recommendation">
            <b>🎯  Recommendation</b><br><br>
            {to_bullets(recommend_text)}
        
        """, unsafe_allow_html=True)

        
# ---------------- CROP ----------------
if page == "🌱 Crop Planning":

    # ------------------ DARK UI STYLE ------------------
    st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: white;
    }

    .crop-card {
        background: linear-gradient(145deg, #161b22, #0e1117);
        padding: 18px;
        border-radius: 12px;
        border-left: 6px solid #2ea043;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-bottom: 12px;
    }

    .crop-title {
        font-size: 18px;
        font-weight: bold;
        color: #58a6ff;
    }

    .crop-profit {
        font-size: 16px;
        color: #2ea043;
        margin-top: 5px;
    }

    .section-box {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🌱 Smart Crop Planning")

    # ------------------ INPUT SECTION ------------------
    st.markdown('<div class="section-box">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        state = st.selectbox("🌍 State", sorted(df["State"].dropna().unique()))

    with col2:
        district = st.selectbox("🏙️ District", sorted(df[df["State"]==state]["District"].unique()))

    with col3:
        month = st.selectbox("📅 Month", sorted(df["Month"].unique()))

    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ BUTTON ------------------
    if st.button("🚀 Recommend Best Crops"):

        crops = recommend_crop(df, state, district, month)

        if crops is not None:

            st.markdown("### 🌾 Top 3 Crops to Maximize Profit")

            # ------------------ CROP CARDS ------------------
            for i, (_, row) in enumerate(crops.iterrows(), start=1):

                profit = round(row['Profit'], 2)

                st.markdown(f"""
                <div class="crop-card">
                    <div class="crop-title">
                        🥇 Rank {i}: {row['Commodity_Name']}
                    </div>
                    <div class="crop-profit">
                        💰 Expected Profit: ₹ {profit}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        else:
            st.warning("⚠️ No data available for selected inputs")