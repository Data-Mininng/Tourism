import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules

def run_fpgrowth(df: pd.DataFrame, min_sup: float, min_conf: float) -> pd.DataFrame:
    """Nhận DataFrame data đầu vào, trả về DataFrame luật đầu ra"""
    
    if df.empty:
        raise ValueError("Bảng dữ liệu đang trống!")

    df_bool = df.astype(bool)

    # Chạy thuật toán
    frequent_itemsets = fpgrowth(df_bool, min_support=min_sup, use_colnames=True)
    if frequent_itemsets.empty:
        raise ValueError(f"Không tìm thấy tập phổ biến nào với support >= {min_sup}")

    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_conf)

    # Làm sạch luật 1-1
    rules['antecedents'] = rules['antecedents'].apply(lambda x: list(x)[0] if len(x) == 1 else None)
    rules['consequents'] = rules['consequents'].apply(lambda x: list(x)[0] if len(x) == 1 else None)
    rules = rules.dropna(subset=['antecedents', 'consequents'])
    
    rules_db = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
    rules_db.columns = ['DichVu_Goc', 'DichVu_GoiY', 'Do_Ho_Tro', 'Do_Tin_Cay_Confidence', 'Chi_So_Lift']
    rules_db = rules_db.sort_values(by='Do_Tin_Cay_Confidence', ascending=False)

    return rules_db