import streamlit as st
import plotly.express as px
import random
from datetime import datetime, timedelta
from openai import OpenAI
from query_db import fetch_records_in_date_range_and_author, fetch_repo_tables, fetch_all_data

import os
from dotenv import load_dotenv

load_dotenv()

## Set the API key and model name
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def get_repos():
    repos = fetch_repo_tables()

    if len(repos) > 0:
        repo = st.sidebar.selectbox("Choose a repo", repos)
        return repo
    else:
        st.error("No repositories found, please [load some data first](/LoadData)")
        return

def get_users(repo):
    all_commits = fetch_all_data(f"{repo}_commits")

    # Get unique Authors using set comprehension
    unique_authors = {t[2] for t in all_commits}

    author = st.sidebar.selectbox("Select User", unique_authors)
    return author

def generate_response(data, author, commit_date, repo):
    # Create a unique key for session storage based on author and date range
    response_key = f"{author}_{commit_date}_{repo}"

    # Check if we already have a saved response for this author and date range
    if response_key in st.session_state:
        response = st.session_state[response_key]
        st.write(response)
        return

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
                                                      "a report of the main changes made. If no context is given response should"
                                                      "be 'No Commits Made in this range of dates'"},
                        # <-- This is the system message that provides context to the model
                        {"role": "user", "content": f"Context : {data}"}
                        # <-- This is the user message for which the model will generate a response
                ]
            )
            response = completion.choices[0].message.content
            tokens = completion.usage.total_tokens
            st.write(response)
            st.write(tokens)
            # Save the response in session state
            st.session_state[response_key] = response

def report(data, author, commit_date, repo):
    # Create a unique key for session storage based on author and date range
    response_key = f"{author}_{commit_date}_{repo}"

    # Check if we already have a saved response for this author and date range
    if response_key in st.session_state:
        response = st.session_state[response_key]
        #st.write(response)
        return response

    if "reports" not in st.session_state.keys():  # Initialize the chat messages history
        st.session_state.reports = [
            {"role": "assistant",
             "content": "Analyzing..."}
        ]

    if not data:
        response = 'No Commits Made in this range of dates'
        return response

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
                                                      "a report of the main changes made. If no context is given response should"
                                                      "be 'No Commits Made in this range of dates'"},
                        # <-- This is the system message that provides context to the model
                        {"role": "user", "content": f"Context : {data}"}
                        # <-- This is the user message for which the model will generate a response
                ]
            )
            response = completion.choices[0].message.content
            tokens = completion.usage.total_tokens
            print(tokens)
            # Save the response in session state
            st.session_state[response_key] = response

    return response

def summary(reports, author, start, end, repo):
    # Create a unique key for session storage based on author and date range
    summary = f"{author}_{start}_{end}_{repo}"

    # Check if we already have a saved response for this author and date range
    if summary in st.session_state:
        response = st.session_state[summary]
        st.write(response)
        return

    # If last message is not from assistant, generate a new response
    with st.chat_message("assistant"):
        with st.spinner("Generating Response..."):
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                        {"role": "system", "content": "You are given a set of daily reports of actions made by a user"
                                                      "in a repository. Generate a concise and structured summary of the"
                                                      "reports ordered by dates from oldest to earliest."},
                        # <-- This is the system message that provides context to the model
                        {"role": "user", "content": f"Context : {reports}"}
                        # <-- This is the user message for which the model will generate a response
                ]
            )
            response = completion.choices[0].message.content
            tokens = completion.usage.total_tokens
            st.write(response)
            st.write(tokens)
            # Save the response in session state
            st.session_state[summary] = response


def commits_barplot():
    # Days of the week
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # Random numbers for each day
    values = [random.randint(0, 10) for _ in days]

    fig = px.bar(x=days, y=values)
    fig.update_layout(
        title="Commits for Each Day of the Week",
        xaxis_title="Day of the Week",
        yaxis_title="Commits Made",
        width=700,  # Set the width in pixels
        height=300  # Set the height in pixels
    )
    return fig

def date_range(repo, author):
    #custom_date = datetime(year=2024, month=6, day=3).date()
    all_datetimes = []

    if search_date == 'Personalized':
        with col6:
            start = st.date_input('Select Start Date')
        with col7:
            end = st.date_input('Select End Date')

        current_date = start

        while current_date <= end:
            all_datetimes.append(datetime(current_date.year, current_date.month, current_date.day).date())
            current_date += timedelta(days=1)

        commits = fetch_records_in_date_range_and_author(f"{repo}_commits", author, start, end)

    elif search_date == 'Today':
        today = datetime.today().date()
        commits = fetch_records_in_date_range_and_author(f"{repo}_commits", author, today, today)
        all_datetimes.append(today)

    elif search_date == 'Last 7 Days':

        #end = datetime.today().date()
        end = datetime.today().date()
        start = end - timedelta(days=6)

        #st.write("Start of last week:", start)
        #st.write("End of last week:", end)

        # Generate all datetimes in the range

        current_date = start

        while current_date <= end:
            all_datetimes.append(datetime(current_date.year, current_date.month, current_date.day).date())
            current_date += timedelta(days=1)

        commits = fetch_records_in_date_range_and_author(f"{repo}_commits", author, start, end)

    elif search_date == 'Last Month':
        end = datetime.today().date()
        start = end - timedelta(days=30)

        st.write("Start of last week:", start)
        st.write("End of last week:", end)

        current_date = start

        while current_date <= end:
            all_datetimes.append(datetime(current_date.year, current_date.month, current_date.day).date())
            current_date += timedelta(days=1)

        commits = fetch_records_in_date_range_and_author(f"{repo}_commits", author, start, end)

    return commits, all_datetimes

repo = get_repos()

user = get_users(repo)


col1, col2, col3 = st.columns([0.3, 0.1, 0.6])
col4, col5= st.columns([0.5, 0.5])
col6, col7, col8 = st.columns([0.25, 0.25, 0.5])

with col1:
    st.image('112446639.png', width=100)
    st.subheader(f"User {user}")
    st.write('(Daniel Vargas)')
    st.write(f' - {repo}')
    st.write(' - 30 Commits made')

with col2:
    st.write("")
    #st.subheader("CodingMaster")
    #st.subheader("Repo ARGOS")

with col3:
    with st.container(height=300):
        fig = commits_barplot()
        st.plotly_chart(fig)

with col4:
    search_date = st.selectbox("Select Date", ["Today", "Last 7 Days", "Last Month", "Personalized"])

with col5:
    tool = st.selectbox("Select Tool", ['Commits', 'Reports'])



author = user

commits, all_datetime = date_range(repo, author)

# Group commits by message
commits_by_message = {}
for commit in commits:
    message = commit[4]
    if message not in commits_by_message:
        commits_by_message[message] = []
    commits_by_message[message].append(commit)

custom_date = datetime(year=2024, month=6, day=3)
reports_dict = {}

if tool == 'Reports':
    with col8:
        generate_report = st.button(f'Generate Report for {author}')
    if generate_report:
        summarizer = ""
        for date in all_datetime:
            data = fetch_records_in_date_range_and_author(f"{repo}_commits", author, date, date)
            data = [commit[2:] for commit in data if len(commit) > 1]
            #generate_response(data, author, date, repo)
            reportes = report(data, author, date, repo)
            summarizer += f"\n {reportes} \n"
            reports_dict[str(date)] = reportes

        if search_date == 'Today':
            st.write(summarizer)

        if search_date == 'Last 7 Days':
            with st.expander('Summary', expanded=True):
                summary(reports_dict, author, all_datetime[0], all_datetime[-1], repo)
            for key, item in reports_dict.items():
                with st.expander(f'{key} Report'):
                    st.write(item)
        if search_date == 'Last Month':
            with st.expander('Summary', expanded=True):
                summary(reports_dict, author, all_datetime[0], all_datetime[-1], repo)
            for key, item in reports_dict.items():
                if item != "No Commits Made in this range of dates":
                    with st.expander(f'{key} Report'):
                        st.write(item)



        #with st.expander('Report', expanded=True):
            #generate_response(commits_by_message, author, custom_date, repo)

elif tool == 'Commits':
    with st.expander('Commits', expanded=True):
        try:
            if not commits:
                st.code('No Commits Found Or Made')
            else:
                with st.container(height=300):
                    history = ""
                    for message, commits in commits_by_message.items():
                        history = f"{message} --- \n"
                        #st.write(f"--- Commit : {message} ---")
                        with st.container():
                            for commit in commits:
                                history = history + f"{commit[3]} - {commit[5]} - {commit[6]} \n"
                            st.code(history, language='bash')


        except:
            st.code('No Commits Found')
