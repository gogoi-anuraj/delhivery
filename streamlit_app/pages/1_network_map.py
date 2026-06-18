import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
from utils import load_data, load_graphs, get_name_lookup, get_edge_weights

st.set_page_config(page_title="Network Map", page_icon="🗺️", layout="wide")
st.title("🗺️ Delhivery Logistics Network Map")
st.markdown("Interactive view of the hub network with bottleneck hubs highlighted.")

# ── Load data ───────────────────────────────────────────────────────────
df, bottleneck, corridor = load_data()
graphs      = load_graphs()
G           = graphs['main']
name_lookup = get_name_lookup(df)
hub_lookup  = bottleneck.set_index('hub_code')

# ── Sidebar controls ────────────────────────────────────────────────────
st.sidebar.header("Map controls")

graph_type = st.sidebar.selectbox(
    "Graph type",
    ["main", "ftl", "carting", "night", "peak_evening", "day"],
    index=0
)
G_selected = graphs[graph_type]

show_top_n = st.sidebar.slider("Show top N bottleneck hubs", 3, 20, 5)
min_trips  = st.sidebar.slider("Min corridor trip count", 1, 100, 5)
delay_threshold = st.sidebar.slider("Min delay factor to show", 1.0, 5.0, 1.5)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**{graph_type.upper()} graph:**")
st.sidebar.markdown(f"- Nodes: {G_selected.number_of_nodes():,}")
st.sidebar.markdown(f"- Edges: {G_selected.number_of_edges():,}")

# ── Top N bottleneck hubs ───────────────────────────────────────────────
top_n = bottleneck.nlargest(show_top_n, 'bottleneck_score')
top_n_codes = set(top_n['hub_code'].tolist())

# ── Build layout using spring layout on subgraph ────────────────────────
# Use top 100 hubs by degree for visualisation
top_hubs    = sorted(G_selected.degree(), key=lambda x: x[1], reverse=True)[:80]
top_hub_ids = [h[0] for h in top_hubs]

# Always include top N bottleneck hubs
include_nodes = set(top_hub_ids) | top_n_codes
subgraph      = G_selected.subgraph(include_nodes)

pos = nx.spring_layout(subgraph, seed=42, k=1.8)

# ── Build plotly figure ─────────────────────────────────────────────────
edge_traces = []
for u, v, data in subgraph.edges(data=True):
    if data['trip_count'] < min_trips:
        continue
    if data['weight'] < delay_threshold:
        continue

    x0, y0 = pos[u]
    x1, y1 = pos[v]
    weight  = data['weight']

    # Colour by weight
    if weight >= 3.0:
        color = 'rgba(163,45,45,0.6)'
    elif weight >= 2.0:
        color = 'rgba(186,117,23,0.5)'
    else:
        color = 'rgba(59,109,17,0.4)'

    edge_traces.append(go.Scatter(
        x=[x0, x1, None], y=[y0, y1, None],
        mode='lines',
        line=dict(width=1.2, color=color),
        hoverinfo='none',
        showlegend=False,
    ))

# ── Node traces ─────────────────────────────────────────────────────────
# Separate bottleneck vs normal nodes
bottleneck_x, bottleneck_y = [], []
bottleneck_text, bottleneck_hover = [], []
bottleneck_colors, bottleneck_sizes = [], []

normal_x, normal_y = [], []
normal_text, normal_hover = [], []

rank_colors = {1:'#A32D2D', 2:'#C25A1A', 3:'#BA7517',
               4:'#BA7517', 5:'#3B6D11', 6:'#3B6D11',
               7:'#185FA5', 8:'#185FA5', 9:'#185FA5', 10:'#185FA5'}

top_n_list = top_n['hub_code'].tolist()

for node in subgraph.nodes():
    x, y = pos[node]
    hub_name = name_lookup.get(node, node)
    short    = hub_name.split('(')[0].strip()

    if node in hub_lookup.index:
        bc    = hub_lookup.loc[node, 'betweenness']
        score = hub_lookup.loc[node, 'bottleneck_score']
        br    = hub_lookup.loc[node, 'breach_rate'] * 100
        hover = (f"<b>{short}</b><br>"
                 f"Bottleneck score: {score:.3f}<br>"
                 f"Betweenness: {bc:.4f}<br>"
                 f"Breach rate: {br:.1f}%<br>"
                 f"In/Out degree: {G_selected.in_degree(node)}/{G_selected.out_degree(node)}")
    else:
        hover = f"<b>{short}</b>"

    if node in top_n_codes:
        rank = top_n_list.index(node) + 1
        bottleneck_x.append(x)
        bottleneck_y.append(y)
        bottleneck_text.append(f"#{rank} {short[:12]}")
        bottleneck_hover.append(hover)
        bottleneck_colors.append(rank_colors.get(rank, '#A32D2D'))
        bottleneck_sizes.append(28)
    else:
        normal_x.append(x)
        normal_y.append(y)
        normal_text.append("")
        normal_hover.append(hover)

normal_trace = go.Scatter(
    x=normal_x, y=normal_y,
    mode='markers',
    marker=dict(size=8, color='#B5D4F4', line=dict(width=0.5, color='white')),
    text=normal_text,
    hovertext=normal_hover,
    hoverinfo='text',
    name='Other hubs',
)

bottleneck_trace = go.Scatter(
    x=bottleneck_x, y=bottleneck_y,
    mode='markers+text',
    marker=dict(
        size=bottleneck_sizes,
        color=bottleneck_colors,
        line=dict(width=1.5, color='white'),
    ),
    text=bottleneck_text,
    textposition='top center',
    textfont=dict(size=9, color='black'),
    hovertext=bottleneck_hover,
    hoverinfo='text',
    name=f'Top {show_top_n} bottleneck hubs',
)

fig = go.Figure(
    data=edge_traces + [normal_trace, bottleneck_trace],
    layout=go.Layout(
        title=dict(
            text=f"Delhivery network — {graph_type} graph | "
                 f"Top {show_top_n} bottleneck hubs highlighted",
            font=dict(size=14)
        ),
        showlegend=True,
        hovermode='closest',
        height=650,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        paper_bgcolor='white',
        plot_bgcolor='#f8f9fa',
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
    )
)

st.plotly_chart(fig, width='stretch')

# ── Edge colour legend ───────────────────────────────────────────────────
st.markdown("""
**Edge colour guide:**
🔴 Red = delay factor ≥ 3× &nbsp;&nbsp;
🟡 Amber = delay factor 2–3× &nbsp;&nbsp;
🟢 Green = delay factor < 2×
""")

# ── Top N hub summary table ─────────────────────────────────────────────
st.markdown("---")
st.subheader(f"Top {show_top_n} bottleneck hubs")

display = top_n[['hub_name','betweenness','breach_rate',
                  'total_cutoff_score','bottleneck_score']].copy()
display['breach_rate']        = (display['breach_rate'] * 100).round(1).astype(str) + '%'
display['betweenness']        = display['betweenness'].round(4)
display['bottleneck_score']   = display['bottleneck_score'].round(4)
display['total_cutoff_score'] = display['total_cutoff_score'].apply(lambda x: f"{x:,.0f}")
display.columns = ['Hub Name','Betweenness','Breach Rate',
                   'Total Cutoff Score','Bottleneck Score']
display.index = range(1, len(display) + 1)

st.dataframe(display, width='stretch')