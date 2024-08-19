import streamlit as st
from query_db import fetch_repo_tables, fetch_all_data, fetch_records_by_pr_number
from openai import OpenAI
import os
from datetime import date

import time
import requests

from query_db import create_table_pr, create_table_pr_files
from query_db import insert_to_db_pr, insert_to_db_pr_files
from dotenv import load_dotenv

load_dotenv()

if 'pr_page' not in st.session_state:
    st.session_state.pr_page = "main"

## Set the API key and model name
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Configure the Streamlit page
st.set_page_config(page_title="Github Commit Beta", page_icon="🧑‍💼")
st.header("Pull Request Analyzer")


def get_pull_requests(owner, repo):
    GITHUB_TOKEN = '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'

    # Headers for authentication
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    tablename = f"{owner}_{repo}".replace("-", "_")
    create_table_pr(tablename)
    create_table_pr_files(tablename)
    # GitHub API URL for pull requests
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls'
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        pull_requests = response.json()

        for pr in pull_requests:
            number = pr['number']
            author = pr['user']['login']
            date = pr['created_at'].split('T')[0]
            title = pr['title']
            state = pr['state']
            branch = pr['head']['ref']
            merge = pr['base']['ref']

            insert_to_db_pr(tablename, number, author, date, title, state, branch, merge)

            try:
                pr_commits = f'https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files'
                response_commits = requests.get(pr_commits, headers=headers)

                if response_commits.status_code == 200:
                    commits_requests = response_commits.json()
                    for commit in commits_requests:
                        filename = commit['filename']
                        status = commit['status']
                        code = commit['patch']

                        insert_to_db_pr_files(tablename, number, filename, status, code)
            except:
                print("Error getting files")


    else:
        print(f"Failed to retrieve pull requests: {response.status_code}")



def get_repos():
    repos = fetch_repo_tables()

    if len(repos) > 0:
        repo = st.sidebar.selectbox("Choose a repo", repos)
        return repo
    else:
        st.error("No repositories found, please [load some data first](/LoadData)")
        return


def generate_response(data, author, number):
    # Create a unique key for session storage based on author and date range
    response_key = f"{author}_{number}"

    # Check if we already have a saved response for this author and date range
    if response_key in st.session_state:
        response = st.session_state[response_key]
        st.write("Response retrieved from saved data:")
        st.write(response)
        return

    if "reports" not in st.session_state.keys():  # Initialize the chat messages history
        st.session_state.reports = [
            {"role": "assistant",
             "content": "Analyzing..."}
        ]

    # If last message is not from assistant, generate a new response
    with st.chat_message("assistant"):
        with st.spinner("Generating Report..."):
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                        {"role": "system", "content": "You are analyzing a pull request of a repo."
                                                      " code and status is given. You will be given "
                                                      "filecodes of different commits made by the same author in the pull request."
                                                      " lines of code that start with the sign '+' means code added and"
                                                      "lines of code that start with sign '-' means code deleted. Generate"
                                                      "a report of the main changes made and if there is any potential issue."},
                        # <-- This is the system message that provides context to the model
                        {"role": "user", "content": f"Context : {data}"}
                        # <-- This is the user message for which the model will generate a response
                ]
            )
            response = completion.choices[0].message.content
            tokens = completion.usage.total_tokens
            st.write(f"Tokens used: {tokens}")
            st.write(response)

            # Save the response in session state
            st.session_state[response_key] = response


@st.experimental_dialog("Generate AI Report", width='large')
def popup(table, author, number):
    st.write(f"Pull Request Report for {author}")

    if st.button("Generate Report"):
        data = fetch_records_by_pr_number(table, number)
        generate_response(data, author, number)




def find_commit_with_most_recent_date(data):
    most_recent_date = date.min
    most_recent_commit = None

    for key, lists in data.items():
        current_date = lists[0][2] if lists else date.min

        if current_date > most_recent_date:
            most_recent_date = current_date
            most_recent_commit = key

    return most_recent_commit


def main():
    table = get_repos()
    try:
        all_pr = fetch_all_data(f"{table}_pr")
        pr_files = fetch_all_data(f"{table}_pr_files")
    except:
        st.error("No Pull Requests Loaded")
        """
            if st.button("Get Pull Requests"):
                st.spinner("Obtaining Pull Requests...")
                owner, repo = table.split("_")
                start = time.time()
                progress = st.progress(0, f"Processing Pull Requests {table}")
                get_pull_requests(owner, repo)
                progress.progress(50, f"Processing Files")
                time.sleep(3)
                duration = time.time() - start
                progress.progress(100, f"Processing Requests took {duration} seconds")
                time.sleep(2)
                st.rerun()
        """
        return

    # Group commits by pr number
    commits_by_pr = {}
    for commit in pr_files:
        number = commit[1]
        if number not in commits_by_pr:
            commits_by_pr[number] = []
        commits_by_pr[number].append(commit)

    for pr in all_pr:
        with st.expander(f"#{pr[0]} {pr[1]} - {pr[3]} / {pr[2]}", icon=":material/person:", expanded=True):
            st.write(f"Pull Request by {pr[1]}")
            key = pr[0]
            with st.container():
                history = f"Changes made :  \n\n"
                try:
                    commits = commits_by_pr[key]
                    for commit in commits:
                        history = history + f"{commit[2]} - {commit[3]} \n"
                except:
                    history = "No Files Changes Found"
                st.code(history, language='bash')
            if st.button(f"Generate Report of Pull Request #{key}"):
                popup(f"{table}_pr_files", pr[1], key)


def user_page():
    st.write("Page for user")

    # Button to navigate back to the main page
    if st.button("Back to Main Page"):
        # Redirect to the main page
        st.session_state.pr_page = "main"
        st.rerun()


if 'report' not in st.session_state:
    st.session_state.report = ""

if st.session_state.pr_page == "main":
    main()
else:
    run()

