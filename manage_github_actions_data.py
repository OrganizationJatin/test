import os
import json
import requests
import base64
from nacl import encoding, public

GITHUB_API = "https://api.github.com"
ORG_NAME = os.getenv("ORG")
REPO = os.getenv("REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

ENVIRONMENT = os.getenv("ENVIRONMENT") or None
SECRETS_JSON = os.getenv("SECRETS_JSON", "{}")
VARIABLES_JSON = os.getenv("VARIABLES_JSON", "{}")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


def ensure_environment_exists(env_name: str):
    url = f"{GITHUB_API}/repos/{ORG_NAME}/{REPO}/environments/{env_name}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        print(f"Environment '{env_name}' already exists.")
        return

    if response.status_code == 404:
        print(f"Environment '{env_name}' does not exist. Creating it...")
        payload = {
            "wait_timer": 0,
            "deployment_branch_policy": {
                "protected_branches": True,
                "custom_branch_policies": False  # ✅ required and must be different from above
            }
        }
        create_response = requests.put(url, headers=HEADERS, json=payload)
        if create_response.status_code in [200, 201]:
            print(f"Environment '{env_name}' created successfully.")
        else:
            print(f"Failed to create environment '{env_name}': {create_response.status_code} - {create_response.text}")
            exit(1)
    else:
        print(f"Error checking environment '{env_name}': {response.status_code} - {response.text}")
        exit(1)


def get_public_key():
    if ENVIRONMENT:
        url = f"{GITHUB_API}/repos/{ORG_NAME}/{REPO}/environments/{ENVIRONMENT}/secrets/public-key"
    else:
        url = f"{GITHUB_API}/repos/{ORG_NAME}/{REPO}/actions/secrets/public-key"

    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def encrypt_secret(public_key: str, secret_value: str) -> str:
    public_key_bytes = base64.b64decode(public_key)
    pk = public.PublicKey(public_key_bytes)
    sealed_box = public.SealedBox(pk)
    encrypted = sealed_box.encrypt(secret_value.encode())
    return base64.b64encode(encrypted).decode()


def create_or_update_secret(name: str, value: str, key_data):
    encrypted_value = encrypt_secret(key_data['key'], value)

    if ENVIRONMENT:
        url = f"{GITHUB_API}/repos/{ORG_NAME}/{REPO}/environments/{ENVIRONMENT}/secrets/{name}"
    else:
        url = f"{GITHUB_API}/repos/{ORG_NAME}/{REPO}/actions/secrets/{name}"

    payload = {
        "encrypted_value": encrypted_value,
        "key_id": key_data['key_id']
    }

    response = requests.put(url, headers=HEADERS, json=payload)
    if response.status_code == 201:
        print(f"Secret '{name}' created.")
    elif response.status_code == 204:
        print(f"Secret '{name}' updated.")
    else:
        print(f"Failed to create/update secret '{name}': {response.status_code} - {response.text}")


def create_or_update_variable(name: str, value: str):
    base = f"{GITHUB_API}/repos/{ORG_NAME}/{REPO}"
    if ENVIRONMENT:
        get_url = f"{base}/environments/{ENVIRONMENT}/variables/{name}"
        post_url = f"{base}/environments/{ENVIRONMENT}/variables"
    else:
        get_url = f"{base}/actions/variables/{name}"
        post_url = f"{base}/actions/variables"

    get_resp = requests.get(get_url, headers=HEADERS)

    if get_resp.status_code == 200:
        patch_resp = requests.patch(get_url, headers=HEADERS, json={"value": value})
        if patch_resp.status_code == 204:
            print(f"Variable '{name}' updated.")
        else:
            print(f"Failed to update variable '{name}': {patch_resp.status_code} - {patch_resp.text}")
    elif get_resp.status_code == 404:
        post_resp = requests.post(post_url, headers=HEADERS, json={"name": name, "value": value})
        if post_resp.status_code == 201:
            print(f"Variable '{name}' created.")
        else:
            print(f"Failed to create variable '{name}': {post_resp.status_code} - {post_resp.text}")
    else:
        print(f"Error checking variable '{name}': {get_resp.status_code} - {get_resp.text}")


def main():
    if not all([ORG_NAME, REPO, GITHUB_TOKEN]):
        print("Missing ORG, REPO, or GITHUB_TOKEN.")
        exit(1)

    try:
        secrets = json.loads(SECRETS_JSON) if SECRETS_JSON.strip() else {}
        variables = json.loads(VARIABLES_JSON) if VARIABLES_JSON.strip() else {}
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON input: {e}")
        exit(1)

    # Ensure environment exists before doing anything
    if ENVIRONMENT:
        ensure_environment_exists(ENVIRONMENT)

    if secrets:
        key_data = get_public_key()
        for name, value in secrets.items():
            create_or_update_secret(name, value, key_data)

    if variables:
        for name, value in variables.items():
            create_or_update_variable(name, value)


if __name__ == "__main__":
    main()
