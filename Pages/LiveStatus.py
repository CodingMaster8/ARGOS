import streamlit as st
from query_db import fetch_repo_tables, fetch_records_in_date_range, fetch_all_data, fetch_records_in_date_range_author_comment
from openai import OpenAI
import os

from datetime import date

from dotenv import load_dotenv

load_dotenv()

## Set the API key and model name
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Configure the Streamlit page
st.set_page_config(page_title="Github Commit Beta", page_icon="🧑‍💼")
st.header("Live Status Of Users")



def get_data_by_author(table, author, start, end, comment):
    try:
        data = fetch_records_in_date_range_author_comment(f"{table}_commits", author, start, end, comment)
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


def generate_response(data, author, commit_date, comment):
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
def popup(table, author, commit_date, comment, code):
    st.write(f"Live Report for {author}")
    start = commit_date
    end = commit_date

    if st.button("Generate Report"):
        data = get_data_by_author(table, author, start, end, comment)
        generate_response(data, author, commit_date, comment)
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


def run():
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
                popup(table, author, commit_date, recent_commit_key, code)


if 'report' not in st.session_state:
    st.session_state.report = ""

run()

