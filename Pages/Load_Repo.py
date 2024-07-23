import streamlit as st

from data_gather import ContextGatherer
from download_github import starts_with_pattern, download_github_repo
from query_db import create_table, fetch_file

import time
import json

def load_repo():
    repo = st.text_input("Repo", "https://github.com/Polo280/KL25Z_Labs")
    branch = st.text_input("Branch", "main")

    if st.button("Load data into the database"):

        st.spinner("Fetching Repo Data...")
        start = time.time()
        progress = st.progress(0, "Fetching Repo Data")
        download_github_repo(str(repo))
        duration = time.time() - start
        progress.progress(100, f"Fetching Repo Data took {duration} seconds")

        file = str(repo)
        table_name = '/'.join(file.split('/')[-2:]).replace('/', '_').replace('-', '_')

        create_table(table_name)

        st.spinner("Processing Tree...")
        start = time.time()
        progress = st.progress(0, f"Processing Tree of Repo {table_name}")
        gatherer = ContextGatherer(
            directory='/Users/pablovargas/Documents/repos',
            output_file='../context.txt',
            relevant_extensions=['.py', '.c'],
            max_file_size=500_000,  # 500KB
            max_tokens=60000,
            repo=str(repo),
            table=table_name
        )
        context, token_count, context_tree = gatherer.run()

        duration = time.time() - start
        progress.progress(100, f"Processing Tree took {duration} seconds")

        st.code(f"Token count: {token_count} \n{context_tree}", language="bash")

        tree_key = {
            f'{table_name.lower()}' : f'{context_tree}'
        }

        # Path to the JSON file
        file_path = 'trees.json'

        add_data_to_json(file_path, tree_key)


def add_data_to_json(file_path, new_data):
    # Load existing data
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    # Update with new data
    data.update(new_data)

    # Save the updated data back to the JSON file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

st.set_page_config(page_title="Load Repo Data", page_icon="💿")

st.markdown("# Load Repo Data For Analysis")
st.sidebar.header("Load Repo Data")
st.write(
    """Load Repo Data!"""
)
load_repo()

