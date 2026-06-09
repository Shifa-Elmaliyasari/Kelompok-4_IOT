import streamlit as st

import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import time

# ─── CONFIG ───────────────────────────────────────────────────────────────────
DB_PATH = r"D:\Kuliah\DOC\Semester 6\IOT\TUGAS\Tugas Kelompok\Projek UAS\room_monitor_esp32\sensor_data.db"

st.set_page_config(
    page_title="Room Comfort Monitor",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Import font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Background */
    .stApp { background-color: #0f1117; }
    .main .block-container { padding: 1.5rem 2rem; max-width: 1400px; }

    /* Header */
    .dash-header {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
        border: 1px solid #2d3561;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .dash-title { font-size: 1.6rem; font-weight: 700; color: #e2e8f0; margin: 0; }
    .dash-subtitle { font-size: 0.85rem; color: #64748b; margin: 0.2rem 0 0; }
    .dash-time { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: #38bdf8; }

    /* Metric cards */
    .metric-card {
        background: #1a1f2e;
        border: 1px solid #2d3561;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 12px 12px 0 0;
    }
    .metric-card.temp::before  { background: linear-gradient(90deg, #f97316, #fb923c); }
    .metric-card.humid::before { background: linear-gradient(90deg, #38bdf8, #7dd3fc); }
    .metric-card.light::before { background: linear-gradient(90deg, #facc15, #fde68a); }
    .metric-card.sound::before { background: linear-gradient(90deg, #a78bfa, #c4b5fd); }
    .metric-card.gas::before   { background: linear-gradient(90deg, #4ade80, #86efac); }
    .metric-card.motion::before{ background: linear-gradient(90deg, #f43f5e, #fb7185); }

    .metric-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
    .metric-value { font-size: 2rem; font-weight: 700; color: #e2e8f0; line-height: 1.2; margin: 0.3rem 0; font-family: 'JetBrains Mono', monospace; }
    .metric-unit  { font-size: 1rem; color: #94a3b8; font-weight: 400; }
    .metric-status { font-size: 0.78rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 20px; display: inline-block; margin-top: 0.3rem; }
    .status-ok      { background: #14532d; color: #4ade80; }
    .status-warning { background: #451a03; color: #fb923c; }
    .status-danger  { background: #4c0519; color: #f43f5e; }
    .status-active  { background: #312e81; color: #a78bfa; }
    .status-none    { background: #1e293b; color: #64748b; }

    /* Comfort score */
    .comfort-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
        border: 1px solid #2d3561;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
    }
    .comfort-score { font-size: 4rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
    .comfort-label { font-size: 1rem; color: #94a3b8; margin-top: 0.3rem; }

    /* Alert box */
    .alert-box {
        background: #1a1f2e;
        border: 1px solid #2d3561;
        border-radius: 12px;
        padding: 1rem 1.4rem;
    }
    .alert-item {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.5rem 0;
        border-bottom: 1px solid #1e293b;
        font-size: 0.85rem;
    }
    .alert-item:last-child { border-bottom: none; }
    .alert-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
    .dot-danger  { background: #f43f5e; }
    .dot-warning { background: #fb923c; }
    .dot-ok      { background: #4ade80; }

    /* Section title */
    .section-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 1.5rem 0 0.8rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #1e293b;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #1e293b; }
    [data-testid="stSidebar"] .stSelectbox label { color: #94a3b8; font-size: 0.85rem; }

    /* Hide streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def load_data(hours=4):
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        since = datetime.now() - timedelta(hours=hours)
        df = pd.read_sql_query("""
            SELECT * FROM sensor_readings
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """, conn, params=(since.strftime("%Y-%m-%d %H:%M:%S"),))
        conn.close()  # ← tutup koneksi setelah query
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def load_latest():
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        df = pd.read_sql_query("""
            SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 1
        """, conn)
        conn.close()  # ← tutup koneksi setelah query
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df.iloc[0]
        return None
    except:
        return None

def compute_comfort_score(temp, humid, gas_ppm, lux, sound):
    score = 100

    # Temperature: ideal 22–26°C
    if   temp < 18: score -= 25
    elif temp < 22: score -= 10
    elif temp > 30: score -= 25
    elif temp > 26: score -= 10

    # Humidity: ideal 40–60%
    if   humid < 30: score -= 20
    elif humid < 40: score -= 8
    elif humid > 80: score -= 20
    elif humid > 60: score -= 8

    # Air quality
    if   gas_ppm > 700: score -= 25
    elif gas_ppm > 400: score -= 12

    # Light: ideal 200–500 lux (cafe)
    if   lux < 50:   score -= 10
    elif lux < 200:  score -= 5
    elif lux > 1000: score -= 10

    # Noise: sound analog > 2500 = noisy
    if   sound > 3000: score -= 15
    elif sound > 2500: score -= 8

    return max(0, min(100, score))

def comfort_label(score):
    if score >= 80: return "😊 Sangat Nyaman", "#4ade80"
    if score >= 60: return "🙂 Nyaman",        "#a3e635"
    if score >= 40: return "😐 Cukup",          "#facc15"
    if score >= 20: return "😟 Kurang Nyaman", "#fb923c"
    return "😣 Tidak Nyaman", "#f43f5e"

def get_status(val, thresholds):
    """thresholds: [(limit, label)] sorted ascending, last = default"""
    for limit, label in thresholds:
        if val <= limit:
            return label
    return thresholds[-1][1]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#94a3b8", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor="#1e293b", linecolor="#2d3561", tickformat="%H:%M"),
    yaxis=dict(gridcolor="#1e293b", linecolor="#2d3561"),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#1a1f2e", bordercolor="#2d3561", font_color="#e2e8f0"),
)


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Pengaturan")
    time_range = st.selectbox("Rentang waktu", ["1 jam", "2 jam", "4 jam", "Hari ini", "Semua data"], index=2)
    auto_refresh = st.toggle("Auto-refresh (30 detik)", value=True)
    st.divider()

    st.markdown("### 📋 Ambang Batas Alert")
    temp_max  = 25
    humid_max = st.slider("Kelembaban maks (%)", 60, 95, 80)
    gas_max   = st.slider("Gas maks (ppm)",   300, 1000, 700)

    st.divider()
    st.markdown('<p style="color:#475569;font-size:0.75rem;">ESP32 Room Comfort Monitor<br>IOT Project — UAS 2026</p>', unsafe_allow_html=True)

hours_map = {"1 jam": 1, "2 jam": 2, "4 jam": 4, "Hari ini": 24, "Semua data": 9999}
hours = hours_map[time_range]


# ─── LOAD DATA ────────────────────────────────────────────────────────────────
df      = load_data(hours)
latest  = load_latest()
now_str = datetime.now().strftime("%d %b %Y, %H:%M:%S")


# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
    <div>
        <p class="dash-title">🌡️ Room Comfort Monitor</p>
        <p class="dash-subtitle">IOT Monitoring — Sistem Pemantauan Kenyamanan Ruangan</p>
    </div>
    <div style="text-align:right">
        <div class="dash-time">{now_str}</div>
        <div style="font-size:0.75rem;color:#475569;margin-top:0.2rem">
            {"🟢 " + str(len(df)) + " data points" if not df.empty else "🔴 Tidak ada data"}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if latest is None:
    st.warning("⚠️ Belum ada data di database. Pastikan `serial_to_db.py` sedang berjalan dan ESP32 terhubung.")
    st.stop()


# ─── METRIC CARDS ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Pembacaan Terkini</div>', unsafe_allow_html=True)

t  = latest["temperature"]
h  = latest["humidity"]
l  = latest["lux"]
s  = latest["sound_level"]
g  = latest["gas_ppm"]
m  = latest["motion"]
ts = latest["timestamp"].strftime("%H:%M:%S")

# Suhu: ideal 20–25°C
if t < 20:
    temp_status = "warning"   # terlalu dingin
elif t <= 25:
    temp_status = "ok"        # ideal
elif t <= 30:
    temp_status = "warning"   # hangat
else:
    temp_status = "danger"    # panas

# Kelembaban: ideal 40–60%
if h < 40:
    humid_status = "warning"  # terlalu kering
elif h <= 60:
    humid_status = "ok"       # ideal
elif h <= 75:
    humid_status = "warning"  # lembab
else:
    humid_status = "danger"   # sangat lembab

# Gas: ideal < 350 ppm, waspada 350–700, bahaya > 700
if g < 350:
    gas_status = "ok"         # udara bersih
elif g <= 700:
    gas_status = "warning"    # mulai menurun
else:
    gas_status = "danger"     # buruk

# Sisanya tetap sama
light_status  = "ok" if 200 <= l <= 800 else "warning"
sound_status  = "ok" if s < 2500 else ("warning" if s < 3000 else "danger")
motion_status = "active" if m else "none"

status_labels = {
    "temp":   {"ok": "Normal", "warning": "Hangat", "danger": "Panas!"},
    "humid":  {"ok": "Normal", "warning": "Lembab", "danger": "Sangat Lembab!"},
    "gas":    {"ok": "Bersih", "warning": "Sedang", "danger": "Buruk!"},
    "light":  {"ok": "Ideal", "warning": "Kurang/Terang"},
    "sound":  {"ok": "Tenang", "warning": "Agak Berisik", "danger": "Berisik!"},
    "motion": {"active": "Terdeteksi", "none": "Tidak Ada"},
}

c1, c2, c3 = st.columns(3)
c4, c5, c6 = st.columns(3)

with c1:
    st.markdown(f"""<div class="metric-card temp">
        <div class="metric-label">🌡️ Suhu</div>
        <div class="metric-value">{t:.1f}<span class="metric-unit">°C</span></div>
        <span class="metric-status status-{temp_status}">{status_labels['temp'][temp_status]}</span>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="metric-card humid">
        <div class="metric-label">💧 Kelembaban</div>
        <div class="metric-value">{h:.1f}<span class="metric-unit">%</span></div>
        <span class="metric-status status-{humid_status}">{status_labels['humid'][humid_status]}</span>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div class="metric-card light">
        <div class="metric-label">☀️ Cahaya</div>
        <div class="metric-value">{l:.0f}<span class="metric-unit"> lux</span></div>
        <span class="metric-status status-{light_status}">{status_labels['light'][light_status]}</span>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""<div class="metric-card sound">
        <div class="metric-label">🔊 Suara</div>
        <div class="metric-value">{s}<span class="metric-unit"> lvl</span></div>
        <span class="metric-status status-{sound_status}">{status_labels['sound'][sound_status]}</span>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown(f"""<div class="metric-card gas">
        <div class="metric-label">💨 Kualitas Udara</div>
        <div class="metric-value">{g:.0f}<span class="metric-unit"> ppm</span></div>
        <span class="metric-status status-{gas_status}">{status_labels['gas'][gas_status]}</span>
    </div>""", unsafe_allow_html=True)

with c6:
    st.markdown(f"""<div class="metric-card motion">
        <div class="metric-label">🚶 Gerakan</div>
        <div class="metric-value" style="font-size:1.6rem">{"Ada" if m else "Tidak"}</div>
        <span class="metric-status status-{motion_status}">{status_labels['motion'][motion_status]}</span>
    </div>""", unsafe_allow_html=True)


# ─── COMFORT SCORE + ALERTS ───────────────────────────────────────────────────
st.markdown('<div class="section-title">🎯 Indeks Kenyamanan & Peringatan</div>', unsafe_allow_html=True)

col_score, col_gauge, col_alert = st.columns([1, 1.4, 1.6])

score = compute_comfort_score(t, h, g, l, s)
label, color = comfort_label(score)

with col_score:
    st.markdown(f"""<div class="comfort-card">
        <div class="comfort-score" style="color:{color}">{score}</div>
        <div style="font-size:0.7rem;color:#475569;text-transform:uppercase;letter-spacing:0.1em">/ 100 — Comfort Score</div>
        <div style="font-size:1.1rem;margin-top:0.8rem">{label}</div>
        <div style="font-size:0.75rem;color:#475569;margin-top:0.5rem">Update: {ts}</div>
    </div>""", unsafe_allow_html=True)

with col_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "%", "font": {"size": 36, "color": color, "family": "JetBrains Mono"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#475569", "tickfont": {"color": "#475569"}},
            "bar":  {"color": color, "thickness": 0.25},
            "bgcolor": "#1a1f2e",
            "bordercolor": "#2d3561",
            "steps": [
                {"range": [0,  20], "color": "#2d1b1b"},
                {"range": [20, 40], "color": "#2d2010"},
                {"range": [40, 60], "color": "#2d2a10"},
                {"range": [60, 80], "color": "#1a2d10"},
                {"range": [80,100], "color": "#102d1a"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.8, "value": score}
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#94a3b8"),
        margin=dict(l=20, r=20, t=20, b=10),
        height=180,
    )
    st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

with col_alert:
    alerts = []
    if t > temp_max:        alerts.append(("danger",  f"Suhu {t:.1f}°C melebihi {temp_max}°C"))
    if h > humid_max:       alerts.append(("danger",  f"Kelembaban {h:.1f}% melebihi {humid_max}%"))
    if g > gas_max:         alerts.append(("danger",  f"Gas {g:.0f} ppm — kualitas udara buruk"))
    if t > temp_max - 3:    alerts.append(("warning", f"Suhu mendekati batas: {t:.1f}°C"))
    if s > 2500:            alerts.append(("warning", f"Tingkat kebisingan tinggi: {s}"))
    if l < 100:             alerts.append(("warning", f"Pencahayaan terlalu redup: {l:.0f} lux"))
    if m:                   alerts.append(("ok",      "Gerakan aktif terdeteksi di ruangan"))
    if not alerts:          alerts.append(("ok",      "Semua parameter dalam batas normal ✓"))

    items_html = ""
    for level, msg in alerts[:6]:
        dot_class = f"dot-{level}"
        color_msg = "#f43f5e" if level=="danger" else ("#fb923c" if level=="warning" else "#94a3b8")
        items_html += f"""<div class="alert-item">
            <div class="alert-dot {dot_class}"></div>
            <span style="color:{color_msg}">{msg}</span>
        </div>"""

    st.markdown(f"""<div class="alert-box">
        <div style="font-size:0.75rem;font-weight:600;color:#475569;text-transform:uppercase;
                    letter-spacing:0.08em;margin-bottom:0.5rem">⚠️ Status & Peringatan</div>
        {items_html}
    </div>""", unsafe_allow_html=True)


# ─── CHARTS ───────────────────────────────────────────────────────────────────
if df.empty:
    st.info("Belum ada data historis untuk ditampilkan. Tunggu beberapa menit setelah serial_to_db.py berjalan.")
else:
    st.markdown('<div class="section-title">📈 Grafik Historis</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🌡️ Suhu & Kelembaban", "💨 Gas & Cahaya", "🔊 Suara & Gerakan"])

    with tab1:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df["timestamp"], y=df["temperature"],
            name="Suhu (°C)", line=dict(color="#f97316", width=2),
            fill="tozeroy", fillcolor="rgba(249,115,22,0.08)"
        ))
        fig1.add_trace(go.Scatter(
            x=df["timestamp"], y=df["humidity"],
            name="Kelembaban (%)", line=dict(color="#38bdf8", width=2),
            yaxis="y2", fill="tozeroy", fillcolor="rgba(56,189,248,0.08)"
        ))
        fig1.add_hline(y=temp_max, line_dash="dash", line_color="#f43f5e",
                       annotation_text=f"Batas suhu {temp_max}°C", annotation_font_color="#f43f5e")
        fig1.update_layout(
            **PLOTLY_LAYOUT, height=300,
            yaxis=dict(title="Suhu (°C)", gridcolor="#1e293b", linecolor="#2d3561"),
            yaxis2=dict(title="Kelembaban (%)", overlaying="y", side="right",
                        gridcolor="#1e293b", linecolor="#2d3561"),
            legend=dict(bgcolor="rgba(0,0,0,0)", x=0.01, y=0.99),
        )
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

    with tab2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df["timestamp"], y=df["gas_ppm"],
            name="Gas (ppm)", line=dict(color="#4ade80", width=2),
            fill="tozeroy", fillcolor="rgba(74,222,128,0.08)"
        ))
        fig2.add_trace(go.Scatter(
            x=df["timestamp"], y=df["lux"],
            name="Cahaya (lux)", line=dict(color="#facc15", width=2),
            yaxis="y2"
        ))
        fig2.add_hline(y=gas_max, line_dash="dash", line_color="#f43f5e",
                       annotation_text=f"Batas gas {gas_max} ppm", annotation_font_color="#f43f5e")
        fig2.update_layout(
            **PLOTLY_LAYOUT, height=300,
            yaxis=dict(title="Gas (ppm)", gridcolor="#1e293b", linecolor="#2d3561"),
            yaxis2=dict(title="Cahaya (lux)", overlaying="y", side="right",
                        gridcolor="#1e293b", linecolor="#2d3561"),
            legend=dict(bgcolor="rgba(0,0,0,0)", x=0.01, y=0.99),
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    with tab3:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df["timestamp"], y=df["sound_level"],
            name="Level Suara", line=dict(color="#a78bfa", width=2),
            fill="tozeroy", fillcolor="rgba(167,139,250,0.08)"
        ))
        fig3.add_trace(go.Bar(
            x=df["timestamp"], y=df["motion"] * df["sound_level"].max() * 0.15,
            name="Gerakan", marker_color="rgba(244,63,94,0.5)", yaxis="y"
        ))
        fig3.add_hline(y=2500, line_dash="dash", line_color="#fb923c",
                       annotation_text="Batas kebisingan", annotation_font_color="#fb923c")
        fig3.update_layout(
            **PLOTLY_LAYOUT, height=300, barmode="overlay",
            yaxis=dict(title="Level Suara", gridcolor="#1e293b", linecolor="#2d3561"),
            legend=dict(bgcolor="rgba(0,0,0,0)", x=0.01, y=0.99),
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    # ─── COMFORT SCORE TREND ──────────────────────────────────────────────────
    st.markdown('<div class="section-title">🎯 Tren Comfort Score</div>', unsafe_allow_html=True)

    df["comfort_score"] = df.apply(
        lambda r: compute_comfort_score(r["temperature"], r["humidity"],
                                        r["gas_ppm"], r["lux"], r["sound_level"]), axis=1
    )
    fig_cs = go.Figure()
    fig_cs.add_trace(go.Scatter(
        x=df["timestamp"], y=df["comfort_score"],
        name="Comfort Score", line=dict(color="#38bdf8", width=2.5),
        fill="tozeroy", fillcolor="rgba(56,189,248,0.07)"
    ))
    for threshold, col, label in [(80, "#4ade80", "Nyaman"), (60, "#facc15", "Cukup"), (40, "#fb923c", "Kurang")]:
        fig_cs.add_hline(y=threshold, line_dash="dot", line_color=col,
                         annotation_text=label, annotation_font_color=col,
                         annotation_position="right")
    fig_cs.update_layout(
        **PLOTLY_LAYOUT, height=220,
        yaxis=dict(title="Comfort Score", range=[0,100], gridcolor="#1e293b", linecolor="#2d3561"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_cs, use_container_width=True, config={"displayModeBar": False})


    # ─── STATS SUMMARY ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📊 Statistik Sesi</div>', unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    stats = {
        "Rata-rata Suhu":    f"{df['temperature'].mean():.1f} °C",
        "Rata-rata Lembab":  f"{df['humidity'].mean():.1f} %",
        "Rata-rata Gas":     f"{df['gas_ppm'].mean():.0f} ppm",
        "Comfort Score Avg": f"{df['comfort_score'].mean():.0f} / 100",
    }
    for col, (label, val) in zip([s1, s2, s3, s4], stats.items()):
        with col:
            st.metric(label=label, value=val)


    # ─── DATA TABLE + EXPORT ──────────────────────────────────────────────────
    st.markdown('<div class="section-title">📋 Data Historis</div>', unsafe_allow_html=True)

    df_display = df[["timestamp", "temperature", "humidity", "lux",
                      "sound_level", "gas_ppm", "motion", "comfort_score"]].copy()
    df_display.columns = ["Waktu", "Suhu (°C)", "Kelembaban (%)", "Cahaya (lux)",
                           "Suara", "Gas (ppm)", "Gerak", "Comfort"]
    df_display = df_display.sort_values("Waktu", ascending=False)

    st.dataframe(df_display, use_container_width=True, height=280,
                 column_config={
                     "Comfort": st.column_config.ProgressColumn("Comfort", min_value=0, max_value=100),
                     "Gerak":   st.column_config.CheckboxColumn("Gerak"),
                 })

    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Export CSV",
        data=csv,
        file_name=f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )


# ─── AUTO REFRESH ─────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(1)
    st.rerun()