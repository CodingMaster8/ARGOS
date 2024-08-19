import os
import logging
import requests
from datetime import datetime

from query_db import insert_to_db, insert_to_db_commits
from query_db import insert_to_db_pr, insert_to_db_pr_files
from query_db import commit_exist
from query_db import file_exists_in_db, update_file_in_db
from query_db import update_filepath_in_db

from apscheduler.schedulers.background import BackgroundScheduler



""" LOGGING is used for making better console outputs/warnings"""
# Set up logging
logger = logging.getLogger(__name__)
log_level = os.getenv("LOGLEVEL", "INFO").upper()
logger.handlers = []

# Set up logging to console
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Set the logging level for the logger
logger.setLevel(log_level)


class ContextGatherer:
    def __init__(self,
                 relevant_extensions=None, repo='.', table='.', github_token='.', owner='.', name='.'):
        self.relevant_extensions = relevant_extensions or ['.py']
        self.repo = repo
        self.table = table
        self.github_token = github_token
        self.repo_owner = owner
        self.repo_name = name
        self.since = None  # Initial since value is None

    def is_relevant_file(self, file_path):
        """Determine if a file is relevant for the context."""
        return any(file_path.endswith(ext) for ext in self.relevant_extensions)

    def gather_context(self, path=""):
        """Gather context from relevant files in the GitHub repository."""
        BASE_URL = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/"
        url = BASE_URL + path
        headers = {"Authorization": f"token {self.github_token}"}
        #params = {"since": self.since.strftime('%Y-%m-%dT00:00:00Z')} if self.since else {}

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repository contents: {response.status_code}")

        contents = response.json()

        for item in contents:
            if item['type'] == 'file':
                file_path = item['path']
                if self.is_relevant_file(file_path):
                    try:
                        filename = item['name']
                        file_content = requests.get(item['download_url']).text
                        if file_exists_in_db(self.table, file_path):
                            update_file_in_db(self.table, file_path, filename, file_content)
                        else:
                            insert_to_db(self.table, file_path, filename, file_content)
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")

                print(f"\rProcessed {file_path}", end="", flush=True)

            elif item['type'] == 'dir':
                # Recursively fetch the files in the directory
                self.gather_context(path=item['path'])

        print()  # New line after progress indicator

    def commit_history(self):

        # GitHub API URL for commits
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/commits"

        headers = {"Authorization": f"token {self.github_token}"}
        #params = {"since": self.since.strftime('%Y-%m-%dT00:00:00Z')} if self.since else {}

        # Parameters for pagination
        params = {
            'per_page': 100,  # Maximum number of results per page
            'page': 1  # Starting page number
        }

        while True:
            # Make a GET request to fetch the commit history
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200 or response.status_code == 404:
                author, name = url.split('/')[-3:-1]
                commits = response.json()
                if not commits:  # Check if there are no more commits
                    break  # Exit the loop if no commits are retrieved

                for commit in commits:
                    sha = commit['sha']
                    commit_author = commit['commit']['author']['name']
                    date = commit['commit']['author']['date'].split('T')[0]  # Extract the date part only
                    message = commit['commit']['message']

                    # Check if the commit already exists in the database
                    if not commit_exist(f'{self.table}_commits', sha):

                        # Get the details of the commit
                        commit_url = f"https://api.github.com/repos/{author}/{name}/commits/{sha}"
                        commit_response = requests.get(commit_url, headers=headers)
                        if commit_response.status_code == 200 or commit_response.status_code == 404:
                            commit_data = commit_response.json()
                            files_changed = commit_data.get('files', [])

                            for file_changed in files_changed:
                                status = file_changed['status']
                                filename = file_changed['filename']

                                if file_changed['status'] == 'renamed':
                                    code = f"Previous filename: {file_changed['previous_filename']} - New filename: {file_changed['filename']}"
                                else:
                                    try:
                                        code = file_changed['patch']
                                    except:
                                        code = "Blank File"
                                insert_to_db_commits(f'{self.table}_commits', sha, commit_author, date, message, filename,
                                                     status, code)
                        else:
                            print(f"Failed to fetch commit details: {commit_response.status_code}\n")
                # Increment the page number for the next iteration
                params['page'] += 1
            else:
                print(f"Failed to fetch commits: {response.status_code}")
                break

    def get_pull_requests(self):

        token = self.github_token

        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # GitHub API URL for pull requests
        url = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls'
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

                insert_to_db_pr(self.table, number, author, date, title, state, branch, merge)

                try:
                    pr_commits = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls/{number}/files'
                    response_commits = requests.get(pr_commits, headers=headers)

                    if response_commits.status_code == 200:
                        commits_requests = response_commits.json()
                        for commit in commits_requests:
                            filename = commit['filename']
                            status = commit['status']
                            code = commit['patch']

                            insert_to_db_pr_files(self.table, number, filename, status, code)
                except:
                    print("Error getting files")


        else:
            print(f"Failed to retrieve pull requests: {response.status_code}")

    def update(self):

        # GitHub API URL for commits
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/commits"

        headers = {"Authorization": f"token {self.github_token}"}

        # Parameters for pagination
        params = {
            'per_page': 100,  # Maximum number of results per page
            'page': 1  # Starting page number
        }

        if self.since:
            params['since'] = self.since  # Add the 'since' parameter to the request

        print(f'Updating Repo since {self.since}')
        while True:
            # Make a GET request to fetch the commit history
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200 or response.status_code == 404:
                author, name = url.split('/')[-3:-1]
                commits = response.json()
                if not commits:  # Check if there are no more commits
                    break  # Exit the loop if no commits are retrieved

                for commit in commits:
                    sha = commit['sha']
                    commit_author = commit['commit']['author']['name']
                    date = commit['commit']['author']['date'].split('T')[0]  # Extract the date part only
                    message = commit['commit']['message']

                    # Check if the commit already exists in the database
                    if not commit_exist(f'{self.table}_commits', sha):

                        # Get the details of the commit
                        commit_url = f"https://api.github.com/repos/{author}/{name}/commits/{sha}"
                        commit_response = requests.get(commit_url, headers=headers)
                        if commit_response.status_code == 200 or commit_response.status_code == 404:
                            commit_data = commit_response.json()
                            files_changed = commit_data.get('files', [])

                            for file_changed in files_changed:
                                status = file_changed['status']
                                filename = file_changed['filename']

                                if file_changed['status'] == 'renamed':
                                    code = f"Previous filename: {file_changed['previous_filename']} - New filename: {file_changed['filename']}"
                                    if self.is_relevant_file(filename):
                                        update_filepath_in_db(self.table, file_changed['filename'], file_changed['previous_filename'])
                                else:
                                    try:
                                        code = file_changed['patch']
                                        if self.is_relevant_file(filename):
                                            content_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/{filename}"
                                            content_response = requests.get(content_url, headers=headers)
                                            if content_response.status_code != 200:
                                                raise Exception(f"Failed to fetch repository contents: {content_response.status_code}")
                                            content_data = content_response.json()
                                            code = requests.get(content_data['download_url']).text
                                            file = filename.split('/')[-1]

                                            update_file_in_db(self.table, filename, file, code)
                                    except:
                                        code = "Blank File"
                                insert_to_db_commits(f'{self.table}_commits', sha, commit_author, date, message, filename,
                                                     status, code)
                        else:
                            print(f"Failed to fetch commit details: {commit_response.status_code}\n")
                # Increment the page number for the next iteration
                params['page'] += 1
            else:
                print(f"Failed to fetch commits: {response.status_code}")
                break

        self.since = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        print(f'Repo succesfully updated until {self.since}')

    def run(self):
        print(self.since)
        """Run the context gathering process and return the context and token count."""
        self.gather_context()
        print(f"Context gathered successfully.")
        self.commit_history()
        print(f"Commits gathered successfully.")
        self.get_pull_requests()
        print(f"Pulls gathered successfully.")
        self.since = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def start_scheduler(self):
        """Start the APScheduler to run the process every 12 hours."""
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.update, 'interval', minutes=2)
        scheduler.start()
        print("Scheduler started. The data gathering process will run every 12 hours.")



