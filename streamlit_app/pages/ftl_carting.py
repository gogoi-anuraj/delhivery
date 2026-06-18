import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pickle
from utils import load_data, load_graphs, get_name_lookup

st.set_page_config(page_title="FTL vs Carting", page_icon="🚛", layout="wide")
st.title("🚛 FTL vs Carting Decision Framework")
st.markdown("Graph-aware route-type scorecard for 68 hubs where both FTL and Carting operate.")

# ── Load data ───────────────────────────────────────────────────────────
df, bottleneck, corridor = load_data()
name_lookup = get_name_lookup(df)

import os
BASE_DIR      = BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FTL_PATH      = os.path.join(BASE_DIR, "outputs", "models", "ftl_carting_model.pkl")

@st.cache_resource
def load_ftl():
    with open(FTL_PATH, 'rb') as f:
        return pickle.load(f)

framework = load_ftl()
scorecard = framework['scorecard'].copy()

# ── Sidebar filters ─────────────────────────────────────────────────────
st.sidebar.header("Filters")

rec_filter = st.sidebar.radio(
    "Show recommendations",
    ["All", "Carting only", "FTL only"],
    index=0
)

min_bc = st.sidebar.slider(
    "Min betweenness centrality", 0.0,
    float(scorecard['betweenness'].max()), 0.0,
    step=0.005, format="%.3f"
)

min_trips = st.sidebar.slider(
    "Min FTL trips", 1,
    int(scorecard['ftl_trips'].max()), 10
)

# ── Apply filters ────────────────────────────────────────────────────────
filtered = scorecard[
    (scorecard['betweenness'] >= min_bc) &
    (scorecard['ftl_trips']   >= min_trips)
].copy()

if rec_filter == "Carting only":
    filtered = filtered[filtered['recommendation'] == 'Carting']
elif rec_filter == "FTL only":
    filtered = filtered[filtered['recommendation'] == 'FTL']

# ── Summary metrics ──────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Hubs analysed",      f"{len(scorecard):,}")
c2.metric("Showing",            f"{len(filtered):,}")
c3.metric("Carting recommended",
          f"{(scorecard['recommendation']=='Carting').sum():,}")
c4.metric("FTL recommended",
          f"{(scorecard['recommendation']=='FTL').sum():,}")
c5.metric("Top SHAP driver", "carting_factor")
st.markdown("---")

# ── Two column layout ────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 3])

with col_left:
    st.subheader("Recommendation scorecard")

    display = filtered[[
        'hub_name','betweenness','ftl_time_per_km',
        'carting_time_per_km','ftl_breach','carting_breach',
        'recommendation'
    ]].copy()

    display['hub_name']          = display['hub_name'].str.split('(').str[0].str.strip()
    display['betweenness']       = display['betweenness'].round(4)
    display['ftl_time_per_km']   = display['ftl_time_per_km'].round(2)
    display['carting_time_per_km'] = display['carting_time_per_km'].round(2)
    display['ftl_breach']        = (display['ftl_breach']*100).round(1).astype(str) + '%'
    display['carting_breach']    = (display['carting_breach']*100).round(1).astype(str) + '%'
    display = display.sort_values('betweenness', ascending=False).reset_index(drop=True)
    display.index = display.index + 1
    display.columns = [
        'Hub','Betweenness','FTL min/km',
        'Carting min/km','FTL breach','Carting breach','Rec'
    ]

    def color_rec(val):
        if val == 'Carting':
            return 'background-color: #EAF3DE; color: #27500A'
        return 'background-color: #FCEBEB; color: #A32D2D'

    st.dataframe(
        display.style.map(color_rec, subset=['Rec']),
        use_container_width=True,
        height=520,
    )

with col_right:
    st.subheader("Quadrant map — graph position vs Carting efficiency")

    med_bc  = scorecard['betweenness'].median()
    med_cpm = scorecard['carting_time_per_km'].median()

    colors_rec = ['#3B6D11' if r == 'Carting' else '#A32D2D'
                  for r in filtered['recommendation']]
    sizes = filtered['out_degree'] * 8 + 20

    fig_quad = go.Figure()

    # Quadrant shading
    fig_quad.add_shape(type='rect',
        x0=med_bc, x1=filtered['betweenness'].max()*1.1,
        y0=med_cpm, y1=filtered['carting_time_per_km'].max()*1.05,
        fillcolor='rgba(163,45,45,0.05)', line_width=0
    )

    for rec, color, label in [('Carting','#3B6D11','Carting recommended'),
                                ('FTL','#A32D2D','FTL recommended')]:
        mask = filtered['recommendation'] == rec
        sub  = filtered[mask]
        fig_quad.add_trace(go.Scatter(
            x=sub['betweenness'],
            y=sub['carting_time_per_km'],
            mode='markers+text',
            marker=dict(
                size=(sub['out_degree'] * 0.8 + 8).clip(8, 30),
                color=color,
                opacity=0.8,
                line=dict(width=1, color='white')
            ),
            text=sub['hub_name'].str.split('(').str[0].str.strip().str[:12],
            textposition='top center',
            textfont=dict(size=7),
            name=label,
            hovertemplate=(
                '<b>%{customdata[0]}</b><br>'
                'Betweenness: %{x:.4f}<br>'
                'Carting min/km: %{y:.2f}<br>'
                'FTL breach: %{customdata[1]:.1f}%<br>'
                'Carting breach: %{customdata[2]:.1f}%<br>'
                '<extra></extra>'
            ),
            customdata=np.column_stack([
                sub['hub_name'].str.split('(').str[0].str.strip(),
                sub['ftl_breach']*100,
                sub['carting_breach']*100,
            ])
        ))

    # Threshold lines
    fig_quad.add_vline(x=med_bc, line_dash='dash',
                       line_color='gray', opacity=0.5)
    fig_quad.add_hline(y=med_cpm, line_dash='dash',
                       line_color='gray', opacity=0.5)

    # Quadrant annotations
    fig_quad.add_annotation(
        x=med_bc*0.3, y=filtered['carting_time_per_km'].min()*1.1,
        text='Low BC · Carting ok',
        showarrow=False, font=dict(size=9, color='#3B6D11'),
        xanchor='left'
    )
    fig_quad.add_annotation(
        x=med_bc*1.05, y=filtered['carting_time_per_km'].min()*1.1,
        text='High BC · Carting ok',
        showarrow=False, font=dict(size=9, color='#BA7517'),
        xanchor='left'
    )
    fig_quad.add_annotation(
        x=med_bc*1.05, y=filtered['carting_time_per_km'].max()*0.95,
        text='High BC · USE FTL',
        showarrow=False, font=dict(size=9, color='#A32D2D',),
        xanchor='left'
    )

    fig_quad.update_layout(
        height=480,
        margin=dict(l=10,r=10,t=20,b=50),
        xaxis_title='Betweenness centrality (structural importance)',
        yaxis_title='Carting time per km (min/km)',
        plot_bgcolor='#f8f9fa',
        legend=dict(x=0.01, y=0.99),
    )
    st.plotly_chart(fig_quad, use_container_width=True)

# ── Breach rate comparison ───────────────────────────────────────────────
st.markdown("---")
st.subheader("SLA breach rate — FTL vs Carting (top 15 hubs by betweenness)")

top15 = scorecard.nlargest(15, 'betweenness').copy()
top15['short'] = top15['hub_name'].str.split('(').str[0].str.strip().str[:18]

fig_breach = go.Figure()
fig_breach.add_trace(go.Bar(
    name='FTL',
    x=top15['short'],
    y=top15['ftl_breach']*100,
    marker_color='#4C72B0',
    text=(top15['ftl_breach']*100).round(1),
    texttemplate='%{text:.0f}%',
    textposition='outside',
))
fig_breach.add_trace(go.Bar(
    name='Carting',
    x=top15['short'],
    y=top15['carting_breach']*100,
    marker_color='#DD8452',
    text=(top15['carting_breach']*100).round(1),
    texttemplate='%{text:.0f}%',
    textposition='outside',
))
fig_breach.add_hline(y=80, line_dash='dash', line_color='red',
                     opacity=0.5, annotation_text='80% reference')
fig_breach.update_layout(
    barmode='group',
    height=380,
    margin=dict(l=10,r=10,t=20,b=100),
    yaxis_title='SLA breach rate (%)',
    xaxis_tickangle=-35,
    plot_bgcolor='#f8f9fa',
    legend=dict(x=0.01, y=0.99),
    yaxis=dict(range=[0, 115]),
)
st.plotly_chart(fig_breach, use_container_width=True)

# ── SHAP importance ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("What drives the FTL vs Carting recommendation (SHAP)")

shap_data = pd.DataFrame([
    {'Feature': 'carting_factor',       'SHAP': 2.480, 'Group': 'Carting performance'},
    {'Feature': 'ftl_time_per_km',      'SHAP': 1.167, 'Group': 'FTL performance'},
    {'Feature': 'ftl_factor',           'SHAP': 1.082, 'Group': 'FTL performance'},
    {'Feature': 'ftl_breach',           'SHAP': 0.868, 'Group': 'FTL performance'},
    {'Feature': 'carting_time_per_km',  'SHAP': 0.300, 'Group': 'Carting performance'},
    {'Feature': 'carting_breach',       'SHAP': 0.266, 'Group': 'Carting performance'},
    {'Feature': 'carting_distance',     'SHAP': 0.193, 'Group': 'Carting performance'},
    {'Feature': 'betweenness',          'SHAP': 0.184, 'Group': 'Graph position'},
    {'Feature': 'bottleneck_score',     'SHAP': 0.167, 'Group': 'Graph position'},
    {'Feature': 'avg_distance',         'SHAP': 0.124, 'Group': 'Distance'},
    {'Feature': 'avg_edge_weight',      'SHAP': 0.102, 'Group': 'Graph position'},
    {'Feature': 'out_degree',           'SHAP': 0.050, 'Group': 'Graph position'},
]).sort_values('SHAP', ascending=True)

color_map = {
    'Carting performance': '#A32D2D',
    'FTL performance'    : '#4C72B0',
    'Graph position'     : '#3B6D11',
    'Distance'           : '#888780',
}

fig_shap = px.bar(
    shap_data, x='SHAP', y='Feature',
    orientation='h',
    color='Group',
    color_discrete_map=color_map,
    text='SHAP',
    title='SHAP feature importance — FTL vs Carting decision',
)
fig_shap.update_traces(texttemplate='%{text:.3f}', textposition='outside')
fig_shap.update_layout(
    height=400,
    margin=dict(l=10,r=60,t=50,b=10),
    plot_bgcolor='#f8f9fa',
    xaxis=dict(gridcolor='#e0e0e0'),
)
st.plotly_chart(fig_shap, use_container_width=True)

# ── Decision rules ───────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Recommendation rules")

st.markdown("""
**Use Carting if ALL three conditions hold:**

| Condition | Threshold | Rationale |
|-----------|-----------|-----------|
| `carting_time_per_km ≤ ftl_time_per_km × 1.30` | 30% slower per km | Cost advantage of Carting justifies moderate efficiency penalty |
| `delay_cost_of_carting < 0.30` | 0.30× factor gap | Cap on acceptable unpredictability |
| `breach_change < 0.05` | 5% breach increase | Operational noise tolerance |

**Use FTL** if any condition fails.

**Data limitation:** Only 68 of 1,657 hubs have both FTL and Carting trips (≥10 each).
Framework is most useful for new corridor planning decisions.
""")

# ── Clearest wins ────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Clearest Carting wins")

carting_wins = scorecard[scorecard['recommendation']=='Carting'].copy()
carting_wins['breach_improvement'] = (
    carting_wins['ftl_breach'] - carting_wins['carting_breach']
) * 100
carting_wins = carting_wins.nlargest(10, 'breach_improvement')[[
    'hub_name','betweenness','ftl_breach','carting_breach',
    'breach_improvement','ftl_time_per_km','carting_time_per_km'
]].copy()

carting_wins['hub_name']          = carting_wins['hub_name'].str.split('(').str[0].str.strip()
carting_wins['ftl_breach']        = (carting_wins['ftl_breach']*100).round(1).astype(str) + '%'
carting_wins['carting_breach']    = (carting_wins['carting_breach']*100).round(1).astype(str) + '%'
carting_wins['breach_improvement']= carting_wins['breach_improvement'].round(1).astype(str) + 'pp'
carting_wins['betweenness']       = carting_wins['betweenness'].round(4)
carting_wins['ftl_time_per_km']   = carting_wins['ftl_time_per_km'].round(2)
carting_wins['carting_time_per_km'] = carting_wins['carting_time_per_km'].round(2)
carting_wins = carting_wins.reset_index(drop=True)
carting_wins.index = carting_wins.index + 1
carting_wins.columns = [
    'Hub','Betweenness','FTL breach','Carting breach',
    'Breach improvement','FTL min/km','Carting min/km'
]

st.dataframe(carting_wins, use_container_width=True)
st.caption("Sorted by breach rate improvement — hubs where switching to Carting reduces SLA breaches most.")