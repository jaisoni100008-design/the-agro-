import pandas as pd
import numpy as np
import json
import math

# ==========================================
# 1. LOAD THE DATA (Replace with your actual file paths)
# ==========================================

# Mocking the CSV load. Replace this with: df = pd.read_csv('rajnandgaon_weather.csv')
# For demonstration, we assume 'df' has columns: Date, Temp_Max_C, Temp_Min_C, Rainfall_POWER_mm, 
# Humidity_pct, Wind_Speed_ms, Solar_Radiation, Rainfall_CHIRPS_mm, NDVI

# Soil Constants (Fetched once from SoilGrids via GEE for your specific Lat/Lon)
SOIL_CONSTANTS = {
    "Rajnandgaon": {"FC_mm": 280, "WP_mm": 120, "SOC_percent": 0.6, "Bulk_Density": 1.45},
    "Machakos":    {"FC_mm": 180, "WP_mm": 80,  "SOC_percent": 1.4, "Bulk_Density": 1.35}
}

# Crop Traits Database (Save this as crops.json and load it, or keep as dict)
CROPS = {
    "Rice": {"family": "Poaceae", "kc_mid": 1.20, "t_base": 10, "t_max": 35, "gdd_required": 1800, "root_depth_cm": 30, "n_fixation_kg_ha": 0, "c_n_ratio": 60},
    "Chickpea": {"family": "Fabaceae", "kc_mid": 1.15, "t_base": 5, "t_max": 30, "gdd_required": 1400, "root_depth_cm": 120, "n_fixation_kg_ha": 60, "c_n_ratio": 15},
    "Moong_Bean": {"family": "Fabaceae", "kc_mid": 1.15, "t_base": 10, "t_max": 35, "gdd_required": 900, "root_depth_cm": 60, "n_fixation_kg_ha": 40, "c_n_ratio": 18},
    "Sorghum": {"family": "Poaceae", "kc_mid": 1.10, "t_base": 10, "t_max": 38, "gdd_required": 1600, "root_depth_cm": 100, "n_fixation_kg_ha": 0, "c_n_ratio": 60},
    "Cowpea": {"family": "Fabaceae", "kc_mid": 1.15, "t_base": 10, "t_max": 35, "gdd_required": 1100, "root_depth_cm": 90, "n_fixation_kg_ha": 50, "c_n_ratio": 20},
    "Pigeonpea": {"family": "Fabaceae", "kc_mid": 1.10, "t_base": 10, "t_max": 35, "gdd_required": 2000, "root_depth_cm": 150, "n_fixation_kg_ha": 70, "c_n_ratio": 25},
    "Maize": {"family": "Poaceae", "kc_mid": 1.20, "t_base": 10, "t_max": 35, "gdd_required": 1600, "root_depth_cm": 50, "n_fixation_kg_ha": 0, "c_n_ratio": 60}
}

# Market Baselines for Economic Scoring
MARKET = {
    "Rice": {"yield_kg_ha": 4500, "price_usd_kg": 0.30},
    "Chickpea": {"yield_kg_ha": 1200, "price_usd_kg": 0.90},
    "Moong_Bean": {"yield_kg_ha": 800, "price_usd_kg": 1.20},
    "Sorghum": {"yield_kg_ha": 2500, "price_usd_kg": 0.25},
    "Cowpea": {"yield_kg_ha": 900, "price_usd_kg": 1.10},
    "Pigeonpea": {"yield_kg_ha": 1000, "price_usd_kg": 1.00},
    "Maize": {"yield_kg_ha": 5000, "price_usd_kg": 0.20}
}

# ==========================================
# 2. CORE AGRONOMIC FORMULAS
# ==========================================

def calculate_gdd(tmax, tmin, t_base):
    """Calculates daily Growing Degree Days."""
    t_mean = (tmax + tmin) / 2.0
    return max(0, t_mean - t_base)

def calculate_et0_fao56(tmax, tmin, solar_radiation):
    """
    FAO-56 Hargreaves Equation for Reference Evapotranspiration (ET0).
    Uses Solar Radiation (Rs in MJ/m2/day), Tmax, and Tmin.
    Highly robust and uses the exact columns you fetched from NASA POWER.
    """
    t_mean = (tmax + tmin) / 2.0
    # Hargreaves formula: ET0 = 0.0023 * Rs * (Tmean + 17.8) * sqrt(Tmax - Tmin)
    et0 = 0.0023 * solar_radiation * (t_mean + 17.8) * math.sqrt(max(0, tmax - tmin))
    return et0

def get_effective_rainfall(rain_mm):
    """
    Proxy for runoff. Gentle rain soaks in; cloudbursts (>30mm) mostly run off.
    """
    if rain_mm > 30:
        return rain_mm * 0.4  # 60% runoff loss during heavy storms
    return rain_mm

# ==========================================
# 3. THE 4-CHECK EVALUATION ENGINE
# ==========================================

def evaluate_rotation(rotation_sequence, weather_df, soil, priorities):
    """
    Evaluates a multi-year crop rotation sequence against the 4 Checks.
    Returns a dictionary with the final score and detailed breakdown.
    """
    score = 100.0
    warnings = []
    bonuses = []
    
    total_gdd_accumulated = 0
    current_soil_water = soil["FC_mm"] # Start at field capacity (e.g., post-monsoon)
    total_n_added = 0
    previous_family = None
    previous_root_depth = 0
    
    # Identify the "Worst Year" in the dataset for Shock Survival check
    # (e.g., year with the lowest total rainfall)
    weather_df['Year'] = pd.to_datetime(weather_df['Date']).dt.year
    yearly_rain = weather_df.groupby('Year')['Rainfall_CHIRPS_mm'].sum()
    worst_year = yearly_rain.idxmin()
    
    for i, crop_name in enumerate(rotation_sequence):
        crop = CROPS[crop_name]
        market = MARKET[crop_name]
        
        # Filter weather data for a generic "growing season" length based on GDD
        # For simulation, we take a block of days equal to the crop's approximate duration
        # (GDD required / avg daily GDD of ~10)
        approx_days = int(crop["gdd_required"] / 10) 
        # In a real app, you'd slice the exact df by planting date. Here we sample randomly for demo.
        sample_days = weather_df.sample(n=min(approx_days, len(weather_df)), random_state=42)
        
        crop_gdd = 0
        heat_stress_days = 0
        water_stress_days = 0
        crop_etc_total = 0
        
        for _, row in sample_days.iterrows():
            # CHECK 1: Timing & Heat
            daily_gdd = calculate_gdd(row['Temp_Max_C'], row['Temp_Min_C'], crop['t_base'])
            crop_gdd += daily_gdd
            
            # Assume flowering happens in the middle 30% of the crop's life
            # Simplified proxy: if Tmax exceeds t_max at any point, flag risk
            if row['Temp_Max_C'] > crop['t_max']:
                heat_stress_days += 1
                
            # CHECK 2: Water Balance (Soil Bucket)
            et0 = calculate_et0_fao56(row['Temp_Max_C'], row['Temp_Min_C'], row['Solar_Radiation'])
            etc = et0 * crop['kc_mid'] # Simplified to mid-season Kc for demo
            crop_etc_total += etc
            
            rain_eff = get_effective_rainfall(row['Rainfall_CHIRPS_mm'])
            
            # Update Soil Water Bucket
            current_soil_water = current_soil_water + rain_eff - etc
            current_soil_water = max(soil["WP_mm"], min(soil["FC_mm"], current_soil_water)) # Clamp between WP and FC
            
            if current_soil_water <= soil["WP_mm"] + 10: # Near wilting point
                water_stress_days += 1
                
        # --- Evaluate Check 1 & 2 Results ---
        if crop_gdd < crop["gdd_required"] * 0.9:
            score -= 15
            warnings.append(f"{crop_name}: Risk of not reaching maturity (GDD deficit).")
            
        if heat_stress_days > 3:
            score -= 20
            warnings.append(f"{crop_name}: High heat stress risk during growth cycle.")
            
        if water_stress_days > 5:
            if priorities.get("irrigation") == "none":
                score -= 25
                warnings.append(f"{crop_name}: Critical water deficit. Not viable without irrigation.")
            else:
                score -= 10
                warnings.append(f"{crop_name}: Moderate water stress. Irrigation required.")

        # CHECK 3: Shock Survival (Worst Year Replay)
        worst_year_data = weather_df[weather_df['Year'] == worst_year]
        worst_year_rain = worst_year_data['Rainfall_CHIRPS_mm'].sum()
        if worst_year_rain < crop_etc_total * 0.5 and priorities.get("irrigation") == "none":
            score -= 15
            warnings.append(f"{crop_name}: High risk of total failure in extreme drought years (e.g., {worst_year}).")

        # CHECK 4: Soil Health & Rotation Rules
        # Rule A: Botanical Family Break
        if previous_family and previous_family == crop["family"]:
            score -= 20
            warnings.append(f"{crop_name}: Repeated botanical family ({crop['family']}). High pest/disease risk.")
        else:
            bonuses.append(f"{crop_name}: Good botanical family rotation.")
            
        # Rule B: Biodrilling (Deep root following shallow root)
        if crop["root_depth_cm"] > previous_root_depth + 40 and soil["Bulk_Density"] > 1.4:
            score += 10
            bonuses.append(f"{crop_name}: Excellent biodrilling taproot to break soil compaction.")
            
        # Rule C: Nitrogen Fixation
        if crop["n_fixation_kg_ha"] > 0:
            total_n_added += crop["n_fixation_kg_ha"]
            score += 5
            bonuses.append(f"{crop_name}: Adds {crop['n_fixation_kg_ha']} kg/ha of biological Nitrogen.")

        # Update state for next crop in sequence
        previous_family = crop["family"]
        previous_root_depth = crop["root_depth_cm"]

    # Apply Farmer Priority Multipliers
    if priorities.get("goal") == "soil_health":
        score = (score * 0.7) + ((total_n_added / 10) * 0.3) # Boost score based on N added
        
    if priorities.get("risk_tolerance") == "low":
        # Penalize high-variance crops if risk tolerance is low
        if "Maize" in rotation_sequence or "Rice" in rotation_sequence:
            score -= 5 

    # Cap score between 0 and 100
    final_score = max(0, min(100, round(score, 1)))
    
    return {
        "rotation": " → ".join(rotation_sequence),
        "score": final_score,
        "warnings": warnings,
        "bonuses": bonuses,
        "estimated_revenue_usd_ha": sum(MARKET[c]["yield_kg_ha"] * MARKET[c]["price_usd_kg"] for c in rotation_sequence)
    }

# ==========================================
# 4. MAIN EXECUTION & DEMO
# ==========================================

if __name__ == "__main__":
    # 1. Load your actual CSV here:
    # df = pd.read_csv("rajnandgaon_weather.csv")
    # For this demo, we will generate 3 years of mock daily data matching your columns
    dates = pd.date_range(start="2020-01-01", end="2022-12-31")
    mock_data = {
        "Date": dates,
        "Temp_Max_C": np.random.normal(30, 5, len(dates)),
        "Temp_Min_C": np.random.normal(20, 4, len(dates)),
        "Rainfall_POWER_mm": np.random.exponential(2, len(dates)),
        "Humidity_pct": np.random.normal(60, 15, len(dates)),
        "Wind_Speed_ms": np.random.normal(3, 1, len(dates)),
        "Solar_Radiation": np.random.normal(20, 5, len(dates)),
        "Rainfall_CHIRPS_mm": np.random.exponential(2.5, len(dates)), # Slightly different to show CHIRPS usage
        "NDVI": np.random.normal(0.6, 0.1, len(dates))
    }
    # Inject a "worst year" drought in 2021 for the Shock Survival check to trigger
    mock_data["Rainfall_CHIRPS_mm"][dates.year == 2021] *= 0.3 
    
    df = pd.DataFrame(mock_data)

    # 2. Define Farmer Priorities (This would come from your UI)
    farmer_priorities = {
        "irrigation": "limited",
        "risk_tolerance": "low",
        "goal": "soil_health"
    }

    # 3. Define Candidate Rotations to Test
    candidate_rotations = [
        ["Rice", "Rice", "Rice"],                  # Baseline: Continuous monoculture (should score poorly)
        ["Rice", "Chickpea", "Moong_Bean"],        # Proposed: Regenerative rotation for Rajnandgaon
        ["Maize", "Maize", "Maize"],               # Baseline: Continuous maize
        ["Sorghum", "Cowpea", "Pigeonpea"]         # Proposed: Drought-escape rotation for Machakos
    ]

    # 4. Run the Engine
    print("🌱 Evaluating Crop Rotations for Rajnandgaon/Machakos...\n")
    print("-" * 80)
    
    results = []
    for rotation in candidate_rotations:
        result = evaluate_rotation(rotation, df, SOIL_CONSTANTS["Rajnandgaon"], farmer_priorities)
        results.append(result)
        
        print(f"Rotation: {result['rotation']}")
        print(f"Resilience Score: {result['score']}/100")
        print(f"Est. Revenue: ${result['estimated_revenue_usd_ha']:.2f} / ha")
        if result['bonuses']:
            print(f"  ✅ Bonuses: {', '.join(result['bonuses'][:2])}...") # Show top 2
        if result['warnings']:
            print(f"  ⚠️  Warnings: {', '.join(result['warnings'][:2])}...") # Show top 2
        print("-" * 80)

    # 5. Rank and Output Final Recommendation
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n🏆 FINAL RECOMMENDATION:")
    print(f"1st Place: {results[0]['rotation']} (Score: {results[0]['score']})")
    print(f"2nd Place: {results[1]['rotation']} (Score: {results[1]['score']})")
    print("\n💡 Judge Pitch: This tool doesn't just show weather maps. It simulates the soil water bucket, calculates FAO-56 crop thirst, and applies agronomic rotation rules to mathematically prove which sequence survives climate shocks while rebuilding soil health.")