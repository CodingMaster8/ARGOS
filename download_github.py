import os
import requests
from zipfile import ZipFile
import shutil

def starts_with_pattern(string, pattern="https://github.com/"):
    return string.startswith(pattern)


def download_github_repo(repo_url, destination_dir='/Users/pablovargas/Documents/repos'):
    # GitHub API URL for the repository's ZIP archive
    try:
        owner, repo = repo_url.rstrip('/').split('/')[-2:]
    except ValueError:
        print('Invalid URL format. Please provide a URL like "https://github.com/owner/repo".')
        return

    # GitHub API URL for the repository's ZIP archive
    url = f'https://api.github.com/repos/{owner}/{repo}/zipball'

    # Make sure the destination directory exists
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    if os.path.exists(destination_dir):
        for filename in os.listdir(destination_dir):
            file_path = os.path.join(destination_dir, filename)
            try:
                # If it's a file, remove it
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                # If it's a directory, remove it and all its contents
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

    # The path where the ZIP file will be saved
    zip_path = os.path.join(destination_dir, f'{repo}.zip')

    # Download the ZIP file
    print(f'Downloading {repo}...')
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(zip_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
        print(f'{repo} downloaded successfully.')
    else:
        print(f'Failed to download {repo}. Status code: {response.status_code}')
        return

    # Extract the ZIP file
    print(f'Extracting {repo}...')
    with ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(destination_dir)

    # Remove the ZIP file after extraction
    os.remove(zip_path)
    print(f'{repo} extracted and ZIP file removed.')


if __name__ == "__main__":
    download_github_repo("https://github.com/Polo280/6348-HORUS-2021")
