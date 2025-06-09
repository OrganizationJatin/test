import os
import json
import requests
import base64
from nacl import encoding, public  

GITHUB_API = "https://api.github.com"
ORG_NAME = os.getenv("ORG")
REPO = os.getenv("REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

SECRETS_JSON = os.getenv("SECRETS_JSON", "{}")
VARIABLES_JSON = os.getenv("VARIABLES_JSON", "{}")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


def get_public_key():
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


def create_secret(name: str, value: str, key_data):
    encrypted_value = encrypt_secret(key_data['key'], value)
    url = f"{GITHUB_API}/repos/{ORG_NAME}/{REPO}/actions/secrets/{name}"
    payload = {
        "encrypted_value": encrypted_value,
        "key_id": key_data['key_id']
    }
    response = requests.put(url, headers=HEADERS, json=payload)
    if response.status_code in [201, 204]:
        print(f"Secret '{name}' created.")
    else:
        print(f"Failed to create secret '{name}': {response.status_code} - {response.text}")


def create_variable(name: str, value: str):
    url = f"{GITHUB_API}/repos/{ORG_NAME}/{REPO}/actions/variables/{name}"
    payload = {"name": name, "value": value}
    print(f"\nCreating variable at {url}")
    print(f"Payload: {payload}")
    response = requests.put(url, headers=HEADERS, json=payload)
    if response.status_code in [201, 204]:
        print(f"Variable '{name}' created.")
    else:
        print(f"Failed to create variable '{name}': {response.status_code}")
        print(f"Response: {response.text}")


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

    if secrets:
        key_data = get_public_key()
        for name, value in secrets.items():
            create_secret(name, value, key_data)

    if variables:
        for name, value in variables.items():
            create_variable(name, value)


if __name__ == "__main__":
    main()
