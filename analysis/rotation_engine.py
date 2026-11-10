"""
rotation_engine.py
Core decision-support engine comparing baseline monoculture vs. adaptive crop rotations
based on NASA satellite indicators, local soil profiles, and crop traits.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent


def get_soil_baseline(region_key):
    """
    Returns baseline soil indicators derived from SoilGrids 2.0 profiles.
    """
    if region_key == "rajnandgaon":
        return {
            "Soil Type": "Clay Loam / Red-Yellow (Inceptisols/Vertisols)",
            "Organic Carbon": "0.48% (Low to Medium)",
            "pH": "6.2 (Slightly Acidic)",
            "Key Vulnerability": "Post-monsoon surface crusting, high evaporation during Zaid.",
        }
    else:  # machakos
        return {
            "Soil Type": "Sandy Clay Loam (Ferralsols/Luvisols)",
            "Organic Carbon": "0.35% (Critically Low)",
            "pH": "5.8 (Acidic)",
            "Key Vulnerability": "Severe topsoil wash-off during storm downpours, low moisture retention.",
        }


def generate_strategies(region_key):
    """
    Generates 3-way rotation comparison required by the 2026 NASA Space Apps Challenge.
    """
    if region_key == "rajnandgaon":
        return [
            {
                "Strategy ID": "Strategy 1: Baseline (Monoculture)",
                "Rotation Pattern": "Paddy (Kharif) ➔ Fallow (Rabi) ➔ Bare Soil (Zaid)",
                "Ground Cover Window": "July to November (~4.5 months green cover)",
                "Soil Health Impact": "Severe nutrient depletion; zero residue returned; summer topsoil erosion.",
                "Water Resilience Score": "Low (100% dependent on monsoon rainfall / tube-well pumping).",
                "Economic/Farmer Benefit": "Familiar cereal harvest, but increasing fertilizer input costs yearly.",
            },
            {
                "Strategy ID": "Strategy 2: Soil Health & Nitrogen Fixation",
                "Rotation Pattern": "Paddy (Kharif) ➔ Chickpea / Lathyrus (Rabi) ➔ Dhaincha (Green Manure)",
                "Ground Cover Window": "July to May (~10 months continuous cover)",
                "Soil Health Impact": "Fixes 65–85 kg/ha biological nitrogen; restores organic carbon; breaks weed cycles.",
                "Water Resilience Score": "Medium-High (Utilizes residual soil moisture post-monsoon without extra pumping).",
                "Economic/Farmer Benefit": "Reduces synthetic urea/DAP expenses by ~30% for subsequent paddy crops.",
            },
            {
                "Strategy ID": "Strategy 3: Climate & Water Conservation",
                "Rotation Pattern": "Kodo Millet / Ragi (Kharif) ➔ Mustard (Rabi) ➔ Summer Moong",
                "Ground Cover Window": "June to April (~9.5 months diversified cover)",
                "Soil Health Impact": "Fibrous root systems break compaction; minimal nutrient leaching.",
                "Water Resilience Score": "Highest (Cuts total farm water footprint by 45% during drought years).",
                "Economic/Farmer Benefit": "High market demand for millets and pulses; shields farmer from monsoon delays.",
            },
        ]
    else:  # machakos
        return [
            {
                "Strategy ID": "Strategy 1: Baseline (Monoculture)",
                "Rotation Pattern": "Maize (Long Rains) ➔ Fallow ➔ Maize (Short Rains)",
                "Ground Cover Window": "April-June & Nov-Dec (~5 months cover)",
                "Soil Health Impact": "Progressive nitrogen exhaustion; heavy surface runoff under intense rain.",
                "Water Resilience Score": "Low (Maize wilts rapidly during mid-season dry spells).",
                "Economic/Farmer Benefit": "Primary staple food, but high risk of catastrophic seasonal failure.",
            },
            {
                "Strategy ID": "Strategy 2: Soil Health & Nitrogen Fixation",
                "Rotation Pattern": "Maize + Pigeonpea (Intercrop) ➔ Cowpea / Lablab Cover",
                "Ground Cover Window": "March to January (~10 months protective cover)",
                "Soil Health Impact": "Prevents soil crusting; deep roots capture subsoil nutrients; nitrogen fixing.",
                "Water Resilience Score": "Medium (Pigeonpea continues growing through dry months).",
                "Economic/Farmer Benefit": "Dual yield: human edible grain + nutrient-dense livestock forage.",
            },
            {
                "Strategy ID": "Strategy 3: Climate & Water Conservation",
                "Rotation Pattern": "Sorghum (Long Rains) ➔ Green Gram (Short Rains) ➔ Drought Grass",
                "Ground Cover Window": "March to December (~9 months cover)",
                "Soil Health Impact": "High biomass recycling; maximum topsoil protection against wind/sun.",
                "Water Resilience Score": "Highest (Exceptional drought tolerance under high land surface temperatures).",
                "Economic/Farmer Benefit": "Guaranteed harvest in semi-arid zones; marketable cash legumes.",
            },
        ]


def get_strategies_dataframe(region_key):
    return pd.DataFrame(generate_strategies(region_key))


if __name__ == "__main__":
    for reg in ["rajnandgaon", "machakos"]:
        print(f"\n{'='*30} {reg.upper()} STRATEGY MATRIX {'='*30}")
        df = get_strategies_dataframe(reg)
        print(df.to_string(index=False))