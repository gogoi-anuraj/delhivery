import pandas as pd
import numpy as np
import networkx as nx
import pickle
import streamlit as st
import os

# ── Paths — adjust if your outputs folder is elsewhere ─────────────────
BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_PATH      = os.path.join(BASE_DIR, "outputs", "clean_all.parquet")
GRAPH_PATH      = os.path.join(BASE_DIR, "outputs", "graphs.pkl")
BOTTLENECK_PATH = os.path.join(BASE_DIR, "outputs", "bottleneck_hubs.parquet")
CORRIDOR_PATH   = os.path.join(BASE_DIR, "outputs", "corridor_audit.parquet")
FTL_MODEL_PATH  = os.path.join(BASE_DIR, "outputs", "models", "ftl_carting_model.pkl")

@st.cache_data
def load_data():
    df         = pd.read_parquet(CLEAN_PATH)
    bottleneck = pd.read_parquet(BOTTLENECK_PATH)
    corridor   = pd.read_parquet(CORRIDOR_PATH)
    return df, bottleneck, corridor

@st.cache_resource
def load_graphs():
    with open(GRAPH_PATH, 'rb') as f:
        return pickle.load(f)

@st.cache_resource
def load_ftl_model():
    with open(FTL_MODEL_PATH, 'rb') as f:
        return pickle.load(f)

@st.cache_data
def get_name_lookup(_df):
    name_lookup = {}
    for _, row in _df.groupby('source_center')['source_name'].first().reset_index().iterrows():
        name_lookup[row['source_center']] = row['source_name']
    return name_lookup

@st.cache_data
def get_edge_weights(_df):
    return (
        _df.groupby(['source_center', 'destination_center'])
        .agg(
            weight      = ('segment_factor', 'median'),
            trip_count  = ('segment_factor', 'count'),
            mean_factor = ('segment_factor', 'mean'),
            source_name = ('source_name',    'first'),
            dest_name   = ('destination_name','first'),
        )
        .reset_index()
    )