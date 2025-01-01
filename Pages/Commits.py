import streamlit as st
from query_db import fetch_repo_tables, fetch_records_in_date_range, fetch_all_data, fetch_records_in_date_range_and_author
from openai import OpenAI
import os
from dotenv import load_dotenv


from datetime import date
from query_db import fetch_records_in_date_range_author_comment


from query_db import fetch_records_by_pr_number

from query_db import create_table_pr, create_table_pr_files
from query_db import insert_to_db_pr, insert_to_db_pr_files
import requests

load_dotenv()

## Set the API key and model name
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Configure the Streamlit page
st.set_page_config(page_title="Github Commit Beta", page_icon="🧑‍💼")



#Commits Analyzer
def get_data(table, start, end):
    try:
        data = fetch_records_in_date_range(f"{table}_commits", start, end)
    except:
        st.error("Date / Commit History not generated yet")

def get_data_by_author(table, author, start, end):
    try:
        data = fetch_records_in_date_range_and_author(f"{table}_commits", author, start, end)
        return data
    except:
        st.error("Date / Commit History not generated yet")

def get_repos():
    repos = fetch_repo_tables()

    if len(repos) > 0:
        repo = st.sidebar.selectbox("Choose a repo", repos)
        return repo
    else:
        st.error("No repositories found, please [load some data first](/LoadData)")
        return

def generate_response(data):
    if "reports" not in st.session_state.keys():  # Initialize the chat messages history
        st.session_state.reports = [
            {"role": "assistant",
             "content": "Analyzing..."}
        ]

    # If last message is not from assistant, generate a new response
    with st.chat_message("assistant"):
        with st.spinner("Generating Response..."):
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                        {"role": "system", "content": "You are a code and commit history analyzer. You will be given "
                                                      "filecodes of different commits made by the same author in a repo."
                                                      " lines of code that start with the sign '+' means code added and"
                                                      "lines of code that start with sign '-' means code deleted. Generate"
                                                      "a report of the main changes made."},
                        # <-- This is the system message that provides context to the model
                        {"role": "user", "content": f"Context : {data}"}
                        # <-- This is the user message for which the model will generate a response
                ]
            )
            response = completion.choices[0].message.content
            tokens = completion.usage.total_tokens
            st.write(tokens)
            st.write(response)

@st.experimental_dialog("Generate AI Report", width='large')
def popup(table, author):
    st.write(f"Choose a range of dates for {author}")
    start = st.date_input(f"Start Date - {author}", value=None)
    end = st.date_input(f"End Date - {author}", value=None)

    if st.button("Submit"):
        data = get_data_by_author(table, author, start, end)
        generate_response(data)

def run():
    st.header("Commit Analyzer")
    st.write('Analyze any commit(s) made in the past')
    st.text_input('', placeholder='Search for User')
    st.write('')

    table = get_repos()
    all_commits = fetch_all_data(f"{table}_commits")

    # Get unique Authors using set comprehension
    unique_authors = {t[2] for t in all_commits}

    for author in unique_authors:
        with st.expander(f"{author}", icon=":material/person:"):
            st.write(f"Commits by {author}")
            if st.button(f"Generate Report of {author}"):
                popup(table, author)
            commits = [t for t in all_commits if t[2] == author]

            # Group commits by message
            commits_by_message = {}
            for commit in commits:
                message = commit[4]
                if message not in commits_by_message:
                    commits_by_message[message] = []
                commits_by_message[message].append(commit)

            with st.container(height=300):
                history = ""
                for message, commits in commits_by_message.items():
                    history = f"{message} --- \n"
                    #st.write(f"--- Commit : {message} ---")
                    with st.container():
                        for commit in commits:
                            history = history + f"{commit[3]} - {commit[5]} - {commit[6]} \n"
                        st.code(history, language='bash')


#Live Status

def live_get_data_by_author(table, author, start, end, comment):
    try:
        data = fetch_records_in_date_range_author_comment(f"{table}_commits", author, start, end, comment)
        return data
    except:
        st.error("Date / Commit History not generated yet")


def live_generate_response(data, author, commit_date, comment):
    # Create a unique key for session storage based on author and date range
    response_key = f"{author}_{commit_date}_{comment}"

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
                        {"role": "system", "content": "You are a code and commit history analyzer. You will be given "
                                                      "filecodes of different commits made by the same author in a repo."
                                                      " lines of code that start with the sign '+' means code added and"
                                                      "lines of code that start with sign '-' means code deleted. Generate"
                                                      "a report of the main changes made."},
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
def live_popup(table, author, commit_date, comment, code):
    st.write(f"Live Report for {author}")
    start = commit_date
    end = commit_date

    if st.button("Generate Report"):
        data = live_get_data_by_author(table, author, start, end, comment)
        live_generate_response(data, author, commit_date, comment)
        #st.code(code, language='python')


def find_commit_with_most_recent_date(data):
    most_recent_date = date.min
    most_recent_commit = None

    for key, lists in data.items():
        current_date = lists[0][3] if lists else date.min

        if current_date > most_recent_date:
            most_recent_date = current_date
            most_recent_commit = key

    return most_recent_commit


def live_run():
    st.header("Live Status")
    st.write('Stay up to date with most recent activity per user')
    st.text_input('', placeholder='Search for User')
    st.write('')


    table = get_repos()
    all_commits = fetch_all_data(f"{table}_commits")

    # Get unique Authors using set comprehension
    unique_authors = {t[2] for t in all_commits}

    for author in unique_authors:
        with st.expander(f"{author}", icon=":material/person:", expanded=True):
            #st.write(f"Commits by {author}")
            commits = [t for t in all_commits if t[2] == author]

            # Group commits by message
            commits_by_message = {}
            for commit in commits:
                message = commit[4]
                if message not in commits_by_message:
                    commits_by_message[message] = []
                commits_by_message[message].append(commit)

            recent_commit_key = find_commit_with_most_recent_date(commits_by_message)

            recent_commit = commits_by_message[recent_commit_key]

            with st.container():
                history = f"{recent_commit_key} --- \n"
                commit_date = recent_commit[0][3]
                code = recent_commit[0][7]
                with st.container():
                    for commit in recent_commit:
                        history = history + f"{commit[3]} - {commit[5]} - {commit[6]} \n"
                    st.code(history, language='bash')
            if st.button(f"Live Status Report of {author}"):
                live_popup(table, author, commit_date, recent_commit_key, code)


#Pull Requests

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

def pr_generate_response(data, author, number):
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
def pr_popup(table, author, number):
    st.write(f"Pull Request Report for {author}")

    if st.button("Generate Report"):
        data = fetch_records_by_pr_number(table, number)
        pr_generate_response(data, author, number)

def pr_run():
    st.header("Merge Requests Analyzer")

    table = get_repos()
    try:
        all_pr = fetch_all_data(f"{table}_pr")
        pr_files = fetch_all_data(f"{table}_pr_files")
    except:
        st.error("No Pull Requests Loaded")
        return

    if all_pr:
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
                    pr_popup(f"{table}_pr_files", pr[1], key)
    else:
        st.error('No Merge Request')



if 'report' not in st.session_state:
    st.session_state.report = ""

option = st.sidebar.selectbox('', ['Live Status', 'Merge Requests', 'Commit Analyzer'])

if option == 'Live Status':
    live_run()
elif option == 'Commit Analyzer':
    run()
    start_date = st.sidebar.date_input("Start Date", value=None)

    end_date = st.sidebar.date_input("End Date", value=None)

    if st.sidebar.button("Search For Commits"):
        get_data(table, start_date, end_date)

elif option == 'Merge Requests':
    pr_run()
