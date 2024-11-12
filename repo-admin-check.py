from github import Github
import os
from os.path import join, dirname
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = join(dirname(__file__), '.env')  # Use __file__ instead of _file_
load_dotenv(dotenv_path)
access_token = os.getenv("GITHUB_TOKEN")
organization_name = os.getenv("ORG")

if not access_token:
    print("GitHub token is not set.")
    exit(1)
if not organization_name:
    print("Organization name is not set.")
    exit(1)

# Connect to GitHub
g = Github(access_token)

try:
    org = g.get_organization(organization_name)
except Exception as e:
    print(f"Error retrieving organization: {e}")
    exit(1)

# Generate Markdown table header
markdown_table = "| Repo Name | Teams (with Admin Role) | Members (with Admin Role) |\n"
markdown_table += "|-----------|--------------------------|---------------------------|\n"

# Collect data for each repository
for repo in org.get_repos():
    print(f"Checking repository: {repo.name}")
    
    # Collect teams with admin role
    admin_teams = [team.name for team in repo.get_teams() if team.permission == "admin"]

    # Collect members with admin role
    admin_members = [member.login for member in repo.get_collaborators(permission="admin")]

    # Add row to Markdown table
    markdown_table += f"| {repo.name} | {', '.join(admin_teams)} | {', '.join(admin_members)} |\n"

# Print the Markdown table so it can be captured by the GitHub Actions workflow
print(markdown_table)
