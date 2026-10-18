import requests
import streamlit as st
st.set_page_config(page_title='IntelliConsult AI',page_icon='🧠',layout='wide')
st.title('IntelliConsult AI')
st.caption('Approved architecture skeleton · FastAPI + LangGraph + Hybrid Retrieval + Ollama-ready')
question=st.text_area('Enterprise question',value='We want Agilent laboratory equipment. What financial supplier risks should we consider?')
if st.button('Consult',type='primary'):
    try:
        res=requests.post('http://127.0.0.1:8000/consult',json={'question':question},timeout=180)
        res.raise_for_status();data=res.json()
        st.info('Mode: '+data['mode']+' — Mock responses and evidence are synthetic until real integrations are enabled.')
        if data.get('needs_clarification'):
            st.warning('Clarification required — no specialist was selected.')
            for item in data.get('missing_information', []):
                st.write('- ' + item)
        st.write('**Selected agents:**',', '.join(data['selected_agents']) or 'None')
        st.subheader('Findings')
        for f in data['findings']:st.write(f"**{f['domain'].title()}:** {f['summary']}")
        st.subheader('Recommendations')
        for r in data['recommendations']:st.write(f"**{r['domain'].title()}:** {r['action']} — {r['rationale']}")
        st.subheader('Retrieved evidence')
        for e in data['evidence']:st.caption(f"{e['id']} | {e['source']} | page {e['page']} | {e['retrieval']}");st.write(e['text'])
        st.subheader('Uncertainties / risks')
        for x in data['uncertainties']+data['risks']:st.write('- '+x)
        st.subheader('Next actions and KPIs')
        st.write(data['next_actions']);st.write(data['kpis'])
    except requests.RequestException as e:
        st.error(f'Cannot reach FastAPI. Start backend first. Detail: {e}')
