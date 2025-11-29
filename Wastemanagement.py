
# Waste Management Digital IT Dashboard (Single-File Streamlit App)
# -----------------------------------------------------------------
# How to run:
#   pip install streamlit pandas altair plotly numpy
#   streamlit run app.py
#
# Notes:
# - Data below is synthetic for demonstration. Replace with CPCB/ERP/PLM/DAM connectors.
# - The app shows all dashboards in one workflow with a sidebar selector:
#     Landing, Mandatory Compliance, Alerts & Thresholds, Inventory Management,
#     EPR Tracking, Eco‑Design & Substance Registry, Production Communication,
#     Marketing & Sales.

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime

# Try to import Plotly. If missing, we'll degrade gracefully.
PLOTLY_AVAILABLE = True
try:
    import plotly.graph_objects as go
except Exception:
    PLOTLY_AVAILABLE = False

# -----------------------------
# Synthetic Data (Demo Only)
# -----------------------------
top_kpis = {
    "complianceScore": 76,
    "openRegChanges": 9,
    "eprFulfilment": {"plastic": 82, "ewaste": 68, "battery": 74},
    "nonCompliantStockValue": 1.9,      # INR Crores
    "nextFilingDueDays": 12,
    "alertBacklog": {"critical": 3, "high": 7, "medium": 15}
}

regulatory_feed = [
    {"id": "PWM-2025-13", "title": "Plastic Waste Mgmt: ↑ Min recycled content to 20% by FY26",
     "effective": "2025-12-31", "deadline": "2026-03-31", "severity": "high", "material": "Plastic"},
    {"id": "EWR-2025-07", "title": "E‑Waste Rules: Mandatory UID per device category",
     "effective": "2026-01-15", "deadline": "2026-06-30", "severity": "medium", "material": "E‑Waste"},
    {"id": "BWR-2025-02", "title": "Battery Waste: Extended collection targets (+5%)",
     "effective": "2026-03-01", "deadline": "2026-07-31", "severity": "high", "material": "Battery"},
    {"id": "PWM-2025-15", "title": "PVC label ban in food-contact packaging",
     "effective": "2026-02-28", "deadline": "2026-05-31", "severity": "critical", "material": "Plastic"},
]

impact_by_sku = [
    {"sku":"BEV-P-001", "product":"Bottle 1L PET", "rulesAffected":2, "risk":"medium",
     "recycledRequired":20, "currentRecycled":12},
    {"sku":"FOOD-P-007", "product":"Snack Pouch (multi-layer)", "rulesAffected":3, "risk":"high",
     "recycledRequired":20, "currentRecycled":5},
    {"sku":"ELEC-E-019", "product":"Home Router", "rulesAffected":1, "risk":"medium",
     "traceabilityUID":True},
    {"sku":"BATT-L-003", "product":"Li‑ion pack 2Ah", "rulesAffected":2, "risk":"high",
     "collectionTarget":45, "currentCollection":35},
]

epr_waterfall_plastic = [
    {"stage":"Obligation FY25", "amount": 1800},
    {"stage":"Collections", "amount": -1200},
    {"stage":"Certified Recycling", "amount": -300},
    {"stage":"Net Gap", "amount": 300},
]

inventory_scatter = [
    {"sku":"RM-PET-01", "class":"A", "leadTime":12, "daysOfCover":18},
    {"sku":"RM-PVC-02", "class":"A", "leadTime":20, "daysOfCover":10},
    {"sku":"PKG-Label-01", "class":"B", "leadTime":9, "daysOfCover":22},
    {"sku":"RM-ALU-03", "class":"C", "leadTime":25, "daysOfCover":35},
    {"sku":"RM-GLASS-05", "class":"B", "leadTime":15, "daysOfCover":17},
]

threshold_breaches_by_site = [
    {"site":"Pune", "critical":1, "high":3, "medium":5},
    {"site":"Chennai", "critical":2, "high":2, "medium":4},
    {"site":"Kolkata", "critical":0, "high":1, "medium":6},
]

epr_trend = [
    {"month":"Apr", "plastic":68, "ewaste":60, "battery":61},
    {"month":"May", "plastic":70, "ewaste":61, "battery":62},
    {"month":"Jun", "plastic":72, "ewaste":63, "battery":63},
    {"month":"Jul", "plastic":75, "ewaste":64, "battery":66},
    {"month":"Aug", "plastic":78, "ewaste":65, "battery":69},
    {"month":"Sep", "plastic":80, "ewaste":66, "battery":71},
    {"month":"Oct", "plastic":82, "ewaste":68, "battery":74},
]

material_library = [
    {"material":"PET", "recyclability":"High", "ban":"No", "minRecycled":20, "availability":"Good"},
    {"material":"PVC", "recyclability":"Low", "ban":"Food-contact labels: ban", "minRecycled":0, "availability":"Good"},
    {"material":"PP", "recyclability":"Medium", "ban":"No", "minRecycled":15, "availability":"Moderate"},
]

traceability_readiness = [
    {"sku":"ELEC-E-019", "ready":"Yes", "completeness":92, "action":"Push to DAM"},
    {"sku":"FOOD-P-007", "ready":"Partial", "completeness":68, "action":"Collect UID mapping"},
]

alerts_list = [
    {"id":"AL-1001", "title":"PVC label detected in food-contact SKU", "severity":"critical",
     "owner":"Compliance", "etaDays":7, "state":"Open"},
    {"id":"AL-1002", "title":"Battery collection shortfall (5%)", "severity":"high",
     "owner":"Ops", "etaDays":12, "state":"Assigned"},
    {"id":"AL-1003", "title":"E‑Waste UID data gaps", "severity":"medium",
     "owner":"IT/Traceability", "etaDays":20, "state":"Open"},
]

# -----------------------------
# Helper / Domain Functions
# -----------------------------
def days_to_deadline(deadline_str: str) -> int:
    import datetime as _dt
    deadline = _dt.datetime.strptime(deadline_str, '%Y-%m-%d').date()
    today = _dt.date.today()
    return max(0, (deadline - today).days)

timeline_rules = [{"rule": r["id"], "daysToDeadline": days_to_deadline(r["deadline"])} for r in regulatory_feed]

def simulate(material_from, material_to, recycled_pct, lead_time_days, traceability, base_cost_per_unit=10):
    """Eco‑Design What‑If: compliance, cost delta, availability risk, EPR gap reduction."""
    compliance_target = 20
    material_boost = 12 if (material_from=='PVC' and material_to=='PET') else 4
    compliance_score = min(100, 60 + material_boost + max(0, recycled_pct - compliance_target))

    material_cost_factor = 1.08 if material_to=='PET' else 1.0
    traceability_cost = 0.02 if traceability else 0
    new_cost = base_cost_per_unit * material_cost_factor * (1 + traceability_cost)
    cost_delta_pct = round(((new_cost - base_cost_per_unit)/base_cost_per_unit)*100)

    base_risk = 20
    lead_risk = max(0, (lead_time_days - 10) * 2)
    recycled_risk = max(0, (recycled_pct - compliance_target) * 0.8)
    availability_risk = min(95, base_risk + lead_risk + recycled_risk)

    epr_gap_reduction = round((recycled_pct - compliance_target) * 5)

    return {
        'complianceScore': compliance_score,
        'costDeltaPct': cost_delta_pct,
        'availabilityRisk': availability_risk,
        'eprGapReduction': epr_gap_reduction
    }

def mcda_score(metrics: dict, weights: dict) -> int:
    """MCDA scoring; cost is lower-better (invert)."""
    normalized = {
        'compliance': metrics['compliance'],
        'cost': (100 - metrics['cost']),
        'availability': metrics['availability'],
        'recyclability': metrics['recyclability'],
        'traceability': metrics['traceability']
    }
    return round(sum(normalized[k] * weights[k] for k in weights))

# -----------------------------
# Render Functions (Dashboards)
# -----------------------------
def render_landing():
    st.markdown("## Global Landing")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('Compliance Score', f"{top_kpis['complianceScore']}%")
    with col2:
        st.metric('Open Regulatory Changes (90d)', top_kpis['openRegChanges'],
                  help='Monitor new CPCB/EPR updates')
    with col3:
        e = top_kpis['eprFulfilment']
        st.metric('EPR Fulfilment (P/E/B)', f"{e['plastic']}% / {e['ewaste']}% / {e['battery']}%")
    with col4:
        st.metric('Non‑Compliant Stock Value',
                  f"₹{top_kpis['nonCompliantStockValue']} Cr",
                  delta=f"Next filing in {top_kpis['nextFilingDueDays']} days")

    st.divider()

    st.subheader('Regulatory Change Feed (India EPR)')
    rf_df = pd.DataFrame(regulatory_feed)
    st.dataframe(rf_df, use_container_width=True)

    st.subheader('Waste Flow (approx) – Collection → Processing (Stacked bars)')
    flow_df = pd.DataFrame([
        {'label':'Plastic','collected':1200,'recycled':300,'landfill':120},
        {'label':'E‑Waste','collected':180,'recycled':120,'landfill':15},
        {'label':'Battery','collected':220,'recycled':160,'landfill':10},
    ])
    flow_m = flow_df.melt('label', var_name='stage', value_name='tons')
    chart = alt.Chart(flow_m).mark_bar().encode(
        x=alt.X('label:N', title='Category'),
        y=alt.Y('tons:Q', stack='normalize', title='Share'),
        color=alt.Color('stage:N', scale=alt.Scale(range=['#38bdf8','#22c55e','#ef4444']))
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

    # ---- Sankey for Waste Flow ----
    st.subheader('Waste Flow Sankey – Generation → Processing Outcomes')
    if not PLOTLY_AVAILABLE:
        st.warning(
            "Plotly is not installed, so the Sankey cannot be rendered. "
            "Install Plotly and rerun: `pip install plotly`."
        )
    else:
        # Define nodes and colors
        nodes = ["Plastic", "E‑Waste", "Battery", "Recycle", "Reuse", "Co‑process", "Landfill"]
        node_colors = [
            "#38bdf8",  # Plastic
            "#f59e0b",  # E‑Waste
            "#22c55e",  # Battery
            "#22c55e",  # Recycle
            "#60a5fa",  # Reuse
            "#a78bfa",  # Co‑process
            "#ef4444"   # Landfill
        ]
        # Flows (synthetic; sums match the stacked bars above)
        # Index map: 0:Plastic, 1:E‑Waste, 2:Battery, 3:Recycle, 4:Reuse, 5:Co‑process, 6:Landfill
        source = [
            0, 0, 0, 0,      # Plastic -> Recycle, Reuse, Co‑process, Landfill
            1, 1, 1,         # E‑Waste -> Recycle, Reuse, Landfill
            2, 2, 2          # Battery -> Recycle, Reuse, Landfill
        ]
        target = [
            3, 4, 5, 6,      # Plastic flows
            3, 4, 6,         # E‑Waste flows
            3, 4, 6          # Battery flows
        ]
        value = [
            300, 280, 500, 120,   # Plastic totals = 1200
            120, 45, 15,          # E‑Waste totals = 180
            160, 50, 10           # Battery totals = 220
        ]

        import plotly.graph_objects as go  # safe (PLOTLY_AVAILABLE checked)
        sankey_fig = go.Figure(
            go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=18, thickness=24,
                    line=dict(color="rgba(255,255,255,0.3)", width=1),
                    label=nodes,
                    color=node_colors
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=value,
                    color=[
                        "#22c55e", "#60a5fa", "#a78bfa", "#ef4444",  # Plastic links
                        "#22c55e", "#60a5fa", "#ef4444",             # E‑Waste links
                        "#22c55e", "#60a5fa", "#ef4444"              # Battery links
                    ]
                )
            )
        )
        sankey_fig.update_layout(
            template="plotly_dark",
            height=420,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(sankey_fig, use_container_width=True)
    # ---- End Sankey ----

    colA, colB, colC = st.columns(3)
    with colA:
        st.subheader('EPR Gap – Plastic (Waterfall)')
        if not PLOTLY_AVAILABLE:
            st.info("Plotly not installed. Install Plotly to see the waterfall chart (`pip install plotly`).")
        else:
            wf = pd.DataFrame(epr_waterfall_plastic)
            fig = go.Figure(go.Waterfall(
                orientation='v',
                measure=['absolute','relative','relative','total'],
                x=wf['stage'],
                y=wf['amount'],
                connector={'line': {'color': 'rgba(255,255,255,0.4)'}},
            ))
            fig.update_layout(height=300, margin=dict(l=10,r=10,t=30,b=10), template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)

    with colB:
        st.subheader('Inventory Health – Days of Cover vs Lead Time')
        inv = pd.DataFrame(inventory_scatter)
        chart2 = alt.Chart(inv).mark_circle(size=90).encode(
            x=alt.X('leadTime:Q', title='Lead Time (days)'),
            y=alt.Y('daysOfCover:Q', title='Days of Cover'),
            color=alt.Color('class:N',
                            scale=alt.Scale(domain=['A','B','C'],
                                            range=['#38bdf8','#22c55e','#f59e0b'])),
            tooltip=['sku','leadTime','daysOfCover','class']
        ).properties(height=300)
        st.altair_chart(chart2, use_container_width=True)

    with colC:
        st.subheader('Eco‑Design Spotlight (MCDA Radar)')
        if not PLOTLY_AVAILABLE:
            st.info("Plotly not installed. Install Plotly to see the radar chart (`pip install plotly`).")
        else:
            radar_df = pd.DataFrame([
                {'metric':'Compliance','A':72,'B':88},
                {'metric':'Cost (inverse)','A':60,'B':68},
                {'metric':'Availability','A':70,'B':62},
                {'metric':'Recyclability','A':55,'B':82},
                {'metric':'Traceability','A':50,'B':80},
            ])
            fig2 = go.Figure()
            fig2.add_trace(go.Scatterpolar(r=radar_df['A'], theta=radar_df['metric'],
                                           fill='toself', name='Option A',
                                           line=dict(color='#38bdf8')))
            fig2.add_trace(go.Scatterpolar(r=radar_df['B'], theta=radar_df['metric'],
                                           fill='toself', name='Option B',
                                           line=dict(color='#22c55e')))
            fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,100])),
                               showlegend=True, height=300, template='plotly_dark')
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader('Alert Backlog by Site')
    ab = pd.DataFrame(threshold_breaches_by_site)
    ab_m = ab.melt('site', var_name='severity', value_name='count')
    chart3 = alt.Chart(ab_m).mark_bar().encode(
        x=alt.X('site:N'), y='count:Q',
        color=alt.Color('severity:N',
                        scale=alt.Scale(domain=['critical','high','medium'],
                                        range=['#ef4444','#f59e0b','#38bdf8']))
    ).properties(height=300)
    st.altair_chart(chart3, use_container_width=True)

def render_compliance():
    st.markdown('## Mandatory Compliance – Regulatory Intelligence & Alerting')

    st.subheader('Regulatory Feed & Watchlist')
    rf = pd.DataFrame(regulatory_feed)
    st.dataframe(rf, use_container_width=True)

    st.subheader('Impact Assessment by SKU & Packaging')
    impact = pd.DataFrame(impact_by_sku)
    st.dataframe(impact, use_container_width=True)

    st.subheader('Compliance Readiness & Deadlines (days to deadline)')
    tr = pd.DataFrame(timeline_rules)
    chart = alt.Chart(tr).mark_bar(color='#ef4444').encode(
        x=alt.X('rule:N', title='Rule'),
        y=alt.Y('daysToDeadline:Q', title='Days')
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

    st.subheader('Reporting & Filings – CPCB Submission Calendar')
    cal = pd.DataFrame([
        {'month':'Nov','Plastic':'Submitted','E‑Waste':'Planned','Battery':'Planned','Status':'Submitted'},
        {'month':'Dec','Plastic':'Draft','E‑Waste':'Planned','Battery':'Planned','Status':'Pending'},
        {'month':'Jan','Plastic':'Planned','E‑Waste':'Draft','Battery':'Planned','Status':'Pending'},
        {'month':'Feb','Plastic':'Planned','E‑Waste':'Planned','Battery':'Draft','Status':'Pending'},
    ])
    st.dataframe(cal, use_container_width=True)

def render_alerts():
    st.markdown('## Alerts & Thresholds')

    st.subheader('Threshold Configuration & Governance')
    col1, col2, col3 = st.columns(3)
    with col1:
        recycled_min = st.number_input('Min Recycled %', value=20)
    with col2:
        collection_target = st.number_input('Collection Target %', value=75)
    with col3:
        uid_comp = st.number_input('UID Data Completeness %', value=90)
    st.caption('Changing thresholds will typically affect alert volume; wire to policy store in production.')

    st.subheader('Active Alerts by Site & Severity')
    ab = pd.DataFrame(threshold_breaches_by_site)
    ab_m = ab.melt('site', var_name='severity', value_name='count')
    chart = alt.Chart(ab_m).mark_bar().encode(
        x='site:N', y='count:Q',
        color=alt.Color('severity:N',
                        scale=alt.Scale(domain=['critical','high','medium'],
                                        range=['#ef4444','#f59e0b','#38bdf8']))
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

    st.subheader('Alert Backlog & SLA')
    alerts = pd.DataFrame(alerts_list)
    st.dataframe(alerts, use_container_width=True)

def render_inventory():
    st.markdown('## Inventory Management')

    st.subheader('Raw Materials & Packaging – ABC / Days of Cover vs Lead Time')
    inv = pd.DataFrame(inventory_scatter)
    chart = alt.Chart(inv).mark_circle(size=90).encode(
        x=alt.X('leadTime:Q', title='Lead Time (days)'),
        y=alt.Y('daysOfCover:Q', title='Days of Cover'),
        color=alt.Color('class:N',
                        scale=alt.Scale(domain=['A','B','C'],
                                        range=['#38bdf8','#22c55e','#f59e0b'])),
        tooltip=['sku','leadTime','daysOfCover','class']
    ).properties(height=320)
    st.altair_chart(chart, use_container_width=True)

    st.subheader('Waste Inventory & Segregation')
    waste = pd.DataFrame([
        {'Category':'Plastic','Qty (t)':1200,'Recycled (t)':300,'Landfill (t)':120,'Aging (days)':12},
        {'Category':'E‑Waste','Qty (t)':180,'Recycled (t)':120,'Landfill (t)':15,'Aging (days)':9},
        {'Category':'Battery','Qty (t)':220,'Recycled (t)':160,'Landfill (t)':10,'Aging (days)':7},
    ])
    st.dataframe(waste, use_container_width=True)

    st.subheader('BOM Compliance & Non‑Compliant Stock')
    bom = pd.DataFrame([
        {'SKU':'FOOD-P-007','Old BOM':'PVC label','Compliant BOM':'PET label',
         'Non‑Compliant Stock (₹L)':28,'Plan':'Phase‑out by Jan'},
        {'SKU':'BATT-L-003','Old BOM':'Old separator','Compliant BOM':'Compliant separator',
         'Non‑Compliant Stock (₹L)':12,'Plan':'Rework by Dec'},
    ])
    st.dataframe(bom, use_container_width=True)

def render_epr():
    st.markdown('## EPR Tracking')

    st.subheader('EPR Fulfilment Trend by Category')
    trend = pd.DataFrame(epr_trend)
    trend_m = trend.melt('month', var_name='category', value_name='fulfilment')
    chart = alt.Chart(trend_m).mark_line(point=True).encode(
        x='month:N',
        y=alt.Y('fulfilment:Q', title='%'),
        color=alt.Color('category:N',
                        scale=alt.Scale(domain=['plastic','ewaste','battery'],
                                        range=['#38bdf8','#f59e0b','#22c55e']))
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

    st.subheader('Gap Analysis – Plastic (Waterfall)')
    if not PLOTLY_AVAILABLE:
        st.info("Plotly not installed. Install Plotly to see the waterfall chart (`pip install plotly`).")
    else:
        wf = pd.DataFrame(epr_waterfall_plastic)
        fig = go.Figure(go.Waterfall(orientation='v',
                                     measure=['absolute','relative','relative','total'],
                                     x=wf['stage'], y=wf['amount']))
        fig.update_layout(height=300, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)

    st.subheader('CPCB Reporting Status')
    cal = pd.DataFrame([
        {'Month':'Nov','Status':'Submitted','Error Log':''},
        {'Month':'Dec','Status':'In Progress','Error Log':'Missing UID in 3 SKUs'},
        {'Month':'Jan','Status':'In Progress','Error Log':''},
        {'Month':'Feb','Status':'In Progress','Error Log':''},
    ])
    st.dataframe(cal, use_container_width=True)

def render_ecodesign():
    st.markdown('## Eco‑Design & Substance Registry')

    st.subheader('What‑If Simulator')
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        material_from = st.selectbox('Material From', ['PVC','PET','PP'], index=0)
    with col2:
        material_to = st.selectbox('Material To', ['PET','PP','PVC'], index=0)
    with col3:
        recycled_pct = st.number_input('Recycled %', value=22)
    with col4:
        lead_time_days = st.number_input('Lead Time (days)', value=14)
    with col5:
        traceability = st.selectbox('Traceability (QR/UID)', ['Enabled','Disabled'], index=0) == 'Enabled'

    sim = simulate(material_from, material_to, recycled_pct, lead_time_days, traceability)

    colA, colB = st.columns(2)
    with colA:
        st.metric('Compliance Score', f"{sim['complianceScore']}%")
        st.metric('Availability Risk', f"{sim['availabilityRisk']}%")
    with colB:
        st.metric('Cost Δ', f"{sim['costDeltaPct']}%")
        st.metric('EPR Gap Reduction (est.)', f"{sim['eprGapReduction']} t/month")

    st.subheader('MCDA Scoring – Options')
    weights = {'compliance':0.30,'cost':0.20,'availability':0.15,'recyclability':0.20,'traceability':0.15}
    optionA = {'compliance':72,'cost':40,'availability':70,'recyclability':55,'traceability':50}
    optionB = {
        'compliance':sim['complianceScore'],
        'cost':min(100, 50 + sim['costDeltaPct']),
        'availability':100 - sim['availabilityRisk'],
        'recyclability':min(100, 60 + (recycled_pct-20)*2),
        'traceability': 85 if traceability else 60
    }
    scoreA = mcda_score(optionA, weights)
    scoreB = mcda_score(optionB, weights)
    st.write(f"**MCDA Score (Option A):** {scoreA} | **MCDA Score (Option B):** {scoreB}")

    if not PLOTLY_AVAILABLE:
        st.info("Plotly not installed. Install Plotly to see the radar chart (`pip install plotly`).")
    else:
        radar_df = pd.DataFrame([
            {'metric':'Compliance','A': optionA['compliance'], 'B': optionB['compliance']},
            {'metric':'Cost (inverse)','A': 100-optionA['cost'], 'B': 100-optionB['cost']},
            {'metric':'Availability','A': optionA['availability'], 'B': optionB['availability']},
            {'metric':'Recyclability','A': optionA['recyclability'], 'B': optionB['recyclability']},
            {'metric':'Traceability','A': optionA['traceability'], 'B': optionB['traceability']},
        ])
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=radar_df['A'], theta=radar_df['metric'],
                                      fill='toself', name='Option A', line=dict(color='#38bdf8')))
        fig.add_trace(go.Scatterpolar(r=radar_df['B'], theta=radar_df['metric'],
                                      fill='toself', name='Option B', line=dict(color='#22c55e')))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,100])),
                          showlegend=True, height=320, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)

    st.subheader('Material Library & Substance Registry (Demo)')
    ml = pd.DataFrame(material_library)
    st.dataframe(ml, use_container_width=True)

    st.subheader('Digital Traceability Readiness')
    tr = pd.DataFrame(traceability_readiness)
    st.dataframe(tr, use_container_width=True)

def render_production():
    st.markdown('## Production Unit Communication')

    st.subheader('Controlled Engineering Change Orders (ECO)')
    eco = pd.DataFrame([
        {'ECO#':'ECO-9001','SKU':'FOOD-P-007','State':'Approved','Age (days)':5,'Owner':'R&D'},
        {'ECO#':'ECO-9002','SKU':'BATT-L-003','State':'Review','Age (days)':9,'Owner':'QA'},
        {'ECO#':'ECO-9003','SKU':'ELEC-E-019','State':'Released','Age (days)':2,'Owner':'Production'},
    ])
    st.dataframe(eco, use_container_width=True)

    st.subheader('Manufacturing Instruction Update & Quality Checks')
    mi = pd.DataFrame([
        {'Instruction':'New packaging assembly (PET label)','Site':'Pune','Checklist':'10 steps','Completion':'80%'},
        {'Instruction':'Battery recycled content QC','Site':'Chennai','Checklist':'7 steps','Completion':'71%'},
    ])
    st.dataframe(mi, use_container_width=True)

    st.subheader('BOM Update & Rollout')
    bom = pd.DataFrame([
        {'SKU':'FOOD-P-007','Plant':'Pune','BOM Compliance %':92,'Obsolete Material Usage (trend)':'↓'},
        {'SKU':'BATT-L-003','Plant':'Chennai','BOM Compliance %':88,'Obsolete Material Usage (trend)':'↓'},
    ])
    st.dataframe(bom, use_container_width=True)

def render_marketing():
    st.markdown('## Marketing & Sales Communication')

    st.subheader('Compliance Data Sheet Generation')
    cds = pd.DataFrame([
        {'SKU':'FOOD-P-007','Sheet Version':'v3.1','Coverage':'Updated claims, end‑of‑life','Status':'Ready'},
        {'SKU':'ELEC-E-019','Sheet Version':'v1.8','Coverage':'UID, take‑back scheme','Status':'Ready'},
    ])
    st.dataframe(cds, use_container_width=True)

    st.subheader('Digital Asset Management (DAM) – Labels & Web Copy')
    dam = pd.DataFrame([
        {'Asset':'Label artwork','SKU':'FOOD-P-007','Version':'v3','Approval':'Approved'},
        {'Asset':'Web product page','SKU':'ELEC-E-019','Version':'v12','Approval':'Pending Legal'},
    ])
    st.dataframe(dam, use_container_width=True)

    st.subheader('Sales Enablement – Talking Points & Data Cards')
    sales = pd.DataFrame([
        {'SKU':'FOOD-P-007','Talking Points':'PET label, ≥20% recycled content, compliant disposal',
         'Verification':'CPCB filing ID: PWM‑2025‑13'},
        {'SKU':'ELEC-E-019','Talking Points':'UID traceability, take‑back partner network',
         'Verification':'E‑Waste UID pilot: #EWR‑2025‑07'},
    ])
    st.dataframe(sales, use_container_width=True)

# -----------------------------
# App Shell (Single Workflow)
# -----------------------------
st.set_page_config(page_title='Waste Management Tool', layout='wide')
with st.sidebar:
    st.title('Waste Mgmt Tool')
    st.selectbox('Period', ['FY 2025','FY 2026'], key='period')
    st.selectbox('Business Unit', ['All BUs','Consumer','Industrial'], key='bu')
    st.selectbox('Site', ['All Sites','Pune','Chennai','Kolkata'], key='site')
    st.selectbox('Material', ['All Materials','Plastic','E‑Waste','Battery'], key='material')
    st.caption('Synthetic demo data')
    st.markdown("---")
    view = st.radio(
        "Choose dashboard",
        [
            "Landing",
            "Mandatory Compliance",
            "Alerts & Thresholds",
            "Inventory Management",
            "EPR Tracking",
            "Eco‑Design & Substance Registry",
            "Production Communication",
            "Marketing & Sales"
        ],
        index=0
    )

# Render selected view
if view == "Landing":
    render_landing()
elif view == "Mandatory Compliance":
    render_compliance()
elif view == "Alerts & Thresholds":
    render_alerts()
elif view == "Inventory Management":
    render_inventory()
elif view == "EPR Tracking":
    render_epr()
elif view == "Eco‑Design & Substance Registry":
    render_ecodesign()
elif view == "Production Communication":
    render_production()
elif view == "Marketing & Sales":
