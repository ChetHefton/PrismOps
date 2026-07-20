"""Centralized visual system for the PrismOps Streamlit application."""

from __future__ import annotations

import streamlit as st


def apply_prismops_theme() -> None:
    """Apply the dark, high-contrast PrismOps dashboard theme once per render."""

    st.markdown(
        """
<style>
:root {
  --prism-bg: #070b16;
  --prism-surface: #101728;
  --prism-surface-2: #151e32;
  --prism-border: #263450;
  --prism-text: #f4f7ff;
  --prism-muted: #aab7cf;
  --prism-violet: #9b7cff;
  --prism-blue: #4f8cff;
  --prism-cyan: #36d7e7;
  --prism-magenta: #ec67d6;
  --prism-success: #3dd6a0;
  --prism-warning: #f6bd60;
  --prism-risk: #ff7b72;
}

.stApp {
  color: var(--prism-text);
  background:
    radial-gradient(circle at 82% -8%, rgba(92, 77, 210, .18), transparent 32rem),
    radial-gradient(circle at 8% 28%, rgba(17, 143, 177, .10), transparent 28rem),
    var(--prism-bg);
}

[data-testid="stAppViewContainer"] > .main .block-container {
  max-width: 1440px;
  padding: 2rem 2.2rem 5rem;
}

[data-testid="stHeader"] { background: transparent; }

[data-testid="stSidebar"] {
  min-width: 14rem !important;
  max-width: 14rem !important;
  background: linear-gradient(180deg, #0d1424 0%, #090e1b 100%);
  border-right: 1px solid var(--prism-border);
}
[data-testid="stSidebar"] > div:first-child { width: 14rem !important; }
[data-testid="stSidebar"] .block-container { padding: 1.4rem 1rem; }

h1, h2, h3, h4 { color: var(--prism-text) !important; letter-spacing: -.02em; }
p, li, label, [data-testid="stCaptionContainer"] { color: var(--prism-muted); }

.prismops-hero {
  padding: 1.35rem 1.5rem;
  margin-bottom: 1rem;
  border: 1px solid var(--prism-border);
  border-radius: 18px;
  background: linear-gradient(120deg, rgba(155,124,255,.13), rgba(79,140,255,.06) 55%, rgba(54,215,231,.08));
  box-shadow: 0 16px 46px rgba(0,0,0,.20);
}
.prismops-eyebrow {
  color: var(--prism-cyan);
  font-size: .74rem;
  font-weight: 750;
  letter-spacing: .14em;
  text-transform: uppercase;
}
.prismops-hero h1 { margin: .2rem 0 0; font-size: clamp(2rem, 4vw, 3.1rem); }
.prismops-hero p { margin: .35rem 0 0; max-width: 62rem; font-size: 1rem; }
.prismops-gradient-text {
  background: linear-gradient(90deg, var(--prism-violet), var(--prism-blue), var(--prism-cyan));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.prismops-section-anchor { scroll-margin-top: 1rem; }
.prismops-section-kicker {
  color: var(--prism-cyan);
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  margin-bottom: -.4rem;
}

.prismops-status-success,
.prismops-setup-card {
  border-radius: 12px;
  padding: .72rem .9rem;
  font-size: .9rem;
  margin: .65rem 0 1rem;
}
.prismops-status-success {
  color: #c9ffe9;
  border: 1px solid rgba(61,214,160,.38);
  background: rgba(25,125,94,.18);
}
.prismops-setup-card {
  color: #dbe5fa;
  border: 1px solid rgba(79,140,255,.38);
  background: linear-gradient(110deg, rgba(79,140,255,.10), rgba(155,124,255,.08));
}

.prismops-ai-panel {
  border: 1px solid transparent;
  border-radius: 18px;
  padding: 1px;
  margin: .4rem 0 1.5rem;
  background: linear-gradient(120deg, rgba(236,103,214,.75), rgba(125,105,255,.8), rgba(54,215,231,.65));
  box-shadow: 0 18px 55px rgba(50,35,110,.20);
}
.prismops-ai-panel-inner {
  border-radius: 17px;
  padding: 1rem 1.1rem;
  background: linear-gradient(145deg, rgba(16,23,40,.98), rgba(11,17,31,.98));
}
.prismops-workflow {
  display: grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: .55rem;
  margin: .8rem 0 .25rem;
}
.prismops-step {
  min-height: 66px;
  padding: .65rem .7rem;
  border: 1px solid var(--prism-border);
  border-radius: 11px;
  background: rgba(21,30,50,.76);
}
.prismops-step strong { display: block; color: var(--prism-text); font-size: .82rem; }
.prismops-step span { color: var(--prism-muted); font-size: .74rem; }
.prismops-step-badge {
  display: inline-grid !important;
  place-items: center;
  width: 1.35rem; height: 1.35rem;
  border-radius: 999px;
  margin-right: .35rem;
  color: #fff !important;
  background: linear-gradient(135deg, var(--prism-violet), var(--prism-blue));
}

.prismops-metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: .75rem;
}
.prismops-metric-card {
  min-height: 132px;
  border: 1px solid var(--prism-border);
  border-top: 3px solid var(--metric-accent, var(--prism-blue));
  border-radius: 14px;
  padding: .9rem 1rem;
  background: linear-gradient(160deg, rgba(21,30,50,.96), rgba(13,20,36,.96));
  box-shadow: 0 12px 30px rgba(0,0,0,.14);
  transition: border-color .16s ease, transform .16s ease;
}
.prismops-metric-card:hover { border-color: var(--metric-accent); transform: translateY(-1px); }
.prismops-metric-label { color: var(--prism-muted); font-size: .76rem; font-weight: 650; min-height: 2.1em; }
.prismops-metric-value { color: var(--prism-text); font-size: clamp(1.25rem, 2vw, 1.8rem); font-weight: 760; line-height: 1.15; margin: .45rem 0; overflow-wrap: anywhere; }
.prismops-metric-support { color: #8fa0be; font-size: .72rem; }

.prismops-rank-card,
.prismops-report-card,
.prismops-summary-card {
  border: 1px solid var(--prism-border);
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(21,30,50,.96), rgba(12,18,32,.96));
  box-shadow: 0 10px 28px rgba(0,0,0,.13);
}
.prismops-rank-card { padding: .85rem 1rem; margin: .55rem 0; }
.prismops-rank-head { display: flex; align-items: center; gap: .65rem; }
.prismops-rank-badge { min-width: 2rem; height: 2rem; display: grid; place-items: center; border-radius: 9px; color: white; font-weight: 750; background: linear-gradient(135deg, var(--prism-violet), var(--prism-blue)); }
.prismops-rank-name { color: var(--prism-text); font-size: 1rem; font-weight: 720; flex: 1; }
.prismops-score-badge { color: var(--prism-text); font-size: .8rem; font-weight: 700; border: 1px solid var(--prism-border); border-radius: 999px; padding: .25rem .55rem; }
.prismops-rank-meta { color: #c3cee3; font-size: .78rem; margin: .45rem 0; }
.prismops-rank-reason { color: var(--prism-muted); font-size: .78rem; }
.prismops-progress { height: 5px; border-radius: 999px; background: #202b44; overflow: hidden; margin-top: .6rem; }
.prismops-progress > span { display: block; height: 100%; background: linear-gradient(90deg, var(--prism-magenta), var(--prism-violet), var(--prism-blue)); }

.prismops-summary-card { padding: 1rem 1.1rem; border-left: 3px solid var(--prism-cyan); margin-bottom: .75rem; }
.prismops-report-card { padding: 1rem 1.1rem; border-top: 3px solid var(--prism-violet); margin: .7rem 0; }
.prismops-report-head { display: flex; gap: .6rem; align-items: center; justify-content: space-between; }
.prismops-report-head h4 { margin: 0; }
.prismops-confidence { font-size: .73rem; font-weight: 750; padding: .25rem .55rem; border-radius: 999px; color: #d9fff2; background: rgba(61,214,160,.14); border: 1px solid rgba(61,214,160,.35); }
.prismops-detail-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: .55rem; margin-top: .7rem; }
.prismops-detail { border-left: 3px solid var(--detail-accent, var(--prism-blue)); border-radius: 8px; background: rgba(8,13,25,.58); padding: .65rem .75rem; }
.prismops-detail strong { color: var(--prism-text); font-size: .78rem; }
.prismops-detail ul { margin: .35rem 0 0; padding-left: 1rem; }
.prismops-detail li { font-size: .77rem; margin: .18rem 0; }

div[data-testid="stPlotlyChart"] {
  border: 1px solid var(--prism-border);
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(16,23,40,.96), rgba(11,17,31,.98));
  padding: .35rem;
  box-shadow: 0 12px 30px rgba(0,0,0,.15);
  overflow: hidden;
  transition: border-color .16s ease;
}
div[data-testid="stPlotlyChart"]:hover { border-color: #40557e; }

div[data-testid="stDataFrame"], details[data-testid="stExpander"] {
  border: 1px solid var(--prism-border);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(16,23,40,.82);
}

.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
  color: white;
  border: 0;
  background: linear-gradient(100deg, #9b5cff, #625bff 52%, #287cf5);
  box-shadow: 0 8px 24px rgba(92,77,210,.28);
}
.stButton > button, .stFormSubmitButton > button { border-radius: 10px; transition: transform .15s ease, filter .15s ease, border-color .15s ease; }
.stButton > button:hover, .stFormSubmitButton > button:hover { transform: translateY(-1px); filter: brightness(1.08); }
.stButton > button:focus-visible, .stFormSubmitButton > button:focus-visible, input:focus-visible, textarea:focus-visible { outline: 3px solid rgba(54,215,231,.55) !important; outline-offset: 2px; }
.stButton > button:disabled { filter: saturate(.35); opacity: .5; transform: none; }

[data-testid="stChatMessage"] { border: 1px solid var(--prism-border); border-radius: 12px; background: rgba(16,23,40,.75); padding: .25rem .4rem; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) { border-left: 3px solid var(--prism-violet); }
[data-testid="stChatInput"] { position: static !important; border-color: #40557e; background: var(--prism-surface); }

.prismops-sidebar-brand { font-size: 1.05rem; font-weight: 800; color: var(--prism-text); }
.prismops-sidebar-tag { color: var(--prism-muted); font-size: .72rem; margin-bottom: 1rem; }
.prismops-status-badge { display: inline-block; border-radius: 999px; padding: .23rem .5rem; font-size: .72rem; font-weight: 750; color: #d9fff2; background: rgba(61,214,160,.13); border: 1px solid rgba(61,214,160,.35); }
.prismops-status-badge.off { color: #ffe8b0; background: rgba(246,189,96,.12); border-color: rgba(246,189,96,.34); }
.prismops-nav a { display: block; color: #bdc9df !important; text-decoration: none; font-size: .78rem; padding: .25rem 0; }
.prismops-nav a:hover { color: var(--prism-cyan) !important; }

@media (max-width: 1100px) {
  .prismops-metric-grid { grid-template-columns: repeat(3, minmax(0,1fr)); }
  .prismops-workflow { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
@media (max-width: 760px) {
  [data-testid="stAppViewContainer"] > .main .block-container { padding: 1.2rem .85rem 4rem; }
  .prismops-metric-grid, .prismops-detail-grid { grid-template-columns: 1fr; }
  .prismops-metric-card { min-height: 110px; }
  div[data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  div[data-testid="column"] { min-width: min(100%, 18rem); flex: 1 1 100%; }
}
@media (max-width: 430px) {
  .prismops-workflow { grid-template-columns: 1fr; }
  .prismops-hero { padding: 1rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; }
}
</style>
""",
        unsafe_allow_html=True,
    )
