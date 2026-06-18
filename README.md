# Optimising Delivery ETAs with Graph-Based Network Intelligence
### Delhivery | Machine Learning Consulting Project

---

## Overview

This project builds a graph-based intelligence system for Delhivery's logistics network. The network is modelled as a directed weighted graph where facilities are nodes and corridors are edges with median delay factors as weights. The system produces smarter ETA predictions, identifies bottleneck hubs, and provides a data-backed FTL vs Carting decision framework.

**Data:** 144,867 trip segments across 1,657 hubs — Sep 12 to Oct 3, 2018

---

## Key Results

### ETA Model
| Model | MAE | Within 15% of actual |
|-------|-----|----------------------|
| Linear Regression (floor) | 175.12 min | 27.00% |
| XGBoost Baseline (tabular only) | 55.45 min | 50.46% |
| XGBoost + node2vec embeddings | 40.56 min | 62.14% |
| **XGBoost + All Graph Features** | **38.34 min** | **65.04%** |

**Graph advantage: −30.8% MAE, +14.58pp within-15% accuracy**

### Top 5 Bottleneck Hubs
| Rank | Hub | SLA Breach Rate | Network Risk Share | Intervention |
|------|-----|-----------------|-------------------|--------------|
| #1 | Gurgaon Bilaspur HB | 81.1% | **38.5%** | Parallel route |
| #2 | Bangalore Nelmngla H | 81.9% | 16.2% | Route-type shift |
| #3 | Kolkata Dankuni HB | 84.9% | 3.0% | Facility upgrade |
| #4 | Hyderabad Shamshabad H | 88.6% | 2.3% | Facility upgrade |
| #5 | Bhiwandi Mankoli HB | 90.1% | 10.7% | Parallel route |

**5 hubs account for 70.6% of all network SLA damage.**
Upgrading the top 3 to top-10% performance eliminates 4,266 SLA breaches (4.3% reduction network-wide).

### Network Overview
- **83.8%** of SLA-bound trips missed their deadline
- **73.7%** of all corridors are chronically delayed — systemic OSRM underestimation
- OSRM underestimates actual delivery time by **2.1×** on average

---

## Project Structure

```
delhivery_project/
│
├── data/
│   └── delivery_data.csv              ← raw data (not tracked)
│
├── notebooks/
│   ├── data_pipeline.ipynb         ← data cleaning & feature engineering
│   ├── graph.ipynb            ← directed weighted graph construction
│   ├── bottleneck.ipynb        ← bottleneck & corridor audit
│   ├── baseline_model.ipynb   ← baseline XGBoost ETA model
│   ├── graph_model.ipynb      ← graph-enhanced ETA model (node2vec)
│   └── ftl_carting.ipynb      ← FTL vs Carting decision framework
│    
│
├── streamlit_app/
│   ├── dashboard.py                         ← main dashboard entry point
│   ├── utils.py                       ← shared data loading (cached)
│   └── pages/
│       ├── 1_network_map.py           ← interactive network graph
│       ├── 2_hub_profiles.py          ← hub search and delay profile
│       ├── 3_corridor_audit.py        ← chronic corridor explorer
│       ├── 4_model_comparison.py      ← baseline vs graph model metrics
│       └── 5_ftl_carting.py           ← FTL vs Carting scorecard
│
├── outputs/                           ← generated files (not tracked)
│   ├── clean_all.parquet
│   ├── clean_train.parquet
│   ├── clean_test.parquet
│   ├── graphs.pkl                     ← 6 stratified graphs
│   ├── bottleneck_hubs.parquet
│   ├── corridor_audit.parquet
│   └── models/
│       ├── baseline_model.pkl
│       ├── graph_model.pkl
│       └── ftl_carting_model.pkl
│
├── memo/
│   ├── memo.ipynb
│   ├── strategy_memo.md
│   └── Network_Operations_Strategy_Memo.pdf   ← network operations strategy memo
│
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone and create virtual environment

```bash
git clone https://github.com/gogoi-anuraj/delhivery.git
cd delhivery_project
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add data

Place `delivery_data.csv` in the `data/` folder.
Download from the dataset link provided in the problem statement.

---

## Run Order

Run notebooks **in sequence** — each phase depends on outputs from the previous one.

| Step | Notebook | Output |
|------|----------|--------|
| 1 | `data_pipeline.ipynb` | `clean_all.parquet`, `clean_train.parquet`, `clean_test.parquet` |
| 2 | `graph.ipynb` | `graphs.pkl` (6 stratified graphs) |
| 3 | `bottleneck.ipynb` | `bottleneck_hubs.parquet`, `corridor_audit.parquet` |
| 4 | `baseline_model.ipynb` | `baseline_model.pkl` |
| 5 | `graph_model.ipynb` | `graph_model.pkl` |
| 6 | `ftl_carting.ipynb` | `ftl_carting_model.pkl` |
| 7 | `memo.ipynb` | `strategy_memo.md`, network graph |

```bash
cd notebooks
jupyter notebook
```

---

## Streamlit Dashboard

```bash
cd streamlit_app
streamlit run dashboard.py
```

Opens at `http://localhost:8501`

**Five pages:**
-  Network Map — interactive graph with bottleneck hubs highlighted
-  Hub Profiles — search any hub for delay profile and intervention
-  Corridor Audit — filter and explore chronically delayed corridors
-  Model Comparison — baseline vs graph-enhanced ETA performance
-  FTL vs Carting — route-type decision scorecard

---

## Methodology

### Phase 1 — Graph Construction
- Directed weighted graph: 1,657 nodes, 2,783 edges
- Edge weight = **median segment_factor** per corridor (actual/OSRM ratio)
- 6 stratified graphs: main, FTL, Carting, night, peak_evening, day
- Stratification justified by distinct delay profiles across route types and time windows

### Phase 2 — Bottleneck Audit
- **Betweenness centrality** — structural chokepoints (weighted, normalised)
- **In/out-degree** — hub connectivity
- **Clustering coefficient** — regional embeddedness
- **SLA breach ranking** by `total_cutoff_score` (sum of cutoff_factor per hub)
- Data-driven weights via correlation with SLA damage (betweenness: 95.1%)
- **2,052 chronic corridors** (73.7%) — systemic OSRM underestimation confirmed

### Phase 3a — Baseline ETA Model
- XGBoost on 11 tabular features (OSRM predictions, route type, time-of-day)
- Log-transformed target to handle right skew (skewness 2.08 → 0.28)
- TimeSeriesSplit CV confirms no overfitting (CV MAE 58.62 ± 7.47)

### Phase 3b — Graph-Enhanced ETA Model
- **node2vec** embeddings (dimensions=64, walks=200, p=1, q=2)
  - q=2 biases toward global exploration — captures national hub roles
  - All 1,657 nodes embedded, zero missing
- Explicit graph metrics: betweenness, clustering, in/out-degree per hub
- Corridor-level features: median factor, mean factor, std, CV, trip count
- 154 total features vs 11 baseline
- **Graph advantage: MAE −30.8%, within-15% +14.58pp**

### Phase 3c — FTL vs Carting Framework
- Standard classifier achieves 99% accuracy — trivially learns distance threshold, not a trade-off
- Scorecard approach on 68 hubs with both route types (≥10 trips each)
- Distance-normalised comparison: time per km (min/km)
- SHAP-explained recommendations — betweenness 8th most important feature
- Three-condition rule: time efficiency, delay factor, breach rate

### Phase 4 — Strategy Memo
- Top 5 hub profiles with corridor-specific interventions
- Upgrade impact: 4,266 fewer breaches, 4.3% reduction, 8.9% risk recovered
- Written for an operations leader — no raw model outputs


---

## Dependencies

```
pandas
numpy
networkx
matplotlib
seaborn
plotly
scikit-learn
xgboost
node2vec
shap
pyarrow
streamlit
pyvis
```

Full list in `requirements.txt`.

---

## Grading Criteria (PS)

| Criterion | How addressed |
|-----------|--------------|
| Technical rigor | Log transform justified, TimeSeriesSplit CV, data-driven weights via correlation |
| Analytical depth | 73.7% chronic corridor finding, Bhiwandi ranking explained, cutoff_factor decoded |
| Business translation | Strategy memo in ops leader language, no raw model outputs |
| Creativity | Streamlit dashboard, node2vec on directed weighted graph, scorecard vs classifier |

---
> This project has been done as a part of the Summer Projects, 2026 conducted by the Consulting & Analytics Club, IIT Guwahati

*Analysis period: Sep 12 – Oct 3, 2018 | 142,502 clean trip segments*
*Graph: 1,657 nodes, 2,783 edges | node2vec: dimensions=64, walks=200* 
