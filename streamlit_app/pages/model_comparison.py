import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils import load_data

st.set_page_config(page_title="Model Comparison", page_icon="📊", layout="wide")
st.title("📊 ETA Model Comparison")
st.markdown("Baseline XGBoost vs Graph-enhanced model — performance on both PS-required metrics.")

# ── Model results (from Phase 3a and 3b) ───────────────────────────────
results = pd.DataFrame([
    {'Model': 'Linear Regression',              'MAE': 175.12, 'Within_15': 27.00,
     'Color': '#888780', 'Type': 'Baseline'},
    {'Model': 'XGBoost Baseline',               'MAE': 55.45,  'Within_15': 50.46,
     'Color': '#BA7517', 'Type': 'Baseline'},
    {'Model': 'XGBoost + node2vec',             'MAE': 40.56,  'Within_15': 62.14,
     'Color': '#C25A1A', 'Type': 'Graph'},
    {'Model': 'XGBoost + All Graph Features',   'MAE': 38.34,  'Within_15': 65.04,
     'Color': '#A32D2D', 'Type': 'Graph'},
])

# ── Summary metrics ──────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Baseline MAE",        "55.45 min")
c2.metric("Graph Model MAE",     "38.34 min",  delta="-30.8%",   delta_color="inverse")
c3.metric("Baseline Within-15%", "50.46%")
c4.metric("Graph Within-15%",    "65.04%",     delta="+14.58pp")

st.markdown("---")

# ── Two charts side by side ──────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Mean Absolute Error (lower is better)")

    fig_mae = go.Figure()
    for _, row in results.iterrows():
        fig_mae.add_trace(go.Bar(
            x=[row['Model']],
            y=[row['MAE']],
            marker_color=row['Color'],
            name=row['Model'],
            text=f"{row['MAE']:.1f}",
            textposition='outside',
            showlegend=False,
        ))

    fig_mae.add_hline(
        y=55.45, line_dash='dash',
        line_color='#BA7517', opacity=0.6,
        annotation_text='Baseline 55.45',
        annotation_position='right'
    )
    fig_mae.update_layout(
        height=380,
        margin=dict(l=10,r=60,t=20,b=80),
        yaxis_title='MAE (minutes)',
        xaxis_tickangle=-15,
        plot_bgcolor='#f8f9fa',
        yaxis=dict(gridcolor='#e0e0e0'),
    )
    st.plotly_chart(fig_mae, use_container_width=True)

with col2:
    st.subheader("Within-15% Accuracy (higher is better)")

    fig_w15 = go.Figure()
    for _, row in results.iterrows():
        fig_w15.add_trace(go.Bar(
            x=[row['Model']],
            y=[row['Within_15']],
            marker_color=row['Color'],
            name=row['Model'],
            text=f"{row['Within_15']:.1f}%",
            textposition='outside',
            showlegend=False,
        ))

    fig_w15.add_hline(
        y=50.46, line_dash='dash',
        line_color='#BA7517', opacity=0.6,
        annotation_text='Baseline 50.46%',
        annotation_position='right'
    )
    fig_w15.update_layout(
        height=380,
        margin=dict(l=10,r=80,t=20,b=80),
        yaxis_title='% of trips within 15% of actual',
        xaxis_tickangle=-15,
        plot_bgcolor='#f8f9fa',
        yaxis=dict(gridcolor='#e0e0e0', range=[0, 80]),
    )
    st.plotly_chart(fig_w15, use_container_width=True)

st.markdown("---")

# ── Improvement breakdown ────────────────────────────────────────────────
st.subheader("What each graph feature group contributed")

improvement = pd.DataFrame([
    {'Feature group'  : 'Tabular only (baseline)',
     'MAE'           : 55.45,
     'Within_15'     : 50.46,
     'MAE_reduction' : 0.0,
     'W15_gain'      : 0.0},
    {'Feature group'  : '+ node2vec embeddings',
     'MAE'           : 40.56,
     'Within_15'     : 62.14,
     'MAE_reduction' : round(55.45 - 40.56, 2),
     'W15_gain'      : round(62.14 - 50.46, 2)},
    {'Feature group'  : '+ graph metrics & corridor features',
     'MAE'           : 38.34,
     'Within_15'     : 65.04,
     'MAE_reduction' : round(40.56 - 38.34, 2),
     'W15_gain'      : round(65.04 - 62.14, 2)},
])

col3, col4 = st.columns(2)

with col3:
    fig_waterfall_mae = go.Figure(go.Waterfall(
        name='MAE reduction',
        orientation='v',
        measure=['absolute', 'relative', 'relative'],
        x=improvement['Feature group'],
        y=[55.45, -(55.45 - 40.56), -(40.56 - 38.34)],
        text=['55.45', '-14.89', '-2.22'],
        textposition='outside',
        connector={'line': {'color': 'gray', 'dash': 'dot'}},
        decreasing={'marker': {'color': '#3B6D11'}},
        increasing={'marker': {'color': '#A32D2D'}},
        totals={'marker': {'color': '#BA7517'}},
    ))
    fig_waterfall_mae.update_layout(
        title='MAE reduction by feature group',
        height=350,
        margin=dict(l=10,r=10,t=50,b=10),
        yaxis_title='MAE (minutes)',
        plot_bgcolor='#f8f9fa',
        xaxis_tickangle=-10,
    )
    st.plotly_chart(fig_waterfall_mae, use_container_width=True)

with col4:
    fig_waterfall_w15 = go.Figure(go.Waterfall(
        name='Within-15% gain',
        orientation='v',
        measure=['absolute', 'relative', 'relative'],
        x=improvement['Feature group'],
        y=[50.46, 62.14 - 50.46, 65.04 - 62.14],
        text=['50.46%', '+11.68pp', '+2.90pp'],
        textposition='outside',
        connector={'line': {'color': 'gray', 'dash': 'dot'}},
        increasing={'marker': {'color': '#3B6D11'}},
        decreasing={'marker': {'color': '#A32D2D'}},
        totals={'marker': {'color': '#BA7517'}},
    ))
    fig_waterfall_w15.update_layout(
        title='Within-15% gain by feature group',
        height=350,
        margin=dict(l=10,r=10,t=50,b=10),
        yaxis_title='Within-15% accuracy (%)',
        plot_bgcolor='#f8f9fa',
        xaxis_tickangle=-10,
    )
    st.plotly_chart(fig_waterfall_w15, use_container_width=True)

st.markdown("---")

# ── Feature importance context ───────────────────────────────────────────
st.subheader("Graph feature importance — what contributed most")

feature_importance = pd.DataFrame([
    {'Feature': 'osrm_distance',          'Importance': 0.491, 'Group': 'Tabular'},
    {'Feature': 'osrm_time',              'Importance': 0.178, 'Group': 'Tabular'},
    {'Feature': 'segment_ratio',          'Importance': 0.052, 'Group': 'Tabular'},
    {'Feature': 'corridor_mean_factor',   'Importance': 0.021, 'Group': 'Corridor'},
    {'Feature': 'corridor_median_factor', 'Importance': 0.014, 'Group': 'Corridor'},
    {'Feature': 'segment_osrm_time',      'Importance': 0.013, 'Group': 'Tabular'},
    {'Feature': 'is_cutoff',              'Importance': 0.008, 'Group': 'Tabular'},
    {'Feature': 'dst_in_degree',          'Importance': 0.007, 'Group': 'Graph metric'},
    {'Feature': 'is_carting',             'Importance': 0.006, 'Group': 'Tabular'},
    {'Feature': 'dst_betweenness',        'Importance': 0.004, 'Group': 'Graph metric'},
    {'Feature': 'dst_avg_weight',         'Importance': 0.003, 'Group': 'Graph metric'},
    {'Feature': 'src_out_degree',         'Importance': 0.003, 'Group': 'Graph metric'},
]).sort_values('Importance', ascending=True)

color_map = {
    'Tabular'     : '#4C72B0',
    'Corridor'    : '#A32D2D',
    'Graph metric': '#3B6D11',
    'Embedding'   : '#888780',
}
feature_importance['Color'] = feature_importance['Group'].map(color_map)

fig_imp = px.bar(
    feature_importance,
    x='Importance', y='Feature',
    orientation='h',
    color='Group',
    color_discrete_map=color_map,
    text='Importance',
    title='Top feature importance — graph-enhanced model',
)
fig_imp.update_traces(texttemplate='%{text:.3f}', textposition='outside')
fig_imp.update_layout(
    height=420,
    margin=dict(l=10,r=60,t=50,b=10),
    plot_bgcolor='#f8f9fa',
    xaxis=dict(gridcolor='#e0e0e0'),
)
st.plotly_chart(fig_imp, use_container_width=True)

# ── Key findings ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Key findings")

st.markdown("""
| Finding | Detail |
|---------|--------|
| **Graph advantage** | 30.8% MAE reduction — measured, not claimed |
| **Corridor features most impactful** | `corridor_mean_factor` and `corridor_median_factor` in top 5 |
| **Destination hub matters more than source** | `dst_in_degree` and `dst_betweenness` outrank source metrics |
| **Distance still dominates** | `osrm_distance` (0.491) — model is distance-to-time corrected by graph |
| **CV confirmed no overfitting** | TimeSeriesSplit CV MAE 58.62 ± 7.47 vs test MAE 55.45 |
| **OSRM underestimates by 2.1×** | Graph model corrects this corridor-specifically |
""")