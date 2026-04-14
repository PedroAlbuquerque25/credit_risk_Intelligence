import streamlit as st
import pandas as pd
import plotly.express as px
import pickle
import os

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title="Credit Risk Intelligence",
    page_icon="🏦",
    layout="wide"
)

# ── Paths ─────────────────────────────────────────────────
# Define the base path to locate /data and /dashboard folders
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Load data ─────────────────────────────────────────────
@st.cache_data
def load_data():
    # Robust absolute path loading for CSV files
    segments = pd.read_csv(os.path.join(BASE_DIR, 'data', 'customer_segments.csv'))
    results  = pd.read_csv(os.path.join(BASE_DIR, 'data', 'model_results.csv'))
    features = pd.read_csv(os.path.join(BASE_DIR, 'data', 'feature_importance.csv'))
    return segments, results, features

@st.cache_resource
def load_model():
    # Load the trained Random Forest model
    with open(os.path.join(BASE_DIR, 'dashboard', 'model.pkl'), 'rb') as f:
        return pickle.load(f)

# Execution of data loading
try:
    segments, results, features = load_data()
    model = load_model()
except Exception as e:
    st.error(f"❌ Error loading files: {e}")
    st.stop()

# ── Header ────────────────────────────────────────────────
st.title("🏦 Credit Risk Intelligence")
st.markdown("**Canadian Banking Project** — Risk Analytics Dashboard")
st.divider()

# ── KPIs ──────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

total    = len(results)
defaults = int(results['actual'].sum())
caught   = len(results[results['result_type'] == 'Hit (Defaulter)'])
missed   = len(results[results['result_type'] == 'Miss (Hidden Default)'])

col1.metric("Total Customers", f"{total:,}")
col2.metric("Actual Defaults", f"{defaults:,}")
col3.metric("Defaults Caught", f"{caught:,}",  delta=f"{caught/defaults*100:.1f}%")
col4.metric("Hidden Defaults", f"{missed:,}",  delta=f"-{missed/defaults*100:.1f}%", delta_color="inverse")

st.divider()

# ── Middle Section: Segments & Feature Importance ──────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Customer Segments")
    seg_count = segments['cluster_name'].value_counts().reset_index()
    seg_count.columns = ['Segment', 'Count']
    
    fig_seg = px.bar(
        seg_count, 
        x='Segment', 
        y='Count',
        color='Segment',
        color_discrete_sequence=px.colors.qualitative.Safe,
        text_auto='.2s'
    )
    fig_seg.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title=None,
        yaxis_title="Customers",
        height=400
    )
    st.plotly_chart(fig_seg, use_container_width=True)

with col_right:
    st.subheader("🔑 Key Risk Factors")
    # Horizontal bar chart for Feature Importance
    fig_importance = px.bar(
        features.head(10), 
        x='importance', 
        y='feature', 
        orientation='h',
        color='importance',
        color_continuous_scale='Blues'
    )
    fig_importance.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis={'categoryorder':'total ascending'},
        xaxis_title="Importance Score",
        yaxis_title=None,
        height=400
    )
    st.plotly_chart(fig_importance, use_container_width=True)

st.divider()

# ── Performance Section ───────────────────────────────────
st.subheader("🎯 Model Performance Metrics")
perf = results['result_type'].value_counts().reset_index()
perf.columns = ['Result Type', 'Count']
st.dataframe(perf, use_container_width=True, hide_index=True)

st.divider()

# ── Risk Simulator ────────────────────────────────────────
st.subheader("🔮 Individual Risk Simulator")
st.markdown("Adjust customer parameters to predict the probability of default.")

sim_col1, sim_col2, sim_col3 = st.columns(3)

with sim_col1:
    age               = st.slider("Age", 21, 100, 45)
    monthly_income    = st.number_input("Monthly Income (CAD $)", 0, 100000, 5000)
    debt_ratio        = st.slider("Debt Ratio (Debt/Income)", 0.0, 5.0, 0.3)

with sim_col2:
    revolving_util    = st.slider("Credit Utilization (%)", 0.0, 1.0, 0.3)
    open_credit_lines = st.slider("Open Credit Lines", 0, 30, 8)
    real_estate_loans = st.slider("Real Estate Loans", 0, 10, 1)

with sim_col3:
    late_30_59 = st.slider("Late 30-59 Days (Times)", 0, 10, 0)
    late_60_89 = st.slider("Late 60-89 Days (Times)", 0, 10, 0)
    late_90    = st.slider("Late 90+ Days (Times)",   0, 10, 0)
    dependents = st.slider("Dependents", 0, 10, 0)

# Feature Engineering for the Simulator
total_late  = late_30_59 + late_60_89 + late_90
high_util   = 1 if revolving_util > 0.75 else 0
debt_income = debt_ratio * monthly_income

# Input DataFrame (must match the training columns exactly)
input_data = pd.DataFrame([{
    'RevolvingUtilizationOfUnsecuredLines': revolving_util,
    'age':                                  age,
    'NumberOfTime30-59DaysPastDueNotWorse': late_30_59,
    'DebtRatio':                            debt_ratio,
    'MonthlyIncome':                        monthly_income,
    'NumberOfOpenCreditLinesAndLoans':      open_credit_lines,
    'NumberOfTimes90DaysLate':              late_90,
    'NumberRealEstateLoansOrLines':         real_estate_loans,
    'NumberOfTime60-89DaysPastDueNotWorse': late_60_89,
    'NumberOfDependents':                   dependents,
    'debt_to_income':                       debt_income,
    'total_late_payments':                  total_late,
    'high_utilization':                     high_util,
}])

if st.button("🚀 Calculate Risk Score", type="primary", use_container_width=True):
    # Probability prediction
    prob = model.predict_proba(input_data)[0][1]

    st.markdown(f"### Probability of Default: **{prob:.2%}**")
    st.progress(prob)

    if prob < 0.2:
        st.success("✅ **Low Risk:** High probability of payment. Credit approved.")
    elif prob < 0.5:
        st.warning("⚠️ **Medium Risk:** Moderate risk. Requires additional guarantees.")
    else:
        st.error("🚨 **High Risk:** Critical probability of default. Credit not recommended.")