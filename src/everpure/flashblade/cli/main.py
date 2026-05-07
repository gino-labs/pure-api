import os
import json
import argparse
import requests

fb_token = os.environ["FB_TOKEN"]
fb_mgmt = os.environ["FB_MGMT"]
base = f"https://{fb_mgmt}/api/2.latest/"

def header():
    login_url = f"https://{fb_mgmt}/api/login"
    r = requests.post(login_url, headers={"api-token": fb_token})
    r.raise_for_status()
    header = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-auth-token": r.headers.get("x-auth-token")
    }
    return header

def _get(ep: str, **params):
    url = base + ep
    r = requests.get(url, headers=header(), params=params)
    r.raise_for_status()
    data = r.json()
    print(json.dumps(data["items"]))

def _post(ep: str):
    url = base + ep
    # TODO

def _patch(ep: str):
    url = base + ep
    # TODO

def _delete(ep: str):
    url = base + ep
    # TODO

def build_parser():
    parser = argparse.ArgumentParser(prog="fb")
    subparsers = parser.add_subparsers(dest="command", required=True)

    get = subparsers.add_parser("get", help="Get request")
    get.add_argument("endpoint")

    post = subparsers.add_parser("post", help="Post request")
    post.add_argument("endpoint")

    patch = subparsers.add_parser("patch", help="Patch request")
    patch.add_argument("endpoint")

    delete = subparsers.add_parser("delete", help="Delete request")
    delete.add_argument("endpoint")
    
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "get":
        _get(args.endpoint)
    elif args.command == "post":
        _post(args.endpoint)
    elif args.command == "patch":
        _patch(args.endpoint)
    elif args.command == "delete":
        _delete(args.endpoint)
    else:
        pass

if __name__ == "__main__":
    main()