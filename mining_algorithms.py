"""
=============================================================
FILE: mining_algorithms.py
MỤC ĐÍCH: Chứa 2 thuật toán khai phá dữ liệu chính
  1. K-Means Clustering   → Phân cụm địa điểm theo độ phổ biến
  2. FP-Growth            → Khai phá luật kết hợp hành vi du khách
=============================================================
"""

import pandas as pd
from sklearn.cluster import KMeans
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules

# --- SỬA LỖI TƯƠNG THÍCH ---
# mlxtend cũ dùng df.append() đã bị xóa ở Pandas 3.0+
# Đoạn này "vá" lại hàm append để mlxtend hoạt động bình thường
if not hasattr(pd.DataFrame, 'append'):
    def _df_append(self, other, ignore_index=False, **kwargs):
        if isinstance(other, dict):
            other = pd.DataFrame([other])
        elif isinstance(other, pd.Series):
            other = other.to_frame().T
        return pd.concat([self, other], ignore_index=ignore_index)
    pd.DataFrame.append = _df_append


# ===========================================================
# THUẬT TOÁN 1: K-MEANS CLUSTERING
# ===========================================================
def apply_kmeans_clustering(df):
    """
    MỤC ĐÍCH: Phân loại 30 địa điểm thành 3 nhóm dựa trên:
      - Tổng lượt ghé thăm (Total_Visits)
      - Điểm đánh giá trung bình (Avg_Rating)

    LÝ THUYẾT K-MEANS:
    ==================
    Ý tưởng: Nhóm các điểm dữ liệu gần nhau thành cụm (cluster).
    
    Các bước thuật toán:
      B1. Chọn ngẫu nhiên K=3 điểm làm "tâm cụm" ban đầu
      B2. Gán mỗi địa điểm vào cụm có tâm gần nhất (theo khoảng cách Euclidean)
      B3. Tính lại tâm cụm mới = trung bình các điểm trong cụm
      B4. Lặp lại B2-B3 cho đến khi tâm cụm không đổi nữa
    
    Kết quả: 3 nhóm địa điểm
      🔴 Địa điểm Hot        → lượt ghé thăm CAO nhất
      🟡 Địa điểm Bình thường → lượt ghé thăm TRUNG BÌNH  
      🔵 Địa điểm Ngách      → lượt ghé thăm THẤP (ít người biết)
    
    Tại sao cần bước này cho FP-Growth?
    → FP-Growth cần dữ liệu PHÂN LOẠI (categorical).
      "Sacred Monkey Forest: 5000 lượt" không thể đưa vào FP-Growth,
      nhưng "Sacred Monkey Forest: Địa điểm Hot" thì được.
    """
    if df is None or df.empty:
        return df

    required = {'Attraction', 'UserId', 'Rating'}
    if not required.issubset(df.columns):
        print(f"[LỖI] K-Means thiếu cột: {required - set(df.columns)}")
        return df

    # Bước 1: Tính thống kê cho từng địa điểm
    location_stats = df.groupby('Attraction').agg(
        Total_Visits=('UserId', 'count'),    # Đếm số lượt thăm
        Avg_Rating=('Rating', 'mean')        # Tính điểm TB
    ).reset_index()

    # Bước 2: Chạy K-Means với K=3 cụm
    # n_init=10: thử 10 lần khởi tạo ngẫu nhiên, lấy kết quả tốt nhất
    # random_state=42: cố định kết quả để tái lập được (reproducible)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    location_stats['Cluster'] = kmeans.fit_predict(
        location_stats[['Total_Visits', 'Avg_Rating']]
    )

    # Bước 3: Gán nhãn ý nghĩa dựa trên lượt ghé thăm trung bình của từng cụm
    # (K-Means tự đặt số 0/1/2, ta cần biết cụm nào là "Hot")
    cluster_visit_mean = location_stats.groupby('Cluster')['Total_Visits'].mean().sort_values()
    label_map = {
        cluster_visit_mean.index[2]: '🔴 Địa điểm Hot',
        cluster_visit_mean.index[1]: '🟡 Địa điểm Bình thường',
        cluster_visit_mean.index[0]: '🔵 Địa điểm Ngách',
    }
    location_stats['Attraction_Hotness'] = location_stats['Cluster'].map(label_map)

    # Bước 4: Gộp nhãn vừa tạo vào bảng chính
    df_result = df.merge(
        location_stats[['Attraction', 'Attraction_Hotness', 'Total_Visits', 'Avg_Rating']],
        on='Attraction',
        how='left'
    )
    return df_result


def get_cluster_summary(df):
    """
    TRẢ VỀ BẢNG TỔNG KẾT K-MEANS để hiển thị biểu đồ
    Mỗi dòng = 1 địa điểm + số lượt thăm + điểm TB + nhãn cụm
    """
    if df is None or 'Attraction_Hotness' not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby(['Attraction', 'Attraction_Hotness'])
        .agg(Total_Visits=('UserId', 'count'), Avg_Rating=('Rating', 'mean'))
        .reset_index()
        .sort_values('Total_Visits', ascending=False)
    )


# ===========================================================
# THUẬT TOÁN 2: FP-GROWTH (Association Rules Mining)
# ===========================================================
def mine_association_rules(df, min_supp=0.05, min_conf=0.6):
    """
    MỤC ĐÍCH: Tìm "luật kết hợp" — các mẫu hành vi thường xuyên xảy ra cùng nhau.
    Ví dụ: "Khách đi Cặp đôi + đến Địa điểm Hot → thường đánh giá Xuất sắc"

    LÝ THUYẾT FP-GROWTH:
    ====================
    Bài toán: Tìm tập mục (itemsets) xuất hiện thường xuyên trong tất cả giao dịch.
    
    Các khái niệm chính:
    
    ① Support (Độ hỗ trợ):
       = Tần suất một luật xuất hiện trong toàn bộ dữ liệu
       Support({A → B}) = số giao dịch chứa cả A và B / tổng giao dịch
       Ý nghĩa: Luật này PHỔ BIẾN đến mức nào?
       Ngưỡng min_support: Lọc bỏ các tập quá hiếm gặp
    
    ② Confidence (Độ tin cậy):
       = Xác suất có B khi đã biết có A
       Confidence({A → B}) = Support(A ∪ B) / Support(A)
       Ý nghĩa: Luật này ĐÁNG TIN CẬY đến mức nào?
       Ngưỡng min_confidence: Lọc bỏ các luật yếu
    
    ③ Lift (Độ nâng):
       = Confidence(A→B) / Support(B)
       Ý nghĩa: So sánh với trường hợp ngẫu nhiên
         Lift > 1: A và B có mối quan hệ DƯƠNG (xuất hiện cùng nhau nhiều hơn ngẫu nhiên)
         Lift = 1: Độc lập, không có mối quan hệ
         Lift < 1: Mối quan hệ ÂM (loại trừ nhau)
    
    Tại sao FP-Growth thay vì Apriori?
       - Apriori: Tạo và kiểm tra TẤT CẢ tập ứng viên → Rất chậm
       - FP-Growth: Nén dữ liệu vào cây FP-Tree → Nhanh hơn nhiều lần
         Không cần duyệt lại database, chỉ duyệt cây 2 lần
    
    CÁCH HIỂU "GIAO DỊCH" TRONG BÀI NÀY:
    =====================================
    Mỗi "giao dịch" = tập hợp tất cả đặc trưng của 1 UserId.
    
    Ví dụ UserId 12345 đã ghé thăm nhiều nơi:
    Giao dịch 12345 = {
        "Cặp đôi",              ← TravelMode
        "Beaches",              ← Type
        "Xuất sắc",             ← Rating_Level
        "🟡 Địa điểm Bình thường" ← Attraction_Hotness
    }
    
    FP-Growth sẽ tìm những tổ hợp {A, B, C} 
    xuất hiện cùng nhau trong NHIỀU UserId.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    features_to_mine = ['TravelMode', 'Type', 'Rating_Level', 'Attraction_Hotness']

    # Kiểm tra đủ cột không
    missing = [f for f in features_to_mine if f not in df.columns]
    if missing:
        print(f"[LỖI] FP-Growth thiếu cột: {missing}")
        return pd.DataFrame()

    # BƯỚC 1: Tạo danh sách "giao dịch"
    # Mỗi user = 1 "giỏ hàng" chứa tất cả đặc trưng của họ
    # set() loại bỏ trùng lặp trong cùng 1 user
    transactions = (
        df.groupby('UserId')[features_to_mine]
        .apply(lambda x: list(set(x.values.ravel())))
        .tolist()
    )

    # BƯỚC 2: Mã hóa One-Hot (TransactionEncoder)
    # Chuyển danh sách → ma trận True/False
    # Ví dụ: ["Cặp đôi", "Beaches"] → [True, False, True, ...]
    te = TransactionEncoder()
    te_array = te.fit(transactions).transform(transactions)
    df_encoded = pd.DataFrame(te_array, columns=te.columns_)

    # BƯỚC 3: Tìm Frequent Itemsets bằng FP-Growth
    frequent_itemsets = fpgrowth(
        df_encoded,
        min_support=min_supp,   # Chỉ giữ tập xuất hiện >= min_supp
        use_colnames=True       # Dùng tên cột thay vì chỉ số
    )

    if frequent_itemsets.empty:
        return pd.DataFrame()

    # BƯỚC 4: Sinh luật kết hợp từ Frequent Itemsets
    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=min_conf  # Chỉ giữ luật có confidence >= min_conf
    )

    if rules.empty:
        return pd.DataFrame()

    # BƯỚC 5: Lọc và sắp xếp
    rules = rules[rules['lift'] > 1.0]                                       # Chỉ giữ luật có ý nghĩa thực sự
    rules = rules.sort_values(['lift', 'confidence'], ascending=[False, False])  # Ưu tiên lift cao nhất

    # Chuyển frozenset → chuỗi để hiển thị
    rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(sorted(x)))
    rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(sorted(x)))

    return rules