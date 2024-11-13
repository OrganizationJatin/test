from github import Github
import os
import csv
from os.path import join, dirname
from dotenv import load_dotenv

# Load environment variables from .env
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
access_token = os.getenv("GITHUB_TOKEN")
organization_name = os.getenv("ORG")

if not access_token:
    print("GitHub token is not set.")
    exit(1)
if not organization_name:
    print("Organization name is not set.")
    exit(1)

g = Github(access_token)

try:
    org = g.get_organization(organization_name)
except Exception as e:
    print(f"Error retrieving organization: {e}")
    exit(1)

# Create the CSV file with headers
with open("admin_roles.csv", mode="w", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Repo Name", "Teams (with Admin Role)", "Members (with Admin Role)"])

    # Fetch repositories and admin roles
    for repo in org.get_repos():
        print(f"Checking repository: {repo.name}")
        
        admin_teams = [team.name for team in repo.get_teams() if team.permission == "admin"]
        admin_members = [member.login for member in repo.get_collaborators(permission="admin")]

        # Write row to CSV
        csv_writer.writerow([repo.name, ", ".join(admin_teams), ", ".join(admin_members)])

print("CSV file 'admin_roles.csv' has been generated successfully.")
