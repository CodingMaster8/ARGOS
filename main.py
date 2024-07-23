import streamlit as st
from streamlit.logger import get_logger

LOGGER = get_logger(__name__)


def run():
    st.set_page_config(
        page_title="Home",
        page_icon="👋",
    )

    st.write("# Welcome to the Github LLM v1 👋")

    st.write("""
            Please go to the sidebar and:
             - Load a repo   
             - Ask queries about the repo to a LLM    
             """)



if __name__ == "__main__":
    run()
