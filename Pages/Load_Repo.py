import os

import streamlit as st

from data_gather import ContextGatherer
from query_db import create_table, create_table_commits, create_table_pr, create_table_pr_files

import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def load_repo(repo):
    if st.button("Load data into the database"):
        file = str(repo)
        table_name = '/'.join(file.split('/')[-2:]).replace('/', '_').replace('-', '_')

        owner, name = file.split("/")[-2:]

        create_table(table_name)
        create_table_commits(table_name)
        create_table_pr(table_name)
        create_table_pr_files(table_name)

        github_token = os.environ.get('GITHUB_TOKEN')

        gatherer = ContextGatherer(
            relevant_extensions=['.py', '.c', '.cpp', '.js', '.v', '.ts'],
            repo=str(repo),
            table=table_name,
            github_token=github_token,
            owner=owner,
            name=name
        )

        st.spinner("Processing Filecodes...")
        start = time.time()
        progress = st.progress(0, f"Processing Filecodes of Repo {table_name}")
        gatherer.gather_context()
        progress.progress(40, f"Processing Commits of Repo {table_name}")
        gatherer.commit_history()
        progress.progress(70, f"Processing Pull Requests of Repo {table_name}")
        gatherer.get_pull_requests()
        duration = time.time() - start
        progress.progress(100, f"Processing Repo took {duration} seconds")

        gatherer.since = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        gatherer.start_scheduler()
        st.success("Scheduler started. The data gathering process will run every 2 minutes.")


st.set_page_config(page_title="Load Repo Data", page_icon="💿")

st.markdown("# Load Repo Data For Analysis")
st.sidebar.header("Load Repo Data")
st.write(
    """Load Repo Data!"""
)

repo = st.text_input("Repo", "https://github.com/Polo280/KL25Z_Labs")
branch = st.text_input("Branch", "main")

load_repo(repo)


