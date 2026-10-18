import httpx
import streamlit as st
from app.config import get_settings

st.set_page_config(page_title="Agentic AI Consulting", layout="wide")
st.title("Agentic AI Management Consulting Platform")
st.caption("Local-first prototype: LangGraph + Ollama + Chroma + SQLite FTS5")
question = st.text_area("Enterprise question", height=120, placeholder="Example: What disclosed operational risks should we consider when upgrading Cisco edge infrastructure?")
if st.button("Analyze", type="primary", disabled=not question.strip()):
    with st.spinner("Running manager and specialists..."):
        try:
            r = httpx.post(f"{get_settings().api_base_url}/v1/consult", json={"question": question}, timeout=120)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            st.error(f"Request failed: {e}")
            st.stop()
    st.subheader("Routing")
    st.json(data["route"])
    rec = data["recommendation"]
    st.subheader("Executive summary")
    st.write(rec["executive_summary"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Recommendations")
        for x in rec["recommendations"]: st.write(f"- {x}")
        st.markdown("### Next actions")
        for x in rec["next_actions"]: st.write(f"- {x}")
    with c2:
        st.markdown("### Risks")
        for x in rec["risks"]: st.write(f"- {x}")
        st.markdown("### Uncertainty")
        for x in rec["uncertainty"]: st.write(f"- {x}")
    st.markdown("### Evidence")
    for e in rec["evidence"]:
        with st.expander(f"{e['source_title']} | page {e.get('page_number')} | score {e['score']}"):
            st.write(e["content"])
            st.code(e["evidence_id"])
    st.caption(f"Latency: {data['latency_ms']} ms | Confidence: {rec['confidence']:.2f}")
