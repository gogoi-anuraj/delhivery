import streamlit as st

st.set_page_config(
    page_title  = "Delhivery Network Intelligence",
    page_icon   = "🚚",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)

st.title("🚚 Delhivery Network Intelligence Dashboard")
st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Hubs",       "1,657")
with col2:
    st.metric("Total Corridors",  "2,783")
with col3:
    st.metric("SLA Breach Rate",  "83.8%",  delta="-4.3% if top 3 upgraded", delta_color="inverse")
with col4:
    st.metric("Graph Model MAE",  "38.34 min", delta="-30.8% vs baseline",   delta_color="inverse")
with col5:
    st.metric("Within-15% Accuracy", "65.0%", delta="+14.58pp vs baseline")

st.markdown("---")

st.markdown("""
### What this dashboard shows

Navigate using the sidebar:

| Page | What it shows |
|------|--------------|
| 🗺️ Network Map | Interactive graph — all 1,657 hubs, top 5 bottlenecks highlighted |
| 🏭 Hub Profiles | Search any hub — delay profile, corridors, intervention |
| 🛣️ Corridor Audit | Chronically delayed corridors — filter by severity |
| 📊 Model Comparison | Baseline vs graph-enhanced ETA model performance |
| 🚛 FTL vs Carting | Route-type decision scorecard for 68 hubs |

### Key findings
- **5 hubs** account for **70.6%** of all network SLA damage
- **Gurgaon Bilaspur HB** alone contributes **38.5%** of SLA risk
- **73.7%** of corridors are chronically delayed — systemic OSRM underestimation
- Graph-enhanced ETA model is **30.8% more accurate** than OSRM baseline
""")