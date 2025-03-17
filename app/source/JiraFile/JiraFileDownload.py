import requests
from requests.auth import HTTPBasicAuth
import os
import json
import re

# Jira 정보
jira_base_url = "https://msimul.atlassian.net"
auth_token = ""
auth = HTTPBasicAuth("juwon@msimul.com", auth_token)  # 이메일 주소를 입력하세요.

# 헤더
headers = {
    "Accept": "application/json"
}

# 저장할 경로1
user_profile = os.environ['USERPROFILE']
download_dir = os.path.join(user_profile, 'OneDrive')
#download_dir = "C:\\Users\\juwon\\Desktop\\강주원\\20.Project\\Pyrhon\\Jira\\Attachments"

# 유효하지 않은 문자를 제거해 폴더명을 정리하는 함수
def clean_folder_name(folder_name):
    invalid_chars = r'[<>:"/\\|?*]'
    clean_name = re.sub(invalid_chars, '', folder_name).strip()
    return clean_name

# 폴더를 생성하는 함수
def create_directory(directory_path):
    try:
        os.makedirs(directory_path, exist_ok=True)
        print(f"Directory created: {directory_path}")
    except Exception as e:
        print(f"Error while creating directory: {e}")

# 파일 다운로드 함수
def download_file(url, save_path):
    response = requests.get(url, headers=headers, auth=auth, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"File downloaded: {save_path}")
    else:
        print(f"Failed to download file: {response.status_code} - {response.text}")

# 특정 이슈의 첨부파일을 다운로드하는 함수
def fetch_attachments(issue_key):
    issue_url = f"{jira_base_url}/rest/api/2/issue/{issue_key}"  # 특정 이슈의 URL
    response = requests.get(issue_url, headers=headers, auth=auth)

    if response.status_code == 200:
        data = response.json()
        issue_summary = data["fields"]["summary"]
        attachments = data["fields"]["attachment"]

        if not attachments:
            print(f"No attachments found for issue {issue_key}.")
            return

        # 폴더 경로 생성
        folder_name = clean_folder_name(f"{issue_key} - {issue_summary}")
        save_dir = os.path.join(download_dir, folder_name)
        create_directory(save_dir)

        # 첨부파일 다운로드
        for attachment in attachments:
            attachment_url = attachment["content"]
            file_name = attachment["filename"]
            save_path = os.path.join(save_dir, file_name)
            download_file(attachment_url, save_path)
    else:
        print(f"Failed to fetch issue details: {response.status_code} - {response.text}")

# 실행 부분
if __name__ == "__main__":
    issue_key = input("Enter the issue key (e.g., ACCO-16): ").strip()  # 사용자 입력
    fetch_attachments(issue_key)