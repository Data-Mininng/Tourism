import pandas as pd
import os
import warnings
from sklearn.cluster import KMeans
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules

# TỐI ƯU: Ngăn cảnh báo Memory Leak của KMeans trên Windows
os.environ["OMP_NUM_THREADS"] = "1"
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Vá lỗi append của Pandas 3.0+ cho thư viện mlxtend cũ
if not hasattr(pd.DataFrame, 'append'):
    def _df_append(self, other, ignore_index=False, **kwargs):
        if isinstance(other, dict):
            other = pd.DataFrame([other])
        elif isinstance(other, pd.Series):
            other = other.to_frame().T
        # Tối ưu: Lọc các phần tử rỗng để tránh Warning của pd.concat
        dfs_to_concat = [df for df in [self, other] if not df.empty]
        if not dfs_to_concat:
            return pd.DataFrame()
        return pd.concat(dfs_to_concat, ignore_index=ignore_index)
    pd.DataFrame.append = _df_append

def apply_kmeans_clustering(df):
    if df is None or df.empty:
        return df

    required = {'Attraction', 'UserId', 'Rating'}
    if not required.issubset(df.columns):
        print(f"[LỖI] K-Means thiếu cột: {required - set(df.columns)}")
        return df

    location_stats = df.groupby('Attraction').agg(
        Total_Visits=('UserId', 'count'),
        Avg_Rating=('Rating', 'mean')
    ).reset_index()

    # Chạy K-Means
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    location_stats['Cluster'] = kmeans.fit_predict(
        location_stats[['Total_Visits', 'Avg_Rating']]
    )

    cluster_visit_mean = location_stats.groupby('Cluster')['Total_Visits'].mean().sort_values()
    
    # TỐI ƯU: Sử dụng map an toàn hơn, đề phòng cluster_visit_mean không có đủ 3 cụm
    if len(cluster_visit_mean) == 3:
        label_map = {
            cluster_visit_mean.index[2]: '🔴 Địa điểm Hot',
            cluster_visit_mean.index[1]: '🟡 Địa điểm Bình thường',
            cluster_visit_mean.index[0]: '🔵 Địa điểm Ngách',
        }
    else:
        # Fallback nếu dữ liệu quá ít không chia đủ 3 cụm
        label_map = {idx: f"Cụm {idx}" for idx in cluster_visit_mean.index}

    location_stats['Attraction_Hotness'] = location_stats['Cluster'].map(label_map)

    df_result = df.merge(
        location_stats[['Attraction', 'Attraction_Hotness', 'Total_Visits', 'Avg_Rating']],
        on='Attraction',
        how='left'
    )
    return df_result

def get_cluster_summary(df):
    if df is None or df.empty or 'Attraction_Hotness' not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby(['Attraction', 'Attraction_Hotness'])
        .agg(Total_Visits=('UserId', 'count'), Avg_Rating=('Rating', 'mean'))
        .reset_index()
        .sort_values('Total_Visits', ascending=False)
    )

def mine_association_rules(df, min_supp=0.05, min_conf=0.6):
    if df is None or df.empty:
        return pd.DataFrame()

    features_to_mine = ['TravelMode', 'Type', 'Rating_Level', 'Attraction_Hotness']
    missing = [f for f in features_to_mine if f not in df.columns]
    if missing:
        return pd.DataFrame()

    transactions = (
        df.groupby('UserId')[features_to_mine]
        .apply(lambda x: list(set(x.values.ravel())))
        .tolist()
    )

    # TỐI ƯU: Kiểm tra list rỗng trước khi đưa vào mã hóa
    if not transactions:
        return pd.DataFrame()

    te = TransactionEncoder()
    te_array = te.fit(transactions).transform(transactions)
    df_encoded = pd.DataFrame(te_array, columns=te.columns_)

    # FP-Growth
    try:
        frequent_itemsets = fpgrowth(
            df_encoded,
            min_support=min_supp,
            use_colnames=True
        )
    except Exception as e:
        print(f"[LỖI] FP-Growth: {e}")
        return pd.DataFrame()

    if frequent_itemsets.empty:
        return pd.DataFrame()

    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=min_conf
    )

    if rules.empty:
        return pd.DataFrame()

    rules = rules[rules['lift'] > 1.0].copy() # Tối ưu: Dùng .copy() để tránh cảnh báo SettingWithCopyWarning
    rules = rules.sort_values(['lift', 'confidence'], ascending=[False, False])

    rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(sorted(x)))
    rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(sorted(x)))

    return rules