import streamlit as st
import pandas as pd
import plotly.express as px
from mining_algorithms import apply_kmeans_clustering, mine_association_rules, get_cluster_summary

# CẤU HÌNH TRANG
st.set_page_config(
    page_title="Khai Phá Dữ Liệu Du Lịch",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem; color: white; text-align: center; }
    .theory-box { background: #1e3a5f; border-left: 4px solid #4fc3f7; padding: 1rem; border-radius: 4px; margin: 0.5rem 0; color: #e0f0ff !important; }
    .theory-box b { color: #7dd3fc !important; }
    .rule-card { background: #1a3a2a; border: 1px solid #4ade80; padding: 1.2rem; border-radius: 8px; margin: 0.5rem 0; color: #d1fae5 !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_data():
    try:
        df = pd.read_csv("DuLieu_DaLamSach_TiengViet.csv", encoding='utf-8-sig')
        df = apply_kmeans_clustering(df)
        return df
    except FileNotFoundError:
        return None

# HEADER
st.markdown("""
<div class="main-header">
    <h1>🗺️ HỆ THỐNG KHAI PHÁ DỮ LIỆU DU LỊCH INDONESIA</h1>
    <p>Thuật toán: <strong>K-Means Clustering</strong> & <strong>FP-Growth Association Rules</strong></p>
</div>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Bảng Điều Khiển")
    st.markdown("### 🔧 Tham số FP-Growth")
    min_supp = st.slider("Min Support", 0.01, 0.20, 0.05, 0.01)
    min_conf = st.slider("Min Confidence", 0.10, 1.00, 0.60, 0.05)

# TẢI DỮ LIỆU
with st.spinner("⏳ Đang tải dữ liệu và chạy K-Means..."):
    df = load_data()

if df is None or df.empty:
    st.error("❌ Không tìm thấy file 'DuLieu_DaLamSach_TiengViet.csv' hoặc file rỗng!")
    st.info("💡 Hãy chạy lệnh: `python chuan_bi_du_lieu.py` trước để tạo file này.")
    st.stop()

cluster_df = get_cluster_summary(df)

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Tổng quan Dữ liệu", "🔵 K-Means Clustering", "📏 FP-Growth Luật Kết Hợp", "📚 Lý Thuyết Thuật Toán"
])

# TAB 1: TỔNG QUAN
with tab1:
    st.header("📊 Tổng Quan Dữ Liệu Sau Tích Hợp")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng giao dịch", f"{df.shape[0]:,}")
    c2.metric("Địa điểm", df['Attraction'].nunique())
    c3.metric("Loại hình", df['TravelMode'].nunique())
    c4.metric("Rating trung bình", f"{df['Rating'].mean():.2f} ⭐")
    st.divider()

    col_left, col_right = st.columns(2)
    with col_left:
        # TỐI ƯU: Xử lý an toàn với rename_axis và reset_index(name='count')
        travel_counts = df['TravelMode'].value_counts().rename_axis('TravelMode').reset_index(name='count')
        fig_mode = px.pie(travel_counts, values='count', names='TravelMode', title="🧳 Phân bố Hình thức Du lịch")
        st.plotly_chart(fig_mode, use_container_width=True)

    with col_right:
        rating_counts = df['Rating_Level'].value_counts().reindex(['Xuất sắc', 'Tốt', 'Trung bình']).fillna(0)
        fig_rating = px.bar(x=rating_counts.index, y=rating_counts.values, title="⭐ Phân bố Đánh Giá", color=rating_counts.index)
        st.plotly_chart(fig_rating, use_container_width=True)

    top_attr = df['Attraction'].value_counts().head(10).rename_axis('Địa điểm').reset_index(name='Lượt thăm')
    fig_top = px.bar(top_attr, x='Lượt thăm', y='Địa điểm', orientation='h', title="🏆 Top 10 Địa Điểm")
    fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_top, use_container_width=True)

# TAB 2: K-MEANS
with tab2:
    st.header("🔵 Kết Quả Phân Cụm K-Means")
    if not cluster_df.empty:
        hot = cluster_df[cluster_df['Attraction_Hotness'].str.contains('Hot', na=False)]
        normal = cluster_df[cluster_df['Attraction_Hotness'].str.contains('Bình thường', na=False)]
        niche = cluster_df[cluster_df['Attraction_Hotness'].str.contains('Ngách', na=False)]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Địa điểm Hot", f"{len(hot)}", f"TB {hot['Total_Visits'].mean():.0f} lượt" if not hot.empty else "")
        c2.metric("🟡 Địa điểm Bình thường", f"{len(normal)}", f"TB {normal['Total_Visits'].mean():.0f} lượt" if not normal.empty else "")
        c3.metric("🔵 Địa điểm Ngách", f"{len(niche)}", f"TB {niche['Total_Visits'].mean():.0f} lượt" if not niche.empty else "")

        fig_kmeans = px.scatter(
            cluster_df, x='Total_Visits', y='Avg_Rating', color='Attraction_Hotness', text='Attraction',
            title="📍 Biểu Đồ Phân Cụm K-Means"
        )
        fig_kmeans.update_traces(textposition='top center')
        st.plotly_chart(fig_kmeans, use_container_width=True)

# TAB 3: FP-GROWTH
with tab3:
    st.header("📏 Khai Phá Luật FP-Growth")
    if st.button("🚀 Bắt đầu Khai phá Luật Kết Hợp", type="primary", use_container_width=True):
        with st.spinner("⏳ Đang chạy FP-Growth..."):
            rules = mine_association_rules(df, min_supp=min_supp, min_conf=min_conf)

        if rules is None or rules.empty:
            st.warning("⚠️ Không tìm thấy luật. Hãy giảm Min Support hoặc Min Confidence.")
        else:
            st.success(f"✅ Tìm thấy **{len(rules)}** luật kết hợp có ý nghĩa!")
            top = rules.iloc[0]
            st.markdown(f"""
            <div class="rule-card">
            <h4>Nếu có: <span style="color:#67e8f9">[{top['antecedents']}]</span></h4>
            <h4>👉 Thì suy ra: <span style="color:#86efac">[{top['consequents']}]</span></h4>
            <p>Support: {top['support']:.1%} | Confidence: {top['confidence']:.1%} | Lift: {top['lift']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Scatter Plot an toàn
            fig_rules = px.scatter(
                rules.head(50), x='support', y='confidence', size='lift', color='lift',
                hover_data=['antecedents', 'consequents'], title="📈 Support vs Confidence"
            )
            st.plotly_chart(fig_rules, use_container_width=True)

# TAB 4: LÝ THUYẾT (Giữ nguyên text của bạn)
with tab4:
    st.header("📚 Lý Thuyết Thuật Toán")
    st.info("Phần này tập trung giải thích các thông số kỹ thuật cho hội đồng chấm đồ án.")