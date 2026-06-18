import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, load_graphs, get_name_lookup

st.set_page_config(page_title="Corridor Audit", page_icon="🛣️", layout="wide")
st.title("🛣️ Corridor Delay Audit")
st.markdown("Chronically delayed corridors — actual time exceeds OSRM prediction by >20% consistently.")

# ── Load data ───────────────────────────────────────────────────────────
df, bottleneck, corridor = load_data()
name_lookup = get_name_lookup(df)

# ── Compute chronic flag if not present ─────────────────────────────────
if 'is_chronic' not in corridor.columns:
    corridor['is_chronic'] = (
        (corridor['weight'] > 1.2) &
        (corridor['trip_count'] >= 5)
    )
if 'cv' not in corridor.columns:
    corridor['cv'] = (
        corridor['std_factor'] /
        corridor['mean_factor'].replace(0, np.nan)
    ).fillna(0)

# ── Sidebar filters ─────────────────────────────────────────────────────
st.sidebar.header("Filters")

show_chronic_only = st.sidebar.checkbox("Chronic corridors only", value=True)

min_factor = st.sidebar.slider(
    "Min median delay factor", 1.0, 11.6, 1.5, step=0.1)

min_trips = st.sidebar.slider(
    "Min trip count (confidence)", 1, 100, 5)

route_type_filter = st.sidebar.selectbox(
    "Route type", ["All", "FTL", "Carting"], index=0)

state_options = ["All"] + sorted(
    corridor['source_name'].str.extract(r'\((.+)\)')[0].dropna().unique().tolist()
)
state_filter = st.sidebar.selectbox("Source state", state_options, index=0)

# ── Apply filters ────────────────────────────────────────────────────────
filtered = corridor.copy()

if show_chronic_only:
    filtered = filtered[filtered['is_chronic'] == True]

filtered = filtered[
    (filtered['weight'] >= min_factor) &
    (filtered['trip_count'] >= min_trips)
]

if route_type_filter != "All":
    # Filter by checking route type in raw data
    if route_type_filter == "FTL":
        ftl_corridors = df[df['route_type']=='FTL'].groupby(
            ['source_center','destination_center']).size().reset_index()[
            ['source_center','destination_center']]
        filtered = filtered.merge(ftl_corridors, on=['source_center','destination_center'])
    else:
        cart_corridors = df[df['route_type']=='Carting'].groupby(
            ['source_center','destination_center']).size().reset_index()[
            ['source_center','destination_center']]
        filtered = filtered.merge(cart_corridors, on=['source_center','destination_center'])

if state_filter != "All":
    filtered = filtered[
        filtered['source_name'].str.contains(state_filter, na=False)
    ]

filtered = filtered.sort_values('weight', ascending=False)

# ── Summary metrics ──────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total corridors",    f"{len(corridor):,}")
c2.metric("Chronic corridors",  f"{corridor['is_chronic'].sum():,}",
          delta=f"{corridor['is_chronic'].mean()*100:.1f}% of all")
c3.metric("Showing",            f"{len(filtered):,}")
c4.metric("Avg delay (filtered)", f"{filtered['weight'].mean():.2f}×"
          if len(filtered) > 0 else "—")

st.markdown("---")

# ── Two column layout ────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("Corridor delay table")

    display = filtered.head(50)[
        ['source_name','dest_name','weight',
         'trip_count','mean_factor','std_factor','cv']
    ].copy()
    display.columns = [
        'Source Hub','Destination Hub','Median Factor',
        'Trips','Mean Factor','Std','CV'
    ]
    display['Median Factor'] = display['Median Factor'].round(3)
    display['Mean Factor']   = display['Mean Factor'].round(3)
    display['Std']           = display['Std'].round(3)
    display['CV']            = display['CV'].round(3)
    display = display.reset_index(drop=True)
    display.index = display.index + 1

    st.dataframe(
        display.style.background_gradient(
            subset=['Median Factor'],
            cmap='RdYlGn_r', vmin=1.0, vmax=5.0
        ),
        width='stretch',
        height=500,
    )

with col_right:
    st.subheader("Delay factor distribution")

    fig_hist = px.histogram(
        filtered, x='weight', nbins=40,
        color_discrete_sequence=['#4C72B0'],
        labels={'weight': 'Median delay factor', 'count': 'Corridors'},
        title='Distribution of corridor delay factors'
    )
    fig_hist.add_vline(x=1.2, line_dash='dash', line_color='red',
                       annotation_text='1.2× threshold')
    fig_hist.add_vline(x=filtered['weight'].median(),
                       line_dash='dash', line_color='orange',
                       annotation_text=f"Median {filtered['weight'].median():.2f}×")
    fig_hist.update_layout(height=280, margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig_hist, width='stretch')

    st.subheader("Top 15 worst corridors")
    top15 = filtered.head(15).copy()

    if len(top15) > 0:
        top15['label'] = (
            top15['source_name'].str.split('(').str[0].str.strip().str[:14] +
            ' → ' +
            top15['dest_name'].str.split('(').str[0].str.strip().str[:14]
        )
        fig_top = px.bar(
            top15, x='weight', y='label',
            orientation='h',
            color='weight',
            color_continuous_scale='RdYlGn_r',
            range_color=[1.0, 5.0],
            text='weight',
            labels={'weight': 'Median factor', 'label': ''},
        )
        fig_top.update_traces(
            texttemplate='%{text:.2f}×',
            textposition='outside'
        )
        fig_top.update_layout(
            height=420,
            margin=dict(l=10,r=40,t=10,b=10),
            yaxis=dict(autorange='reversed'),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_top, width='stretch')

# ── Destination hub heatmap ──────────────────────────────────────────────
st.markdown("---")
st.subheader("Destination hub — how many delayed corridors feed into each hub?")

dest_summary = (
    filtered.groupby('dest_name')
    .agg(
        chronic_corridors = ('weight', 'count'),
        avg_delay         = ('weight', 'mean'),
        max_delay         = ('weight', 'max'),
    )
    .reset_index()
    .sort_values('chronic_corridors', ascending=False)
    .head(20)
)
dest_summary['short_name'] = dest_summary['dest_name'].str.split('(').str[0].str.strip()

fig_dest = px.bar(
    dest_summary, x='chronic_corridors', y='short_name',
    orientation='h',
    color='avg_delay',
    color_continuous_scale='RdYlGn_r',
    range_color=[1.0, 4.0],
    labels={
        'chronic_corridors': 'Number of delayed incoming corridors',
        'short_name': 'Destination hub',
        'avg_delay': 'Avg delay'
    },
    title='Top 20 destination hubs by number of delayed incoming corridors',
    text='chronic_corridors',
)
fig_dest.update_traces(textposition='outside')
fig_dest.update_layout(
    height=500,
    margin=dict(l=10,r=30,t=50,b=10),
    yaxis=dict(autorange='reversed'),
)
st.plotly_chart(fig_dest, width='stretch')

st.caption(
    "A hub appearing frequently as a destination with high delay factors "
    "suggests a facility bottleneck — multiple sources delayed at the same receiving hub."
)