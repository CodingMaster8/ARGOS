import streamlit as st

from query_db import fetch_repo_tables, fetch_file, get_shorturl, search_by_shorturl

from openai import OpenAI
import os
import json
from dotenv import load_dotenv


from local_search import local_search

load_dotenv()

# Configure the Streamlit page
st.set_page_config(page_title="Github LLM Beta", page_icon="🧑‍💼")
st.markdown("# Github LLM Beta 0.2")
st.sidebar.header("Welcome to the Github LLM Beta")

#months = st.sidebar.slider('How many months back to search (0=no limit)?', 0, 130, 0)

## Set the API key and model name
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


class TokenCounter:
    def __init__(self):
        if 'token_sum' not in st.session_state:
            st.session_state.token_sum = 0
            st.sidebar.write(f"Token Count : {st.session_state.token_sum}")

    def token_counter(self, tokens):
        st.session_state.token_sum += int(tokens)
        st.sidebar.write(f"Tokens Query : {tokens}")
        st.sidebar.write(f"Token Count : {st.session_state.token_sum}")



def save_chat_history():
    if "messages" in st.session_state:
        history = st.session_state.messages
        filename = history[1].get('content')[:30].replace(" ", "_") + ".json" #Need to find a way to make them unique
        #print(name)

        # Directory where the jsons will be saved
        directory = "chat"

        if not os.path.exists(directory):
            os.makedirs(directory)

        filepath = os.path.join(directory, filename)

        with open(filepath, "w") as f:
            json.dump(history, f)

        print(f"Chat history saved as {filepath}")
def create_new_chat_history():
    save_chat_history()
    st.session_state.messages = [
        {"role": "assistant",
         "content": "New chat started. Choose any Repo. I will help you analyzing, optimizing or querying the data you provide me."}
    ]
    st.rerun()


def load_chat_history():
    directory = "chat"
    history_files = [f[:-5].replace("_", " ") + "..." for f in os.listdir(directory) if f.endswith(".json")]
    selected_file_display = st.sidebar.selectbox("Select a Chat", history_files)

    file_mapping = {
        f[:-5]: os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".json")
    }

    if st.sidebar.button("Load Chat"):
        selected_file = file_mapping[selected_file_display.replace(" ", "_")[:-3]]
        print(selected_file)
        with open(selected_file, "r") as f:
            st.session_state.messages = json.load(f)
        st.rerun()


def llm(data):

    if "messages" not in st.session_state.keys():  # Initialize the chat messages history
        st.session_state.messages = [
            {"role": "assistant",
             "content": "Choose any Repo. I will help you analyzing, optimizing or querying the data you provide me."}
        ]

    # Check if there is a prompt from the user
    if prompt := st.chat_input("Your question"):  # Prompt for user input and save to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        tokens = generate_response(prompt, data)
        counter.token_counter(int(tokens))


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
                tokens = completion.usage.total_tokens
                st.session_state.messages.append({"role": "assistant", "content": response})  # Add response to message history

    return tokens

def get_repos():
    repos = fetch_repo_tables()

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

        shorturls = get_shorturl(table)
        file_url = st.sidebar.selectbox("Choose File", shorturls)


        file = file_url.split("/")[1]

        data = search_by_shorturl(table, file_url)[3]
        directory = file_url.split('/')[0]

        st.code(f"Code of file {file} at {directory}", language='bash')
        with st.expander("Code"):
            st.code(data, language='bash')

        if st.sidebar.checkbox("Enable Local Search"):
            context = local_search(table, directory, data)
            data += context
            st.sidebar.success("Local Search Enabled")
    return data


def run():
    repo = get_repos()
    query_type = st.sidebar.selectbox("Query Data", ["Commits", "Code File"])
    data = get_data(repo, query_type)
    llm(data)
    load_chat_history()


counter = TokenCounter()
run()

# Add button to create new chat history in sidebar
if st.sidebar.button("Start New Chat"):
    create_new_chat_history()