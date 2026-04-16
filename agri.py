import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Agri Price Analytics", layout="wide")

# ---------------- NAVIGATION ----------------
page = st.sidebar.radio("📌 Navigation", ["📘 Description", "📊 Analysis"])

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    fact = pd.read_csv("FINAL_Fact_Mandi.csv")
    geo = pd.read_csv("FINAL_Dim_Geography.csv")
    com = pd.read_csv("FINAL_Dim_Commodity.csv")
    cal = pd.read_csv("FINAL_Dim_Calendar.csv")
    cost = pd.read_csv("FINAL_Fact_Cost.csv")

    # ✅ Correct date handling
    fact["Arrival_Date_ID"] = pd.to_datetime(fact["Arrival_Date_ID"])
    cal["Date"] = pd.to_datetime(cal["Date"])

    # ✅ Merge with correct keys
    df = (
        fact.merge(geo, on="Mandi_ID", how="left")
            .merge(com, on="Commodity_ID", how="left")
            .merge(cost, left_on="Commodity_ID", right_on="Crop_ID", how="left")
            .merge(cal, left_on="Arrival_Date_ID", right_on="Date", how="left")
    )

    # ✅ Ensure cost column
    if "Total_Input_Cost" not in df.columns:
        cost_col = [c for c in df.columns if "Cost" in c][0]
        df.rename(columns={cost_col: "Total_Input_Cost"}, inplace=True)

    # ✅ Profit calculation
    df["Profit"] = df["Modal_Price"] - df["Total_Input_Cost"]

    return df


df = load_data()

# =========================================================
# 📘 PAGE 1: DESCRIPTION
# =========================================================
if page == "📘 Description":

    st.title("🌾 Agri Price Analytics")

    st.markdown("""
    ## 📌 Problem Statement

    Farmers in India lose **15–25% of their income** because:

    - They don’t have clear information about market prices  
    - Prices change a lot during harvest time  
    - They don’t know which mandi gives better prices  

    Government websites have a lot of data, but they are **hard to understand**.

    Because of this, farmers struggle to:

    - Know the best time to sell  
    - Choose the best market (mandi)  
    - Understand price changes  

    So, many farmers are forced to sell at low prices to middlemen.

---

    ## 🎯 Solution

    This system helps farmers by giving **simple and useful insights**:

    - Compare prices across different mandis.  
    - See price trends over months.  
    - Know if they are making profit or loss.  
    - Get suggestions for better selling decisions.  

---

    ## 👥 Who It's For

    - 👨‍🌾 Farmers → To get better prices.  
    - 📊 Analysts → To study market trends.  
    - 🤝 FPOs → To negotiate better deals.  

---

    ## 🚀 Key Benefits

    - Helps farmers earn better income.  
    - Makes selling decisions easier.  
    - Uses data to guide farmers in a simple way.
    """)

# =========================================================
# 📊 PAGE 2: ANALYSIS
# =========================================================
if page == "📊 Analysis":

    st.title("📊 Market Analysis Dashboard")

    # ---------------- FILTERS ----------------
    st.sidebar.subheader("🌾 Filters")

    states = sorted(df["State"].dropna().unique())
    state = st.sidebar.selectbox("State", states)

    df_state = df[df["State"] == state]

    district = st.sidebar.selectbox(
        "District", sorted(df_state["District"].dropna().unique())
    )
    df_sd = df_state[df_state["District"] == district]

    commodity = st.sidebar.selectbox(
        "Commodity", sorted(df_sd["Commodity_Name"].dropna().unique())
    )
    df_sdc = df_sd[df_sd["Commodity_Name"] == commodity]

    mandi = st.sidebar.selectbox(
        "Mandi", sorted(df_sdc["Mandi_Name"].dropna().unique())
    )

    analyze = st.sidebar.button("🔍 Analyze")

    if not analyze:
        st.info("👈 Select inputs and click Analyze")
        st.stop()

    df = df_sdc[df_sdc["Mandi_Name"] == mandi]

    if df.empty:
        st.warning("No data available")
        st.stop()

    # ---------------- KPI ----------------
    df = df.sort_values("Arrival_Date_ID")

    latest = df["Arrival_Date_ID"].max()
    dates = sorted(df["Arrival_Date_ID"].unique())
    prev = dates[-2] if len(dates) > 1 else latest

    today_price = df[df["Arrival_Date_ID"] == latest]["Modal_Price"].mean()
    yesterday_price = df[df["Arrival_Date_ID"] == prev]["Modal_Price"].mean()

    dod = (today_price - yesterday_price) / yesterday_price if yesterday_price else 0
    pvi = df["Modal_Price"].std() / df["Modal_Price"].mean()
    volume = df["Arrival_Volume_Qty"].sum()

    profit = df["Profit"].mean()
    break_even = df["Total_Input_Cost"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Live Price", f"₹ {round(today_price,2)}")
    col2.metric("DoD %", f"{round(dod*100,2)}%")
    col3.metric("Volatility", f"{round(pvi,2)}")
    col4.metric("Volume", f"{int(volume)}")

    col5, col6 = st.columns(2)
    col5.metric("Break Even", f"₹ {round(break_even,2)}")
    col6.metric("Profit", f"₹ {round(profit,2)}")

    # ---------------- SUGGESTIONS ----------------
    st.subheader("💡 Suggestions")

    if profit < 0:
        st.error("⚠️ You are in LOSS")
        st.markdown("""
        ### 👨‍🌾 For Farmers
        - The current price is lower than your cost, so selling now may give you loss.  
        - Try checking other nearby mandis, they may offer better prices.  
        - Avoid selling immediately during harvest time because supply is high and prices are low. 
        - If possible, store your crop and sell after some time when prices improve.  
        - Sell in small quantities instead of selling everything at once.  

        ---

        ### 📊 For Analysts
        - The low price shows that supply is high or demand is low in this market.  
        - Study monthly trends to understand when prices increase again.  
        - Compare this district with other regions to find better price patterns.  
        - Track price changes regularly to identify recovery trends.  

        ---

        ### 🤝 For FPOs
        - Do not sell large quantities at low prices, it may lead to big losses.  
        - Try negotiating with buyers to get a better price.  
        - Explore other mandis or markets where prices are higher.  
        - Plan selling strategy carefully instead of immediate bulk selling.  
        """)
    else:
        st.success("✅ You are in PROFIT")
        st.markdown("""
        ### 👨‍🌾 For Farmers
        - The current price is higher than your cost, so this is a good time to sell.  
        - You can sell your crop now and earn profit.  
        - Sell in parts so you can benefit if prices increase further.  
        - Check nearby mandis to see if you can get an even better price.  

        ---

        ### 📊 For Analysts
        - Higher price shows strong demand or lower supply.  
        - Identify this as a good selling period.  
        - Track trends to find peak price months.  
        - Compare regions to understand where prices are highest.  

        ---

        ### 🤝 For FPOs
        - This is a good time for bulk selling at higher prices.  
        - You can negotiate better contracts with buyers.  
        - Plan large quantity sales to maximize profit.  
        - Use this opportunity to strengthen market position.  
        """)

    # ---------------- MAP ----------------
    st.subheader("📍 Mandi Map")

    df_map = df.groupby(
        ["Mandi_Name","Latitude","Longitude"], as_index=False
    )["Modal_Price"].mean()

    fig = px.scatter_mapbox(
        df_map,
        lat="Latitude",
        lon="Longitude",
        size="Modal_Price",
        color="Modal_Price",
        zoom=5
    )
    fig.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig, use_container_width=True)

    # ---------------- TREND ----------------
    st.subheader("📈 Monthly Trend")

    trend = df.groupby("Month", as_index=False)["Modal_Price"].mean()

    fig = px.line(trend, x="Month", y="Modal_Price", markers=True)
    fig.update_traces(line_shape="spline")

    st.plotly_chart(fig, use_container_width=True)

    # ---------------- PROFIT ANALYSIS ----------------
    st.subheader("💰 Profit Analysis")

    profit_bar = df.groupby("Mandi_Name", as_index=False)["Profit"].mean()

    fig1 = px.bar(profit_bar, x="Mandi_Name", y="Profit", color="Profit")
    st.plotly_chart(fig1, use_container_width=True)

    # ---------------- BREAK EVEN ----------------
    st.subheader("📊 Break Even Trend")

    df_avg = df.groupby("Month", as_index=False).agg({
        "Modal_Price": "mean",
        "Total_Input_Cost": "mean"
    })

    fig2 = px.line(
        df_avg,
        x="Month",
        y=["Modal_Price", "Total_Input_Cost"]
    )
    fig2.update_traces(line_shape="spline")

    st.plotly_chart(fig2, use_container_width=True)