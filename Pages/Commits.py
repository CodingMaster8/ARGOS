import streamlit as st
from query_db import fetch_repo_tables, fetch_records_in_date_range, fetch_all_data, fetch_records_in_date_range_and_author
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

## Set the API key and model name
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Configure the Streamlit page
st.set_page_config(page_title="Github Commit Beta", page_icon="🧑‍💼")
st.header("Commit History LLM")

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


if 'report' not in st.session_state:
    st.session_state.report = ""

run()

start_date = st.sidebar.date_input("Start Date", value=None)

end_date = st.sidebar.date_input("End Date", value=None)

if st.sidebar.button("Search For Commits"):
    get_data(table, start_date, end_date)