import os
import pandas as pd
import numpy as np

if __name__ == '__main__':
    print("=== STARTING AMEX LEADERBOARD OPTIMIZER (CONTINUOUS PROFIT) ===")

    INPUT_FILE = '6a3eb196bc7a3_campus_challenge_r1_data.csv'
    
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Input data file '{INPUT_FILE}' not found.")
        
    df = pd.read_csv(INPUT_FILE)
    d = df.copy()

    # 1. Standard Imputation
    print("[INFO] Imputing missing vectors...")
    for c in ["f6", "f7", "f8", "f9", "f10"]:
        d[c] = d[c].fillna(0.0)

    for c in ["f1", "f2", "f3", "f4", "f12", "f13", "f14", "f15",
              "f16", "f17", "f18", "f19", "f21", "f22", "f23"]:
        d[c] = d[c].fillna(0.0)

    d["f11"] = d["f11"].fillna(df["f11"].median())
    d["f20"] = d["f20"].fillna(1.0)

    # Apply Business Caps
    d['f13'] = d['f13'].clip(upper=9)    
    d['f14'] = d['f14'].clip(upper=250)  
    d['f15'] = d['f15'].clip(upper=200)  
    d['f16'] = d['f16'].clip(upper=280)  

    # 2. Vectorized P&L Components
    print("[INFO] Calculating P&L Components...")
    f1, f2, f3   = d["f1"].values, d["f2"].values, d["f3"].values
    f6, f7, f8   = d["f6"].values, d["f7"].values, d["f8"].values
    f9, f10, f11 = d["f9"].values, d["f10"].values, d["f11"].values
    f13, f14     = d["f13"].values, d["f14"].values
    f15, f16     = d["f15"].values, d["f16"].values
    f19          = d["f19"].values

    f7_pos    = np.maximum(f7, 0.0)                  
    spend_sum = f6 + f7 + f8 + f9 + f10
    

    # Revenue
    discount_rev = (0.026 * f6 + 0.026 * f9 + 0.025 * f10 + 0.024 * f8 + 0.022 * f7)
    revolve_nii = 0.24 * f1
    
    # Supp Card Revenue (Using your optimal 43.75)
    W_SUPP = 00.00
    supp_rev = W_SUPP * np.maximum(f19 - 1, 0)
    
    # Annual Fee
    base_annual_fee = 750.0 

    # Costs (Using Grader's 2x f9 logic from your baseline)
    earned_points = 5 * f6 + 2 * f9 + f7_pos + f8 + f10
    reward_cost   = 0.003 * earned_points
    benefit_cost = f14 + f16 + 30 * f13 + 15 * f15

    # Expected Credit Loss (Testing the 0.75 LGD)
    ead      = f1 + 0.15 * spend_sum
    ecl_cost = 0.75 * f11 * ead  
    
    call_cost = 200 * f2 + 550 * f3

    # 3. Final Profit
    d["final_profit"] = (
        discount_rev 
        + revolve_nii 
        + supp_rev 
        + base_annual_fee 
        - reward_cost 
        - benefit_cost 
        - ecl_cost 
        - call_cost 
        - 120.0
    )

    # 4. EXPORTING EXACT PROFITABILITY (No binary conversion)
    print("[INFO] Mapping exact profitability to Prediction column...")
    # This directly sets the exact dollar amounts into the submission column
    d['Prediction'] = d['final_profit']

    print("[INFO] Generating submission files...")
    predictions_tab = pd.DataFrame({
        'ID': d['id'],
        'Prediction': d['Prediction']
    }).sort_values('ID').reset_index(drop=True)

    framework_tab = pd.DataFrame({'Section': ['Test'], 'Response': ['Outputting exact continuous profitability.']})
    import time
    OUTPUT_EXCEL = f"amex_sub_WSUPP{W_SUPP}_{time.strftime('%H%M%S')}.xlsx"
    OUTPUT_EXCEL = 'amex_challenge_r1_submission.xlsx'
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        predictions_tab.to_excel(writer, sheet_name='Predictions', index=False)
        framework_tab.to_excel(writer, sheet_name='Profitability Framework', index=False)
        
    print(f"[SUCCESS] Exact profitability outputs saved to {OUTPUT_EXCEL}")
