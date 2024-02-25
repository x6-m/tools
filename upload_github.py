import os
import csv
from github import Github, UnknownObjectException
import time

def load_uploaded_files(log_file):
    max_repo_count = 1
    uploaded_files = set()
    last_repo_img_count = 0
    try:
        with open(log_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[2] == 'Uploaded':
                    uploaded_files.add(row[1])
                repo_count = int(row[0].split('-')[-1])
                max_repo_count = max(max_repo_count, repo_count)
                if repo_count == max_repo_count:
                    last_repo_img_count = int(row[4])
    except FileNotFoundError:
        pass
    return uploaded_files, max_repo_count, last_repo_img_count

def save_uploaded_file(log_file, repo_name, filename, status, error, img_count):
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([repo_name, filename, status, error, img_count])

def create_repo_and_upload_images(token, repo_prefix, path, log_file, images_per_repo=200, max_retries=3):
    g = Github(token)
    user = g.get_user()
    files = os.listdir(path)
    files.sort()

    uploaded_files, repo_count, last_repo_img_count = load_uploaded_files(log_file)

    if last_repo_img_count < images_per_repo:
        image_count = last_repo_img_count
    else:
        image_count = 0
        repo_count += 1  # Create new repo

    try:
        repo = user.get_repo(f'{repo_prefix}-{repo_count}')  # Try to get the last repo
    except Exception as e:  # If the last repo does not exist
        repo = user.create_repo(f'{repo_prefix}-{repo_count}')  # Create a new one

    for filename in files:
        if filename in uploaded_files:
            continue
        if filename.endswith('.jpg') or filename.endswith('.png'):
            if image_count >= images_per_repo:  # Once the repo is full, create a new one
                repo_count += 1
                repo = user.create_repo(f'{repo_prefix}-{repo_count}')
                image_count = 0  # Reset the image count for the new repo
            
            with open(f'{path}/{filename}', 'rb') as file:
                content = file.read()
                
            try:
                for _ in range(max_retries):
                    try:
                        repo.create_file(f'{filename}', 'Upload image {filename}', content)
                        print(f'Uploaded image {filename} to {repo.name}')
                        image_count += 1
                        save_uploaded_file(log_file, repo.name, filename, 'Uploaded', '', image_count)
                        break
                    except Exception as e:
                        print(f'Failed to upload {filename}, error: {str(e)}')

                        time.sleep(0.5)

                        # Check if the file is already in the repo
                        try:
                            repo.get_contents(filename)
                            print(f'File {filename} exists in the repo, assuming successful upload')
                            image_count += 1
                            save_uploaded_file(log_file, repo.name, filename, 'Uploaded', '(assumed after error)', image_count)
                        except:
                            save_uploaded_file(log_file, repo.name, filename, 'Failed', str(e), image_count)

            except GithubException as g:
                print(f'GithubException occurred: {str(g)}')
                if g.status == 422:   # Handle file already exists exception.
                    print(f'File {filename} already exists in the repo, assuming successful upload')
                    # Do standard success steps

# Use it like this:
token = ''  # Replace with your Github personal access token
repo_prefix = f'ban_kou_xiao_xi'  # Replace with your repository prefix
path = ''  # Replace with your image file directory
log_file = f'./{repo_prefix}.csv'  # Replace with your log file
images_per_repo = 100  # Replace with your desired number of images per repository
max_retries = 3  # Replace with your desired number of retries

create_repo_and_upload_images(token, repo_prefix, path, log_file, images_per_repo, max_retries)
