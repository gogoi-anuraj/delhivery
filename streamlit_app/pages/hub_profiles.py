import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils import load_data, load_graphs, get_name_lookup, get_edge_weights

st.set_page_config(page_title="Hub Profiles", page_icon="🏭", layout="wide")
st.title("🏭 Hub Profiles")
st.markdown("Search any hub to see its full delay profile, corridor analysis, and intervention recommendation.")

# ── Load data ───────────────────────────────────────────────────────────
df, bottleneck, corridor = load_data()
graphs      = load_graphs()
G           = graphs['main']
name_lookup = get_name_lookup(df)
hub_lookup  = bottleneck.set_index('hub_code')

# ── Build searchable hub list ───────────────────────────────────────────
all_hubs = bottleneck[['hub_code','hub_name','bottleneck_score']].copy()
all_hubs['short_name'] = all_hubs['hub_name'].str.split('(').str[0].str.strip()
all_hubs = all_hubs.sort_values('bottleneck_score', ascending=False)

hub_options = all_hubs['short_name'].tolist()

# ── Sidebar — hub search ────────────────────────────────────────────────
st.sidebar.header("Hub search")
selected_name = st.sidebar.selectbox(
    "Select or search hub",
    hub_options,
    index=0,
)

selected_row  = all_hubs[all_hubs['short_name'] == selected_name].iloc[0]
selected_code = selected_row['hub_code']

# ── Intervention map ────────────────────────────────────────────────────
interventions = {
    'Gurgaon_Bilaspur_HB'  : ('Parallel Route',    '#A32D2D',
        'Create parallel inter-city corridors via Manesar and Faridabad '
        'to redistribute 20-30% of Gurgaon FTL volume. Volume problem, '
        'not operational — breach rate already among best large hubs.'),
    'Bangalore_Nelmngla_H' : ('Route-Type Shift',  '#C25A1A',
        'Shift Bengaluru city corridors (KH Road, Whitefield, Peenya) '
        'from FTL to Carting. National sorting hub doing last-mile city '
        'delivery — FTL vs Carting framework confirms Carting wins here.'),
    'Kolkata_Dankuni_HB'   : ('Facility Upgrade',  '#BA7517',
        'Increase unloading dock capacity at Dankuni. Incoming feeder '
        'delays (Ranaghat 11.6x, Helencha 11.6x, Midnapore 7.5x) indicate '
        'facility dwell time, not road congestion.'),
    'Hyderabad_Shamshbd_H' : ('Facility Upgrade',  '#BA7517',
        'Add night-shift dock staff — night breach rate 90.1% vs day 87.1%. '
        'Extend facility operating hours to 24/7. Review Tolichowki '
        'and Uppal feeder schedules.'),
    'Bhiwandi_Mankoli_HB'  : ('Parallel Route',    '#3B6D11',
        'Create direct Mumbai to destination corridors bypassing Bhiwandi '
        'for highest-volume flows (Mumbai Hub 171 trips, Chandivali 238 trips). '
        'Decongests Bhiwandi and reduces transit hops simultaneously.'),
}

# ── Hub metrics ─────────────────────────────────────────────────────────
if selected_code in hub_lookup.index:
    row = hub_lookup.loc[selected_code]

    # Rank
    rank = (bottleneck['bottleneck_score'] > row['bottleneck_score']).sum() + 1

    st.markdown(f"## {selected_name}")
    st.markdown(f"**Rank #{rank}** out of 1,657 hubs by bottleneck score")

    # Intervention banner if top 5
    hub_short = selected_code
    for key in interventions:
        if key in selected_name.replace(' ', '_') or key in selected_code:
            itype, icolor, idetail = interventions[key]
            st.markdown(
                f"<div style='background:{icolor}22; border-left: 4px solid {icolor}; "
                f"padding: 12px; border-radius: 4px; margin-bottom: 16px;'>"
                f"<b>Recommended intervention: {itype}</b><br>{idetail}</div>",
                unsafe_allow_html=True
            )
            break

    # ── Metric cards ────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Bottleneck Score",  f"{row['bottleneck_score']:.4f}")
    c2.metric("Betweenness",       f"{row['betweenness']:.4f}")
    c3.metric("Clustering",        f"{row['clustering']:.4f}")
    c4.metric("In-degree",         f"{int(row['in_degree'])}")
    c5.metric("Out-degree",        f"{int(row['out_degree'])}")
    c6.metric("Avg Edge Weight",   f"{row['avg_edge_weight']:.2f}×")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    # ── SLA metrics ──────────────────────────────────────────────────────
    with col_left:
        st.subheader("SLA breach profile")
        if row['total_trips'] > 0:
            s1, s2, s3 = st.columns(3)
            s1.metric("Total SLA trips",    f"{row['total_trips']:,.0f}")
            s2.metric("Breach rate",        f"{row['breach_rate']*100:.1f}%")
            s3.metric("Total cutoff score", f"{row['total_cutoff_score']:,.0f}")

            # Breach rate gauge
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=row['breach_rate'] * 100,
                title={'text': "SLA Breach Rate (%)"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar':  {'color': '#A32D2D'},
                    'steps': [
                        {'range': [0,  70], 'color': '#EAF3DE'},
                        {'range': [70, 85], 'color': '#FAEEDA'},
                        {'range': [85,100], 'color': '#FCEBEB'},
                    ],
                    'threshold': {
                        'line': {'color': 'black', 'width': 2},
                        'thickness': 0.75,
                        'value': 83.8  # network average
                    }
                },
                number={'suffix': '%', 'font': {'size': 28}}
            ))
            fig_gauge.update_layout(height=250, margin=dict(l=20,r=20,t=40,b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.caption("Black line = network average (83.8%)")
        else:
            st.info("No SLA data available for this hub.")

    # ── Worst corridors ──────────────────────────────────────────────────
    with col_right:
        st.subheader("Worst outgoing corridors")
        outgoing = corridor[corridor['source_center'] == selected_code]\
            .nlargest(8, 'weight')[['dest_name','weight','trip_count','mean_factor']]

        if len(outgoing) > 0:
            outgoing.columns = ['Destination','Median Factor','Trips','Mean Factor']
            outgoing['Median Factor'] = outgoing['Median Factor'].round(2)
            outgoing['Mean Factor']   = outgoing['Mean Factor'].round(2)
            outgoing = outgoing.reset_index(drop=True)
            outgoing.index = outgoing.index + 1

            fig_bar = px.bar(
                outgoing, x='Median Factor', y='Destination',
                orientation='h', color='Median Factor',
                color_continuous_scale='RdYlGn_r',
                range_color=[1.0, 5.0],
                text='Median Factor',
            )
            fig_bar.update_traces(texttemplate='%{text:.2f}×', textposition='outside')
            fig_bar.update_layout(
                height=300,
                margin=dict(l=10, r=30, t=10, b=10),
                coloraxis_showscale=False,
                yaxis=dict(autorange='reversed')
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No outgoing corridor data.")

    st.markdown("---")

    # ── Incoming corridors ───────────────────────────────────────────────
    st.subheader("Worst incoming corridors")
    incoming = corridor[corridor['destination_center'] == selected_code]\
        .nlargest(8, 'weight')[['source_name','weight','trip_count','mean_factor','cv']]

    if len(incoming) > 0:
        incoming.columns = ['Source','Median Factor','Trips','Mean Factor','CV']
        incoming['Median Factor'] = incoming['Median Factor'].round(2)
        incoming['Mean Factor']   = incoming['Mean Factor'].round(2)
        incoming['CV']            = incoming['CV'].round(3)
        incoming = incoming.reset_index(drop=True)
        incoming.index = incoming.index + 1
        st.dataframe(
            incoming.style.background_gradient(
                subset=['Median Factor'], cmap='RdYlGn_r', vmin=1.0, vmax=5.0),
            use_container_width=True
        )
    else:
        st.info("No incoming corridor data.")

    # ── Time of day breach pattern ───────────────────────────────────────
    st.markdown("---")
    st.subheader("Breach rate by time of day")

    hub_sla = df[(df['source_center'] == selected_code) & (df['is_cutoff'] == True)].copy()
    hub_sla['is_breach'] = hub_sla['segment_factor'] > 1.2

    if len(hub_sla) > 0:
        tod = hub_sla.groupby('hour_of_day')['is_breach'].mean().reset_index()
        tod.columns = ['Hour', 'Breach Rate']
        tod['Breach Rate'] = tod['Breach Rate'] * 100

        fig_tod = px.bar(
            tod, x='Hour', y='Breach Rate',
            color='Breach Rate',
            color_continuous_scale='RdYlGn_r',
            range_color=[50, 100],
            labels={'Breach Rate': 'Breach rate (%)'},
            title='SLA breach rate by hour of day',
        )
        fig_tod.add_hline(y=83.8, line_dash='dash', line_color='black',
                          annotation_text='Network avg 83.8%')
        fig_tod.update_layout(
            height=280,
            margin=dict(l=10,r=10,t=40,b=10),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_tod, use_container_width=True)
    else:
        st.info("No SLA trip data for this hub.")

else:
    st.warning(f"Hub {selected_name} not found in bottleneck data.")