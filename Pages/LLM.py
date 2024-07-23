import streamlit as st

from query_db import fetch_all_table_names, fetch_file, get_filenames

from openai import OpenAI
import os

# Configure the Streamlit page
st.set_page_config(page_title="Github LLM Beta", page_icon="🧑‍💼")
st.markdown("# Github LLM Beta 0.2")
st.sidebar.header("Welcome to the Github LLM Beta")

months = st.sidebar.slider('How many months back to search (0=no limit)?', 0, 130, 0)

## Set the API key and model name
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "sk-proj-PPVvLU4BgKkl4dEhZRIOT3BlbkFJ4VcKrBv9z8XY8a8zdiVE"))


def llm(data):

    if "messages" not in st.session_state.keys():  # Initialize the chat messages history
        st.session_state.messages = [
            {"role": "assistant",
             "content": "Choose any Repo. I will help you analyzing, optimizing or querying the data you provide me."}
        ]

    # Check if there is a prompt from the user
    if prompt := st.chat_input("Your question"):  # Prompt for user input and save to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        generate_response(prompt, data)


    for message in st.session_state.messages:  # Display the prior chat messages
        with st.chat_message(message["role"]):
            st.write(message["content"])

def generate_response(prompt, data):
    # If last message is not from assistant, generate a new response
    if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Generating Response..."):
                completion = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": "You are a code and commit history analyzer. You help answering questions or optimizing code."},
                        # <-- This is the system message that provides context to the model
                        {"role": "user", "content": f"User query: {prompt}, Context : {data}"}
                        # <-- This is the user message for which the model will generate a response
                    ]
                )
                response = completion.choices[0].message.content
                st.write(completion.usage.total_tokens)
                st.session_state.messages.append({"role": "assistant", "content": response})  # Add response to message history


def get_repos():
    repos = fetch_all_table_names()

    if len(repos) > 0:
        repo = st.sidebar.selectbox("Choose a repo", repos)
        return repo
    else:
        st.error("No repositories found, please [load some data first](/LoadData)")
        return


def get_data(table, query_type):
    if query_type == "Commits":
        data = fetch_file(table, "commits")[3]
        with st.expander("Commit History"):
            st.code(data, language='bash')

    if query_type == "Code File":
        filenames = get_filenames(table)
        file = st.sidebar.selectbox("Choose File", filenames)

        data = fetch_file(table, file)[3]

        st.code(f"Code of file {file}", language='bash')
        with st.expander("Code"):
            st.code(data, language='bash')

    return data

def run():
    repo = get_repos()
    query_type = st.sidebar.selectbox("Query Data", ["Commits", "Code File"])
    data = get_data(repo, query_type)
    llm(data)

run()