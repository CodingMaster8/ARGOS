import streamlit as st
from streamlit.logger import get_logger

LOGGER = get_logger(__name__)


def run():
    st.set_page_config(
        page_title="Home",
        page_icon="👋",
    )

    st.write("# Welcome to the Github LLM v2 👋")

    st.write("""
            Please go to the sidebar and:
             - Load any repo   
             - Ask queries about the repo to a LLM  
             - Get AI Reports of any Author  
             """)

run()

st.write("")

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    tile1 = col1.container(height=60)
    tile1.page_link("Pages/Load_Repo.py", label="Load Your Repo", icon=":material/upload_file:", use_container_width=True)

with col1:
    tile2 = col2.container(height=60)
    tile2.page_link("Pages/Commits.py", label="Get Reports", icon=":material/account_tree:")


with col3:
    tile3 = col3.container(height=60)
    tile3.page_link("Pages/LLM.py", label="Query Anything", icon=":material/data_usage:")

with col4:
    tile4 = col4.container(height=60)
    tile4.page_link("Pages/Tree.py", label="Analyze Tree", icon=":material/manage_search:")






