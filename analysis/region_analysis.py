from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Set clean styling
sns.set_theme(style="whitegrid")

# Automatically find the project root: this file is inside /analysis, so .parent.parent is the root
BASE_DIR = Path(__file__).resolve().parent.parent

# Set up clean output directories
OUTPUT_DIR_RAJ = BASE_DIR / "outputs" / "rajnandgaon"
OUTPUT_DIR_MAK = BASE_DIR / "outputs" / "machakos"
OUTPUT_DIR_RAJ.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR_MAK.mkdir(parents=True, exist_ok=True)


# --- 1. Season Tagging Functions ---
def get_season_rajnandgaon(month):
    if month in [7, 8, 9, 10]:
        return "Kharif (Monsoon)"
    elif month in [11, 12, 1, 2, 3]:
        return "Rabi (Winter)"
    else:
        return "Zaid (Summer)"


def get_season_machakos(month):
    if month in [3, 4, 5]:
        return "Long Rains"
    elif month in [10, 11, 12]:
        return "Short Rains"
    else:
        return "Dry Season"


# --- 2. Chart Generation Function ---
def analyze_region(file_path, region_name, season_func, output_dir):
    print(f"Generating charts for {region_name}...")

    if not file_path.exists():
        print(f"Error: Could not locate file at {file_path}")
        return

    df = pd.read_csv(file_path)
    df["Season"] = df["Month"].apply(season_func)

    # Chart 1: Monthly NDVI Boxplot
    plt.figure(figsize=(9, 4.5))
    sns.boxplot(x="Month", y="NDVI", data=df, palette="Greens")
    plt.axhline(
        0.2,
        color="red",
        linestyle="--",
        label="Bare Soil Threshold (NDVI < 0.2)",
    )
    plt.title(f"{region_name} - Monthly NDVI Distribution (2003-2026)")
    plt.xlabel("Month (1 = Jan, 12 = Dec)")
    plt.ylabel("NDVI")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "ndvi_monthly_boxplot.png", dpi=200)
    plt.close()

    # Chart 2: Dual Axis (NDVI vs Temperature Trend)
    fig, ax1 = plt.subplots(figsize=(12, 4.5))
    ax1.plot(df["Date"], df["NDVI"], color="forestgreen", label="NDVI")
    ax1.set_ylabel("NDVI", color="forestgreen")

    ax2 = ax1.twinx()
    ax2.plot(
        df["Date"],
        df["LST_Celsius"],
        color="crimson",
        label="Temp (°C)",
        alpha=0.6,
    )
    ax2.set_ylabel("LST (°C)", color="crimson")

    ax1.set_xticks(df["Date"][::24])
    ax1.tick_params(axis="x", rotation=45)
    plt.title(
        f"{region_name} - Long-Term Vegetation & Temperature (2003-2026)"
    )
    plt.tight_layout()
    plt.savefig(output_dir / "ndvi_lst_trend.png", dpi=200)
    plt.close()

    # Chart 3: Seasonal Data Proportion
    plt.figure(figsize=(6, 5))
    season_counts = df["Season"].value_counts()
    plt.pie(
        season_counts,
        labels=season_counts.index,
        autopct="%1.1f%%",
        colors=["#2b83ba", "#abdda4", "#fdae61"],
        startangle=140,
    )
    plt.title(f"{region_name} - Seasonal Record Distribution")
    plt.tight_layout()
    plt.savefig(output_dir / "seasonal_proportion.png", dpi=200)
    plt.close()

    # Chart 4: Inter-Year Monthly NDVI Heatmap
    pivot_table = df.pivot(index="Year", columns="Month", values="NDVI")
    plt.figure(figsize=(10, 6))
    sns.heatmap(pivot_table, cmap="YlGn", cbar_kws={"label": "NDVI"})
    plt.title(f"{region_name} - Inter-Year Monthly NDVI Heatmap")
    plt.xlabel("Month")
    plt.ylabel("Year")
    plt.tight_layout()
    plt.savefig(output_dir / "ndvi_year_heatmap.png", dpi=200)
    plt.close()

    print(f"All charts saved for {region_name} inside {output_dir}")


# --- 3. Execute for Both Regions ---
if __name__ == "__main__":
    # Rajnandgaon dataset
    raj_path = BASE_DIR / "master_outputs" / "crop_analytics_2003_2026.csv"
    analyze_region(
        file_path=raj_path,
        region_name="Rajnandgaon (Chhattisgarh)",
        season_func=get_season_rajnandgaon,
        output_dir=OUTPUT_DIR_RAJ,
    )

    # Machakos dataset
    mak_path = (
        BASE_DIR / "machakos_outputs" / "crop_analytics_2003_2026_machakos.csv"
    )
    if not mak_path.exists():
        # Fallback to master if machakos specific analytics csv has a different name
        mak_path = (
            BASE_DIR / "master_outputs" / "crop_analytics_2003_2026.csv"
        )  # fallback[cite: 1]

    analyze_region(
        file_path=mak_path,
        region_name="Machakos (Kenya)",
        season_func=get_season_machakos,
        output_dir=OUTPUT_DIR_MAK,
    )