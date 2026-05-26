"""
=============================================================
FILE: app.py  (Giao diện chính - Streamlit Web App)
MỤC ĐÍCH: Hiển thị kết quả khai phá dữ liệu dưới dạng trực quan
CHẠY: streamlit run app.py
=============================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from mining_algorithms import apply_kmeans_clustering, mine_association_rules, get_cluster_summary

# ============================================================
# CẤU HÌNH TRANG
# ============================================================
st.set_page_config(
    page_title="Khai Phá Dữ Liệu Du Lịch",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh giao diện
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #0f3460;
    }
    .theory-box {
        background: #1e3a5f;
        border-left: 4px solid #4fc3f7;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        color: #e0f0ff !important;
    }
    .theory-box b { color: #7dd3fc !important; }
    .theory-box i { color: #bae6fd !important; }
    .rule-card {
        background: #1a3a2a;
        border: 1px solid #4ade80;
        padding: 1.2rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: #d1fae5 !important;
    }
    .rule-card h4 { color: #d1fae5 !important; margin: 0.3rem 0; }
    .rule-card b  { color: #86efac !important; }
    .rule-card span { font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HÀM TẢI DỮ LIỆU (có cache để không load lại mỗi lần)
# @st.cache_data: Lưu kết quả vào bộ nhớ đệm
#   → Chỉ chạy lại khi file CSV thay đổi, giúp app nhanh hơn nhiều
# ============================================================
@st.cache_data
def load_data():
    """Đọc file đã làm sạch và áp dụng K-Means"""
    try:
        df = pd.read_csv("DuLieu_DaLamSach_TiengViet.csv", encoding='utf-8-sig')
        df = apply_kmeans_clustering(df)
        return df
    except FileNotFoundError:
        st.error("❌ Không tìm thấy file 'DuLieu_DaLamSach_TiengViet.csv'!")
        st.info("💡 Hãy chạy file chuan_bi_du_lieu.py trước để tạo file này.")
        return None


# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="main-header">
    <h1>🗺️ HỆ THỐNG KHAI PHÁ DỮ LIỆU DU LỊCH INDONESIA</h1>
    <p>Đồ án môn Khai Phá Dữ Liệu | Thuật toán: <strong>K-Means Clustering</strong> & <strong>FP-Growth Association Rules</strong></p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR: HƯỚNG DẪN & THÔNG SỐ
# ============================================================
with st.sidebar:
    st.header("⚙️ Bảng Điều Khiển")

    st.markdown("### 📖 Hướng dẫn sử dụng")
    st.markdown("""
    1. **Tab 1**: Xem tổng quan dữ liệu
    2. **Tab 2**: Kết quả K-Means Clustering
    3. **Tab 3**: Khai phá luật FP-Growth
    4. **Tab 4**: Giải thích lý thuyết
    """)

    st.divider()

    st.markdown("### 🔧 Tham số FP-Growth")
    min_supp = st.slider(
        "Min Support (Độ hỗ trợ tối thiểu)",
        min_value=0.01, max_value=0.20,
        value=0.05, step=0.01,
        help="Tần suất tối thiểu để 1 tập mục được coi là 'phổ biến'. Giảm xuống để tìm thêm luật."
    )
    min_conf = st.slider(
        "Min Confidence (Độ tin cậy tối thiểu)",
        min_value=0.10, max_value=1.00,
        value=0.60, step=0.05,
        help="Xác suất tối thiểu của luật. Tăng lên để chỉ giữ luật đáng tin cậy nhất."
    )

    st.divider()
    st.caption("📊 Dữ liệu: 30 địa điểm tham quan Indonesia | ~52,930 lượt đánh giá")


# ============================================================
# TẢI DỮ LIỆU
# ============================================================
with st.spinner("⏳ Đang tải dữ liệu và chạy K-Means..."):
    df = load_data()

if df is None:
    st.stop()

# Tính toán trước để dùng cho nhiều tab
cluster_df = get_cluster_summary(df)

# ============================================================
# 4 TAB CHÍNH
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Tổng quan Dữ liệu",
    "🔵 K-Means Clustering",
    "📏 FP-Growth Luật Kết Hợp",
    "📚 Lý Thuyết Thuật Toán"
])


# ============================================================
# TAB 1: TỔNG QUAN DỮ LIỆU
# ============================================================
with tab1:
    st.header("📊 Tổng Quan Dữ Liệu Sau Tích Hợp")

    # Thống kê nhanh
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng giao dịch", f"{df.shape[0]:,}")
    col2.metric("Địa điểm tham quan", df['Attraction'].nunique())
    col3.metric("Loại hình du lịch", df['TravelMode'].nunique())
    col4.metric("Rating trung bình", f"{df['Rating'].mean():.2f} ⭐")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        # Biểu đồ phân phối hình thức đi
        fig_mode = px.pie(
            df['TravelMode'].value_counts().reset_index(),
            values='count', names='TravelMode',
            title="🧳 Phân bố Hình thức Du lịch",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_mode.update_layout(height=350)
        st.plotly_chart(fig_mode, use_container_width=True)

    with col_right:
        # Biểu đồ phân phối mức đánh giá
        rating_order = ['Xuất sắc', 'Tốt', 'Trung bình']
        rating_counts = df['Rating_Level'].value_counts().reindex(rating_order)
        fig_rating = px.bar(
            x=rating_counts.index, y=rating_counts.values,
            labels={'x': 'Mức đánh giá', 'y': 'Số lượng'},
            title="⭐ Phân bố Mức Đánh Giá",
            color=rating_counts.index,
            color_discrete_map={
                'Xuất sắc': '#2ecc71',
                'Tốt': '#f39c12',
                'Trung bình': '#e74c3c'
            }
        )
        fig_rating.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_rating, use_container_width=True)

    # Biểu đồ Top địa điểm được ghé thăm nhiều nhất
    top_attractions = df['Attraction'].value_counts().head(10).reset_index()
    top_attractions.columns = ['Địa điểm', 'Lượt thăm']
    fig_top = px.bar(
        top_attractions, x='Lượt thăm', y='Địa điểm',
        orientation='h', title="🏆 Top 10 Địa Điểm Được Ghé Thăm Nhiều Nhất",
        color='Lượt thăm', color_continuous_scale='Blues'
    )
    fig_top.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_top, use_container_width=True)

    # Biểu đồ phân bố loại hình địa điểm
    fig_type = px.bar(
        df['Type'].value_counts().reset_index(),
        x='count', y='Type', orientation='h',
        title="🗂️ Phân bố Loại Hình Địa Điểm",
        color='count', color_continuous_scale='Teal'
    )
    fig_type.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_type, use_container_width=True)

    st.subheader("🔍 Xem dữ liệu chi tiết")
    st.dataframe(df[['UserId','TravelMode','Attraction','Type','Rating_Level','Attraction_Hotness']].head(20),
                 use_container_width=True)


# ============================================================
# TAB 2: K-MEANS CLUSTERING
# ============================================================
with tab2:
    st.header("🔵 Kết Quả Phân Cụm K-Means")

    st.markdown("""
    <div class="theory-box">
    <b>💡 K-Means làm gì ở đây?</b><br>
    Phân loại 30 địa điểm thành 3 nhóm dựa trên <b>lượt ghé thăm</b> và <b>điểm đánh giá trung bình</b>.
    Nhãn cụm (<i>Hot / Bình thường / Ngách</i>) sau đó được dùng làm đặc trưng đầu vào cho FP-Growth.
    </div>
    """, unsafe_allow_html=True)

    if not cluster_df.empty:
        # Thống kê theo cụm
        col1, col2, col3 = st.columns(3)
        hot = cluster_df[cluster_df['Attraction_Hotness'].str.contains('Hot')]
        normal = cluster_df[cluster_df['Attraction_Hotness'].str.contains('Bình thường')]
        niche = cluster_df[cluster_df['Attraction_Hotness'].str.contains('Ngách')]

        col1.metric("🔴 Địa điểm Hot", f"{len(hot)} địa điểm",
                    f"TB {hot['Total_Visits'].mean():.0f} lượt/địa điểm")
        col2.metric("🟡 Địa điểm Bình thường", f"{len(normal)} địa điểm",
                    f"TB {normal['Total_Visits'].mean():.0f} lượt/địa điểm")
        col3.metric("🔵 Địa điểm Ngách", f"{len(niche)} địa điểm",
                    f"TB {niche['Total_Visits'].mean():.0f} lượt/địa điểm")

        st.divider()
        col_l, col_r = st.columns([3, 2])

        with col_l:
            # Scatter plot K-Means
            color_map = {
                '🔴 Địa điểm Hot': '#e74c3c',
                '🟡 Địa điểm Bình thường': '#f39c12',
                '🔵 Địa điểm Ngách': '#3498db'
            }
            fig_kmeans = px.scatter(
                cluster_df,
                x='Total_Visits', y='Avg_Rating',
                color='Attraction_Hotness',
                text='Attraction',
                color_discrete_map=color_map,
                title="📍 Biểu Đồ Phân Cụm K-Means (K=3)",
                labels={'Total_Visits': 'Tổng Lượt Ghé Thăm', 'Avg_Rating': 'Điểm Đánh Giá TB'}
            )
            fig_kmeans.update_traces(
                textposition='top center',
                marker=dict(size=12, line=dict(width=1, color='white'))
            )
            fig_kmeans.update_layout(height=500)
            st.plotly_chart(fig_kmeans, use_container_width=True)

        with col_r:
            # Bảng chi tiết
            st.subheader("📋 Chi tiết từng địa điểm")
            display_df = cluster_df[['Attraction', 'Total_Visits', 'Avg_Rating', 'Attraction_Hotness']].copy()
            display_df.columns = ['Địa điểm', 'Lượt thăm', 'Rating TB', 'Phân loại']
            display_df['Rating TB'] = display_df['Rating TB'].round(2)
            st.dataframe(display_df, use_container_width=True, height=480)

        # Biểu đồ bar theo cụm
        fig_bar = px.bar(
            cluster_df.sort_values('Total_Visits', ascending=False),
            x='Attraction', y='Total_Visits',
            color='Attraction_Hotness',
            color_discrete_map=color_map,
            title="📊 Lượt Ghé Thăm Theo Địa Điểm (màu = cụm K-Means)",
            labels={'Attraction': 'Địa điểm', 'Total_Visits': 'Lượt thăm'}
        )
        fig_bar.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)


# ============================================================
# TAB 3: FP-GROWTH LUẬT KẾT HỢP
# ============================================================
with tab3:
    st.header("📏 Khai Phá Luật Kết Hợp bằng FP-Growth")

    st.markdown("""
    <div class="theory-box">
    <b>💡 FP-Growth tìm gì?</b><br>
    Tìm các <b>mẫu hành vi</b> thường xuất hiện cùng nhau.
    Ví dụ: <i>"Khách đi Cặp đôi thường chọn Địa điểm Hot và đánh giá Xuất sắc"</i>.
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Bắt đầu Khai phá Luật Kết Hợp", type="primary", use_container_width=True):
        with st.spinner("⏳ Đang chạy FP-Growth... (có thể mất 10-30 giây)"):
            rules = mine_association_rules(df, min_supp=min_supp, min_conf=min_conf)

        if rules is None or rules.empty:
            st.warning("⚠️ Không tìm thấy luật nào. Hãy **giảm Min Support** hoặc **giảm Min Confidence** ở thanh bên trái.")
        else:
            st.success(f"✅ Tìm thấy **{len(rules)}** luật kết hợp có ý nghĩa (Lift > 1)!")

            # --- TOP 1 LUẬT ---
            st.subheader("🏆 Luật Tiêu Biểu Nhất")
            top = rules.iloc[0]
            st.markdown(f"""
            <div class="rule-card">
            <h4 style="color:#d1fae5">Nếu du khách có đặc điểm:
                <span style="color:#67e8f9;font-weight:bold">[{top['antecedents']}]</span>
            </h4>
            <h4 style="color:#d1fae5">👉 Thì có thể suy ra:
                <span style="color:#86efac;font-weight:bold">[{top['consequents']}]</span>
            </h4>
            <br>
            <span style="color:#86efac;font-weight:bold">📊 Chỉ số đánh giá luật:</span><br>
            <span style="color:#d1fae5">
            • <b style="color:#4ade80">Support = {top['support']:.1%}</b>
              → {top['support']:.1%} tổng giao dịch chứa cả 2 vế<br>
            • <b style="color:#4ade80">Confidence = {top['confidence']:.1%}</b>
              → Khi có vế trái, xác suất <b>{top['confidence']:.1%}</b> có vế phải<br>
            • <b style="color:#4ade80">Lift = {top['lift']:.2f}</b>
              → Cao hơn {top['lift']:.2f}x so với trường hợp ngẫu nhiên ✅
            </span>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            col_l, col_r = st.columns([2, 1])

            with col_l:
                # Biểu đồ Scatter Support vs Confidence
                fig_rules = px.scatter(
                    rules.head(50),
                    x='support', y='confidence',
                    size='lift', color='lift',
                    hover_data=['antecedents', 'consequents'],
                    color_continuous_scale='RdYlGn',
                    title="📈 Biểu đồ Support vs Confidence (kích thước = Lift)",
                    labels={'support': 'Support', 'confidence': 'Confidence', 'lift': 'Lift'}
                )
                fig_rules.update_layout(height=400)
                st.plotly_chart(fig_rules, use_container_width=True)

            with col_r:
                # Top 10 luật có Lift cao nhất
                st.subheader("🔝 Top 10 Luật (theo Lift)")
                top10 = rules[['antecedents', 'consequents', 'confidence', 'lift']].head(10).copy()
                top10['confidence'] = top10['confidence'].apply(lambda x: f"{x:.0%}")
                top10['lift'] = top10['lift'].apply(lambda x: f"{x:.2f}")
                top10.columns = ['Nếu (Antecedents)', 'Thì (Consequents)', 'Tin cậy', 'Lift']
                st.dataframe(top10, use_container_width=True, height=370)

            # Biểu đồ Lift phân phối
            fig_lift = px.histogram(
                rules, x='lift', nbins=30,
                title="📊 Phân phối Lift của toàn bộ luật tìm được",
                labels={'lift': 'Lift', 'count': 'Số luật'},
                color_discrete_sequence=['#3498db']
            )
            fig_lift.add_vline(x=1.0, line_dash="dash", line_color="red",
                               annotation_text="Lift=1 (Ngẫu nhiên)")
            fig_lift.update_layout(height=300)
            st.plotly_chart(fig_lift, use_container_width=True)

            st.subheader("📋 Toàn bộ luật tìm được")
            display_rules = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
            display_rules.columns = ['Nếu (Antecedents)', 'Thì (Consequents)', 'Support', 'Confidence', 'Lift']
            display_rules['Support'] = display_rules['Support'].apply(lambda x: f"{x:.1%}")
            display_rules['Confidence'] = display_rules['Confidence'].apply(lambda x: f"{x:.1%}")
            display_rules['Lift'] = display_rules['Lift'].apply(lambda x: f"{x:.2f}")
            st.dataframe(display_rules, use_container_width=True)
    else:
        st.info("👆 Điều chỉnh tham số ở thanh bên trái rồi nhấn nút để bắt đầu khai phá.")


# ============================================================
# TAB 4: LÝ THUYẾT THUẬT TOÁN
# ============================================================
with tab4:
    st.header("📚 Lý Thuyết Thuật Toán")

    with st.expander("🔵 K-Means Clustering — Chi tiết", expanded=True):
        st.markdown("""
        ### Mục đích trong bài
        Phân nhóm 30 địa điểm thành 3 cụm để tạo nhãn **"Độ Hot"** — đặc trưng đầu vào cho FP-Growth.
        
        ### Các bước thuật toán
        | Bước | Mô tả |
        |------|-------|
        | B1 | Chọn K=3 tâm cụm ngẫu nhiên |
        | B2 | Gán mỗi điểm vào cụm có tâm **gần nhất** (khoảng cách Euclidean) |
        | B3 | Tính lại tâm cụm = **trung bình** các điểm trong cụm |
        | B4 | Lặp B2-B3 cho đến khi tâm không thay đổi |
        
        ### Đặc trưng đầu vào
        - **Total_Visits**: Tổng số lượt ghé thăm của mỗi địa điểm
        - **Avg_Rating**: Điểm đánh giá trung bình của mỗi địa điểm
        
        ### Kết quả 3 cụm
        - 🔴 **Địa điểm Hot**: Lượt thăm rất cao → Địa điểm nổi tiếng
        - 🟡 **Địa điểm Bình thường**: Lượt thăm trung bình → Địa điểm đại trà
        - 🔵 **Địa điểm Ngách**: Lượt thăm thấp → Ít người biết, có thể là "hidden gem"
        
        ### Tham số quan trọng
        - `n_clusters=3`: Số cụm mong muốn
        - `random_state=42`: Cố định kết quả để tái lập (reproducibility)
        - `n_init=10`: Chạy 10 lần, lấy kết quả tốt nhất
        """)

    with st.expander("📏 FP-Growth Association Rules — Chi tiết"):
        st.markdown("""
        ### Mục đích trong bài
        Tìm các **mẫu hành vi du lịch** phổ biến: hình thức đi, loại địa điểm, mức đánh giá thường đi kèm nhau.
        
        ### 3 chỉ số quan trọng
        
        **① Support (Độ hỗ trợ)**
        ```
        Support(A → B) = Số giao dịch chứa cả A và B / Tổng giao dịch
        ```
        → Đo mức **PHỔ BIẾN** của luật. Luật có support cao = xuất hiện ở nhiều user.
        
        **② Confidence (Độ tin cậy)**  
        ```
        Confidence(A → B) = Support(A ∪ B) / Support(A)
        ```
        → Đo mức **ĐÁNG TIN** của luật. "Nếu có A, xác suất bao nhiêu % có B?"
        
        **③ Lift (Độ nâng)**
        ```
        Lift(A → B) = Confidence(A → B) / Support(B)
        ```
        → So sánh với **NGẪU NHIÊN**.
        - Lift > 1: A và B có mối quan hệ dương (đây là các luật ta muốn giữ)
        - Lift = 1: Độc lập, không có quan hệ
        - Lift < 1: A và B "ngại nhau" (loại trừ)
        
        ### Tại sao FP-Growth nhanh hơn Apriori?
        - **Apriori**: Sinh ra tất cả tập ứng viên rồi kiểm tra từng cái → **Tốn bộ nhớ O(2ⁿ)**
        - **FP-Growth**: Nén toàn bộ database vào **cây FP-Tree** → Chỉ duyệt cây 2 lần, không sinh ứng viên
        
        ### "Giao dịch" trong bài này là gì?
        Mỗi **UserId** = 1 giao dịch.  
        Nội dung giao dịch = tập hợp tất cả đặc trưng của user đó:
        ```
        User_12345 = {"Cặp đôi", "Beaches", "Xuất sắc", "🟡 Địa điểm Bình thường"}
        ```
        """)

    with st.expander("🔄 Luồng Xử Lý Dữ Liệu Toàn Bộ"):
        st.markdown("""
        ```
        9 file CSV gốc
             ↓ [data_processing.py]
        load_and_merge_data()    → Đọc + Merge đa tầng + Binning Rating
             ↓
        get_cleaned_features()   → Chọn 6 cột quan trọng + xóa NULL
             ↓ [chuan_bi_du_lieu.py]
        Việt hóa nhãn + Lưu thành DuLieu_DaLamSach_TiengViet.csv
             ↓ [app.py khi khởi động]
        apply_kmeans_clustering() → Thêm cột "Attraction_Hotness"
             ↓ [khi nhấn nút]
        mine_association_rules()  → Tìm luật kết hợp
             ↓
        Hiển thị biểu đồ + bảng kết quả
        ```
        """)

    with st.expander("🛠️ Cách Bảo Trì & Nâng Cấp"):
        st.markdown("""
        ### Bảo trì thường xuyên
        - **Thêm dữ liệu mới**: Chạy lại `chuan_bi_du_lieu.py` để cập nhật file CSV
        - **Thay đổi ngưỡng binning Rating**: Sửa hàm `binning_rating()` trong `data_processing.py`
        - **Thêm địa điểm mới**: Cập nhật `Item.csv` rồi chạy lại preprocessing
        
        ### Nâng cấp gợi ý
        - 🗺️ **Thêm bản đồ**: Dùng `pydeck` hoặc `folium` để hiển thị địa điểm trên bản đồ
        - 📧 **Thêm lọc theo khu vực**: Tích hợp cột `Region` vào FP-Growth
        - 📈 **Thêm phân tích xu hướng theo thời gian**: Dùng cột `VisitYear`, `VisitMonth`
        - 🤖 **Hệ thống gợi ý**: Dựa trên luật kết hợp để recommend địa điểm
        """)