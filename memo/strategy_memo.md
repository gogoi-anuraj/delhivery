# Network Operations Strategy Memo

**TO:** Head of Network Operations, Delhivery
**FROM:** Data Science & Strategy Team
**DATE:** May 2026
**RE:** Graph-Based Network Intelligence - Bottleneck Analysis & Action Plan

---

## Situation

Analysis of 142,502 delivery segments across 1,657 hubs over 22 days
reveals a concentrated problem: **five hubs are responsible for 70.6%
of all SLA damage across the network.** Of 118,708 SLA-bound trips,
99,512 (83.8%) missed their delivery deadline. This is not a random
distribution - it is structurally concentrated and actionable.

A second finding compounds the problem: OSRM, the routing engine
Delhivery uses to estimate delivery times, underestimates actual
delivery time by an average of 2.1x across all corridors. 73.7% of
all corridors are chronically delayed - meaning the gap between
promised and actual delivery is systemic, not isolated.

---

## The Five Hubs Requiring Immediate Attention

Our analysis combines structural graph analysis (which hubs are
chokepoints in the network) with SLA breach contribution (which hubs
cause the most actual damage) to produce a bottleneck score for all
1,657 hubs.

| Rank | Hub | SLA Breach Rate | Network Risk Share | Intervention |
|------|-----|-----------------|-------------------|--------------|
| #1 | Gurgaon Bilaspur HB | 81.1% | **38.5%** | Parallel route |
| #2 | Bangalore Nelmngla H | 81.9% | 16.2% | Route-type shift |
| #3 | Kolkata Dankuni HB | 84.9% | 3.0% | Facility upgrade |
| #4 | Hyderabad Shamshabad H | 88.6% | 2.3% | Facility upgrade |
| #5 | Bhiwandi Mankoli HB | 90.1% | 10.7% | Parallel route |

**Gurgaon alone accounts for 38.5% of network-wide SLA damage.**
With betweenness centrality of 0.233 — the highest in the network —
it sits on the shortest path between more hub pairs than any other
facility. Delays here cascade across the entire network.

---

## Recommended Interventions

### Hub #1 : Gurgaon Bilaspur HB: Parallel Route
Gurgaon's breach rate (81.1%) is already among the best-performing
large hubs in the network. The problem is volume, not operations.
22,275 SLA-bound trips pass through this hub in 22 days - more than
double any other hub. **Recommendation:** Create parallel inter-city
corridors via Manesar and Faridabad to redistribute 20-30% of
Gurgaon's FTL volume. This does not require facility investment -
only route planning.

### Hub #2 : Bangalore Nelmngla H: Route-Type Shift
Bangalore's three worst outgoing corridors are all internal city hops
(KH Road 2.33x, Whitefield 2.0x, Peenya 1.88x). A national sorting
hub is being asked to do last-mile city delivery. **Recommendation:**
Shift Bengaluru city corridors from FTL to Carting. Our FTL vs
Carting framework confirms Bangalore as a clear Carting candidate for
city hops - breach rate drops significantly. Estimated SLA breach
reduction for city corridors: 15-20%.

### Hub #3 : Kolkata Dankuni HB: Facility Upgrade
Kolkata's incoming feeder routes are catastrophically delayed -
Ranaghat (11.6x), Helencha (11.6x), Midnapore (7.5x). These are not
road congestion issues - factors above 10x indicate facility dwell
time at Kolkata itself. **Recommendation:** Increase unloading dock
capacity and staffing at Dankuni. Night breach rate (85.5%) is
marginally worse than day (84.6%), suggesting a scheduling gap during
evening receiving windows.

### Hub #4 : Hyderabad Shamshabad H: Facility Upgrade
Night breach rate of 90.1% vs day rate of 87.1% is a clear
night-shift signal. Incoming corridors from Tolichowki (2.64x) and
Uppal (2.64x) are delayed regardless of time of day - the bottleneck
is inside the facility. **Recommendation:** Add night-shift dock staff
and extend facility operating hours to 24/7. Expected breach rate
improvement: 3-5 percentage points within 90 days.

### Hub #5 : Bhiwandi Mankoli HB: Parallel Route
Bhiwandi receives high-volume Mumbai feeders — Mumbai Hub (171 trips,
2.55x), Chandivali (238 trips, 2.48x), Mira Road outgoing (148
trips, 2.44x). The 90.1% breach rate is the highest among the top 5.
**Recommendation:** Create direct Mumbai to destination corridors
bypassing Bhiwandi for the highest-volume flows. This decongests
Bhiwandi and reduces transit hops for Mumbai shipments simultaneously.

---

## Impact If Top 3 Hubs Are Upgraded

Upgrading Gurgaon, Bangalore, and Kolkata to the performance level
of Delhivery's top-10% hubs (68.9% breach rate):

- **4,266 fewer SLA breaches** in an equivalent 22-day window
- **4.3% reduction in late deliveries** network-wide
- **8.9% of total SLA risk recovered** (2,776,266 cutoff points)

The 4.3% figure is honest - Gurgaon and Bangalore are already
well-operated. The gain comes from route diversification reducing
absolute volume at these hubs, not from fixing poor operations.
Kolkata has the most direct operational improvement headroom.

---

## Smarter ETA Predictions - What Changes

Our graph-enhanced ETA model reduces prediction error by 30.8%:

| Model | MAE | Within 15% of actual |
|-------|-----|----------------------|
| Current OSRM baseline | 55.45 min | 50.5% of trips |
| Graph-enhanced model | 38.34 min | 65.0% of trips |

65% of delivery promises will now be within 15% of actual delivery
time, up from 50.5%. The model learns corridor-specific delay
patterns - it knows that Gurgaon to Kanpur runs at 1.85x OSRM, not
the network average.

---

## Recommended Actions This Week

1. **Route planning team:** Model two parallel corridors from NCR
   bypassing Gurgaon - Manesar and Faridabad are the recommended
   anchor points based on network graph position.

2. **Bangalore operations:** Audit which city-delivery FTL contracts
   can be converted to Carting in Q3. Target: KH Road, Whitefield,
   Peenya corridors first.

3. **Kolkata facility team:** Commission a dock capacity audit at
   Dankuni. Focus on evening receiving window (6-10 PM) where feeder
   delays from Ranaghat and Helencha concentrate.

4. **Hyderabad operations:** Extend facility operating hours and add
   night-shift receiving staff. Review Tolichowki and Uppal feeder
   schedules.

5. **Technology team:** Deploy the graph-enhanced ETA model to
   replace OSRM estimates for customer-facing delivery promises on
   the top 50 corridors by volume.

---

*Analysis based on 142,502 trip segments, Sep 12 - Oct 3 2018.
Graph model uses node2vec embeddings on a 1,657-node directed
network. FTL vs Carting framework based on 68 hubs with observed
data for both route types. All findings reproducible from the
accompanying codebase.*
