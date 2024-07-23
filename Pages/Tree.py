import streamlit as st
from query_db import fetch_all_table_names
import json

st.sidebar.header("Visualize Github Tree Of The Repo")

repos = fetch_all_table_names()
repo = st.sidebar.selectbox("Select Repo", repos)

def get_tree(repo):
    # Path to the JSON file
    file_path = 'trees.json'

    try:
        # Attempt to read and load data from JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Check if the JSON data is empty or not
        if data:
            value = data.get(f'{repo}', 'This Repo is Empty/Not Working')
            st.code(f"Tree of Repo {repo}")
            st.code(value, language='bash')
        else:
            st.code("No Repos Uploaded Yet. Please Upload a Repo.", language='bash')
    except json.JSONDecodeError:
        # This specific exception handles cases where json loading fails due to bad formatting or empty file
        print("Failed to decode JSON, possibly because the file is empty or not properly formatted.")
    except FileNotFoundError:
        # This exception handles cases where the JSON file is not found
        print("The JSON file was not found.")
    except Exception as e:
        # General exception to catch any other kinds of unexpected errors
        print(f"An error occurred: {str(e)}")


get_tree(repo)