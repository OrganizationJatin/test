#!/usr/bin/env python3
import os
import csv
import base64
from github import Github
import yaml

def classify_workflow(workflow_yaml):
    """
    Return (has_ci, has_cd) based on triggers and job keywords.
    """
    events = workflow_yaml.get('on', {})
    if isinstance(events, str):
        events = {events: None}
    ci_events = {'push', 'pull_request'}
    cd_events = {'release', 'deployment', 'deployment_status'}

    triggers = set(events.keys())
    has_ci = bool(triggers & ci_events)
    has_cd = bool(triggers & cd_events)

    # Inspect job names and environment keys for deploy/publish or test/build tasks
    for job_name, job in workflow_yaml.get('jobs', {}).items():
        name = job_name.lower()
        if 'deploy' in name or 'publish' in name or job.get('environment'):
            has_cd = True
        if 'test' in name or 'build' in name or 'lint' in name:
            has_ci = True

    return has_ci, has_cd


def main():
    token = os.getenv('GH_TOKEN')
    if not token:
        raise EnvironmentError('GITHUB_TOKEN not set')

    gh = Github(token)
    org = gh.get_organization('OrganizationJatin')  # Replace with your GitHub organization name
    repos = org.get_repos()

    report_dir = 'report'
    os.makedirs(report_dir, exist_ok=True)
    output_file = os.path.join(report_dir, 'actions_report.csv')

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['repo_name', 'using_actions', 'using_ci', 'using_cd'])

        for repo in repos:
            using = False
            ci_flag = False
            cd_flag = False
            try:
                contents = repo.get_contents('.github/workflows')
                for file in contents:
                    if file.name.lower().endswith(('.yml', '.yaml')):
                        using = True
                        raw = base64.b64decode(file.content)
                        data = yaml.safe_load(raw)
                        ci, cd = classify_workflow(data)
                        ci_flag |= ci
                        cd_flag |= cd
            except Exception:
                # No workflows directory or API error
                pass

            # Only write rows for repos actually using Actions
            if using:
                writer.writerow([repo.full_name, using, ci_flag, cd_flag])

    print(f'Report generated: {output_file}')

if __name__ == '__main__':
    main()
