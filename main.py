import streamlit as st


pg = st.navigation([
    st.Page("Pages/Home.py", title="Home", icon=":material/home:"),
    st.Page("Pages/Load_Repo.py", title="Load Data", icon=":material/upload_file:"),
    st.Page("Pages/Commits.py", title="Analyze", icon=":material/account_tree:"),
    st.Page("Pages/LLM.py", title="LLM", icon=":material/data_usage:"),
    #st.Page("testing.py", title="Manage Team", icon=":material/manage_search:"),
    #st.Page("Pages/LiveStatus.py", title="Live Status", icon=":material/circle:"),
    #st.Page("Pages/Pull_Requests.py", title="Pull Requests", icon=":material/square:"),
    st.Page("Pages/TaskManager.py", title="Tasks", icon= ":material/data_usage:"),
])
pg.run()