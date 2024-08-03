import os
import re
import json
import sys
import requests
from typing import List, Optional
from typing import Optional
import re

TITLE_PATTERNS: List[str] = [
    # Pull Request Title Check for DEV to UAT
    r"[A-Za-z]{8}-(\d{1}) .+",  # Matches titles like ABCDEFGH-1 followed by a space and more characters.
    r"[A-Za-z]{8}+-(\d{1})+ .+",  # For Example: ARCHTECH-1 Formats.
    r"[A-Za-z]{8}+-\d{4}+ .+",  # For Example: ARCHTECH-123 Formats..
    r"[CHG]{3}+\d{10}+ .+",  # For Example: CHG1234567890 ...
    r"[INC]{3}+\d{10}+ .+",  # For Example: INC0025427287....
    r"DEV.to.UAT.*",  # For Example: DEV.to.UAT Test Pull Request..
    r"UAT.to.PRD.*",  # For Example: UAT to PRD Test Pull Request..
    r"PRD.to.DEV.*",  # For Example: PRD to DEV Test Pull Request..
    r"ARCHTECH-\d{1}+"  # Test Pull Request ARCHTECH-1
    # r"\b[A-Za-z]{8}-(\d{1}+)\b"
]

JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "https://XXXXXXX.atlassian.net")
JIRA_API_TOKEN = os.environ.get(
    "JIRA_API_TOKEN",
    "XXXXXXXXXXXXXX",
)
JIRA_USER_EMAIL = os.environ.get("JIRA_USER_EMAIL", "XXXXXXX@gmail.com")


def extract_jira_id(title: str) -> Optional[str]:
    # Regex to extract JIRA ID from title
    match = re.search(r"[A-Za-z]{8}-(\d+)", title)
    
    # match_a = re.search(r"[CHG]{3}+\d{10}+ .+", title)
    
    return match.group(0) if match else None

    # return match_a.group(0) if match_a else None

def is_jira_issue_valid(jira_id: str) -> bool:
    url = f"{JIRA_BASE_URL}/rest/api/2/issue/{jira_id}"
    headers = {
        "Authorization": f"Basic {JIRA_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            url, headers=headers, auth=(JIRA_USER_EMAIL, JIRA_API_TOKEN)
        )
        if response.status_code == 200:
            return True
        else:
            print(f"JIRA issue check failed with status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"Error in connecting to JIRA: {e}")
        return False
    # return response.status_code == 200


def check_pr_title(title: str, patterns: List[str]) -> bool:
    return any(re.search(pattern, title) for pattern in patterns)


def main():
    try:
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if not event_path:
            print("❌❌GITHUB_EVENT_PATH environment variable not set.❌❌")
            sys.exit(1)

        with open(event_path) as f:
            data = json.load(f)

        pr_title = data.get("pull_request", {}).get("title")
        if not pr_title:
            print(
                "❌❌PR doesn't have a title, please add one that follows our guidelines.❌❌"
            )
            sys.exit(1)

        if check_pr_title(pr_title, TITLE_PATTERNS):
            jira_id = extract_jira_id(pr_title)
            if not jira_id:
                print(
                    "❌❌ Extracted JIRA ID is empty or null. Please check the PR title format.❌❌"
                )
                sys.exit(1)

            jira_validity = jira_id and is_jira_issue_valid(jira_id)
            if jira_validity is True:
                print("✅✅ PR Title and JIRA ID are Valid.✅✅")
            elif jira_validity is False:
                print("❌❌ JIRA ID is invalid or not found.❌❌")
                sys.exit(1)
            else:
                print("❌❌Error occurred while validating JIRA ID❌❌")
                sys.exit(1)
        else:
            print(
                "❌❌ PR title is invalid. It does not match any of the required patterns.❌❌"
            )
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()