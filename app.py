from pathlib import Path
from analysis.rotation_engine import get_soil_baseline, get_strategies_dataframe
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="AgroResilience | NASA Space Apps",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent

# --- HEADER ---
st.title("🌱 AgroResilience: Decision-Support Tool")
st.markdown(
    "### *NASA Earth Observations for Adaptive Crop Rotation & Soil Health*"
)
st.caption(
    "Synthesizing 23 years (2003–2026) of NASA MODIS (NDVI), ECOSTRESS/NASA POWER (LST), and GPM Precipitation with local SoilGrids 2.0 profiles."
)
st.divider()

# --- SIDEBAR REGION SELECTION ---
st.sidebar.header("📍 Study Region Selector")
region_option = st.sidebar.radio(
    "Choose Agricultural Zone:",
    ["Rajnandgaon (Chhattisgarh, India)", "Machakos (Kenya)"],
)

is_raj = "Rajnandgaon" in region_option
region_key = "rajnandgaon" if is_raj else "machakos"
output_path = BASE_DIR / "outputs" / region_key

# --- SECTION 1: REGIONAL SUMMARY METRICS ---
st.header("1. Agro-Climatic & Soil Baseline")
soil = get_soil_baseline(region_key)

col_s1, col_s2, col_s3 = st.columns(3)
col_s1.metric("Soil Classification", soil["Soil Type"].split("(")[0].strip())
col_s2.metric("Soil Organic Carbon (SOC)", soil["Organic Carbon"])
col_s3.metric("Soil pH", soil["pH"])
st.info(f"⚠️ **Primary Vulnerability:** {soil['Key Vulnerability']}")

st.divider()

# --- SECTION 2: SATELLITE CLIMATE & VEGETATION DIAGNOSTICS ---
st.header("2. Environmental & Climate Stress Diagnostics (NASA Data)")

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Monthly Vegetation Health (NDVI)")
    ndvi_box = output_path / "ndvi_monthly_boxplot.png"
    if ndvi_box.exists():
        st.image(
            str(ndvi_box),
            caption="Vulnerability Window: Months dipping below the red line (NDVI < 0.20) represent bare, exposed soil.",
        )
    else:
        st.warning("Graph not found. Run region_analysis.py first.")

with col_g2:
    st.subheader("Historical Climate Stress (NDVI vs Temp)")
    trend_img = output_path / "ndvi_lst_trend.png"
    if trend_img.exists():
        st.image(
            str(trend_img),
            caption="Correlation: High Land Surface Temperature (LST) peaks directly coincide with vegetation collapse.",
        )
    else:
        st.warning("Graph not found. Run region_analysis.py first.")

with st.expander("📊 View Multi-Decadal Heatmap & Seasonal Proportions"):
    col_g3, col_g4 = st.columns(2)
    with col_g3:
        heatmap_img = output_path / "ndvi_year_heatmap.png"
        if heatmap_img.exists():
            st.image(
                str(heatmap_img),
                caption="23-Year Monthly NDVI Heatmap (consistency of dry/green seasons across decades).",
            )
    with col_g4:
        season_img = output_path / "seasonal_proportion.png"
        if season_img.exists():
            st.image(
                str(season_img),
                caption="Distribution of records across regional agricultural seasons.",
            )

st.divider()

# --- SECTION 3: ROTATION STRATEGY COMPARISON MATRIX ---
st.header("3. Adaptive Crop Rotation Decision Engine")
st.markdown(
    "Comparing the farmer's **current baseline** against two **climate-adapted alternatives** designed to improve soil health and water resilience."
)

strategies_df = get_strategies_dataframe(region_key)

tab1, tab2, tab3 = st.tabs(
    [
        "1️⃣ Baseline (Current)",
        "2️⃣ Soil Health & Nitrogen",
        "3️⃣ Climate & Water Resilient",
    ]
)

for tab, idx in zip([tab1, tab2, tab3], [0, 1, 2]):
    row = strategies_df.iloc[idx]
    with tab:
        st.subheader(row["Strategy ID"])
        st.success(f"**Crop Rotation Sequence:** {row['Rotation Pattern']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Ground Cover Duration", row["Ground Cover Window"])
        c2.markdown(f"**Soil Impact:**\n{row['Soil Health Impact']}")
        c3.markdown(
            f"**Water & Economic Resilience:**\n{row['Water Resilience Score']}\n\n*{row['Economic/Farmer Benefit']}*"
        )

st.subheader("Summary Comparison Table")
st.dataframe(strategies_df, use_container_width=True)