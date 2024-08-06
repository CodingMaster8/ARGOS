import streamlit as st


pg = st.navigation([
    st.Page("Pages/Home.py", title="Home", icon=":material/home:"),
    st.Page("Pages/Load_Repo.py", title="Load Data", icon=":material/upload_file:"),
    st.Page("Pages/Commits.py", title="Commit Analyzer", icon=":material/account_tree:"),
    st.Page("Pages/LLM.py", title="LLM", icon=":material/data_usage:"),
    st.Page("Pages/Tree.py", title="Tree", icon=":material/manage_search:"),
    st.Page("Pages/LiveStatus.py", title="Live Status", icon=":material/circle:"),
])
pg.run()