import streamlit as st
import pandas as pd
import plotly.express as px
import glob

# 1. 페이지를 제일 넓게 쓰고, 메뉴바 숨기기
st.set_page_config(page_title="FinRAG 관리자 대시보드", page_icon="📊", layout="wide")

# 2. [핵심] CSS 해킹으로 화면 상하좌우 여백(Padding) 극단적으로 줄이기
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        /* 위젯들 사이의 기본 여백 줄이기 */
        div[data-testid="stMetric"] { margin-bottom: -10px; }
    </style>
""", unsafe_allow_html=True)

# 차트를 작고 밀도 있게 만들어주는 헬퍼 함수
def make_compact(fig):
    # 차트 높이를 260px로 고정하고, 쓸데없는 여백(마진)을 다 날립니다.
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=10))
    return fig

# 데이터 로드 함수
def load_spark_data(folder_name):
    path = f"output/{folder_name}/*.csv"
    files = glob.glob(path)
    if not files:
        return pd.DataFrame()
    return pd.read_csv(files[0])

# ====================================================
# 🌟 상단 헤더 & 핵심 KPI (가로로 한 줄에 쫙 배치)
# ====================================================
# 제목과 리프레시 버튼을 같은 줄에 배치하여 세로 공간 절약
head_col1, head_col2 = st.columns([8, 2])
with head_col1:
    st.markdown("### 📊 FinRAG 실시간 관제 대시보드")
with head_col2:
    if st.button("🔄 실시간 데이터 동기화", use_container_width=True):
        st.cache_data.clear()

kpi_df = load_spark_data("kpi_summary")
if kpi_df.empty:
    st.warning("⏳ 데이터를 기다리는 중입니다...")
    st.stop()

# KPI 4개를 한 줄에 꽉 차게 배치
k1, k2, k3, k4 = st.columns(4)
k1.metric("총 누적 대화 수", f"{kpi_df['total_chats'].iloc[0]:,} 건")
k2.metric("고유 사용자 (Sessions)", f"{kpi_df['total_unique_users'].iloc[0]:,} 명")
k3.metric("세션당 대화 (Molt)", f"{kpi_df['avg_chats_per_user'].iloc[0]} 턴")
k4.metric("평균 예치 성향", f"{kpi_df['avg_deposit_prob'].iloc[0]:.1f} %")

st.markdown("---") # 얇은 구분선

# ====================================================
# 💡 [중단] 차트 3개 (연령대 / 직업 / 자산)
# ====================================================
col1, col2, col3 = st.columns(3)

with col1:
    age_df = load_spark_data("demographics_age")
    if not age_df.empty:
        fig_age = px.pie(age_df, names="age_group", values="count", hole=0.4, title="👥 연령대 분포")
        st.plotly_chart(make_compact(fig_age), use_container_width=True)

with col2:
    job_df = load_spark_data("demographics_job")
    if not job_df.empty:
        fig_job = px.bar(job_df, x="count", y="job", orientation='h', title="💼 직업별 분포", color_discrete_sequence=["#2563EB"])
        st.plotly_chart(make_compact(fig_job), use_container_width=True)

with col3:
    wealth_df = load_spark_data("wealth_by_age")
    if not wealth_df.empty:
        fig_wealth = px.bar(wealth_df, x="age_group", y="avg_balance", text_auto='.2s', title="💰 연령별 평균 자산", color_discrete_sequence=["#059669"])
        st.plotly_chart(make_compact(fig_wealth), use_container_width=True)

# ====================================================
# 💡 [하단] 차트 3개 (트렌드 / 키워드 / 대출현황)
# ====================================================
col4, col5, col6 = st.columns(3)

with col4:
    trend_df = load_spark_data("trend_time")
    if not trend_df.empty:
        trend_df["hour_str"] = trend_df["hour"].astype(str) + "시"
        fig_trend = px.line(trend_df, x="hour_str", y="count", markers=True, title="📈 시간대별 접속 트렌드", color_discrete_sequence=["#DC2626"])
        st.plotly_chart(make_compact(fig_trend), use_container_width=True)

with col5:
    keyword_df = load_spark_data("keywords_top50")
    if not keyword_df.empty:
        top_keywords = keyword_df.head(10) # 15개에서 10개로 줄여서 차트 밀도 최적화
        fig_kw = px.bar(top_keywords, x="word", y="count", title="💬 주요 질문 키워드 Top10", color_discrete_sequence=["#7C3AED"])
        st.plotly_chart(make_compact(fig_kw), use_container_width=True)

with col6:
    loan_df = load_spark_data("demographics_loan")
    if not loan_df.empty:
        loan_df["loan_type"] = "주담대:" + loan_df["housing_loan"] + " / 신용:" + loan_df["personal_loan"]
        fig_loan = px.pie(loan_df, names="loan_type", values="count", title="🏦 대출 보유 현황", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(make_compact(fig_loan), use_container_width=True)