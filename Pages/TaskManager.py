import streamlit as st
from query_db import fetch_repo_tables
from query_db import fetch_all_data

from query_db import create_table_task
from query_db import insert_to_db_task


def get_repos():
    repos = fetch_repo_tables()

    if len(repos) > 0:
        repo_task = st.selectbox("Repo", repos)
        return repo_task
    else:
        st.error("No repositories found, please [load some data first](/LoadData)")
        return


def get_repos_sidebar():
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

    author = st.multiselect("Select User", unique_authors)
    return author


@st.experimental_dialog("Add Task", width='large')
def add_task():
    task = st.text_input("Implement a new task: ", placeholder='Write the Task')

    status = st.selectbox('Status', ['Open', 'To Do', 'Doing'])

    repo_task = get_repos()

    users = get_users(repo_task)

    start = st.date_input('Start Date')

    deadline = st.date_input('Deadline')

    if task and repo and users and start and deadline:
        if st.button("Submit"):
            for user in users:
                insert_to_db_task(task, status, repo_task, user, start, deadline)

            st.rerun()


create_table_task()

repo = get_repos_sidebar()

tasks = fetch_all_data('tasks')

repo_tasks = [t for t in tasks if t[3] == repo]

if 'subtasks' not in st.session_state:
    st.session_state.subtasks = []

if st.sidebar.button(f"Add New Task"):
    add_task()

def html_task(task):
    html_code = f"""
    <span style="font-size: smaller; padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; text-decoration: none; display: inline-block;">
        {task}
    </span>
    """
    return html_code


def task_manager():
    col1, col2, col3, col4 = st.columns([0.25, 0.25, 0.25, 0.25])
    with col1:
        with st.expander(f'Open Tasks', expanded=True, icon=":material/manage_search:"):
            open_tasks = [t for t in repo_tasks if t[2] == 'Open']
            unique_open_tasks = {t[1] for t in open_tasks}
            with st.container(height=500):
                for task in unique_open_tasks:
                    st.markdown(html_task(task), unsafe_allow_html=True)
    with col2:
        with st.expander(f'To Do Tasks', expanded=True, icon=":material/manage_search:"):
            todo_tasks = [t for t in repo_tasks if t[2] == 'To Do']
            with st.container(height=500):
                for task in todo_tasks:
                    st.markdown(html_task(task[1]), unsafe_allow_html=True)
    with col3:
        with st.expander(f'Doing Tasks', expanded=True, icon=":material/manage_search:"):
            doing_tasks = [t for t in repo_tasks if t[2] == 'Doing']
            with st.container(height=500):
                for task in doing_tasks:
                    st.markdown(html_task(task[1]), unsafe_allow_html=True)
    with col4:
        with st.expander(f'Closed Tasks', expanded=True, icon=":material/manage_search:"):
            closed_tasks = [t for t in repo_tasks if t[2] == 'Closed']
            with st.container(height=500):
                for task in closed_tasks:
                    st.markdown(html_task(task[1]), unsafe_allow_html=True)



def task_info():
    st.write("# Task Visualizer")
    unique_tasks = {t[1] for t in repo_tasks}
    task = st.sidebar.selectbox('Task', unique_tasks)
    st.subheader(task)

    collaborators = [t[4] for t in repo_tasks if t[1] == task]

    colx, colx2 = st.columns(2)

    with colx:
        progress = st.progress(40, 'Progress Made')
    with colx2:
        prompt = st.chat_input("Add Subtasks")
        st.session_state.subtasks.append(prompt)


    col1, col2,  col3 = st.columns([0.2, 0.3, 0.5])

    with col1:
        with st.container(height=200):
            st.write('Collaborators')
            for collaborator in collaborators:
                st.markdown(html_task(collaborator), unsafe_allow_html=True)

            st.write('')
            st.markdown(html_task('Add Collaborator'), unsafe_allow_html=True)

    with col2:
        with st.container(height=200):
            st.write('Subtasks')
            #subtasks = st.session_state.subtasks
            #for subtask in subtasks:
                #st.write(subtask)


    with col3:
        with st.container(height=200):
            st.write("Subtasks")


    with st.container(height=300):
        report = st.selectbox('Report',['Summary of Work', 'Latest Advancements', 'Things To Do', 'Commits'])


    #if report == 'Summary of Work':




option = st.sidebar.selectbox('',['Task Manager', 'Task'])


if option == 'Task Manager':
    st.write("# Task Manager")
    task_manager()
else:
    task_info()