import argparse
import re
from pathlib import Path

import requests
import yaml


def download_plugin_from_github(org: str, repo: str, output_path: Path, artifacts=(r".*\..jar",), tag: str = None,
                                auth: tuple = None):
    repo_endpoint = 'https://api.github.com/repos/{org}/{repo}'.format(org=org, repo=repo)

    patterns = (re.compile(pattern) for pattern in artifacts)

    if tag:
        release_info = requests.get(
            "{repo_endpoint}/releases/tags/{tag}".format(repo_endpoint=repo_endpoint, tag=tag),
            auth=auth,
            params={"branch": "master", "status": "success"}).json()
    else:
        release_info = requests.get("{repo_endpoint}/releases/latest".format(repo_endpoint=repo_endpoint),
                                    auth=auth,
                                    params={"branch": "master", "status": "success"}).json()

    if "id" in release_info:
        jar_urls = {asset["name"]: asset["browser_download_url"] for asset in release_info.get("assets", []) if
                    any(pattern.match(asset["name"]) for pattern in patterns)}

        if not jar_urls:
            print("Release {} does not contain a matching asset".format(release_info["html_url"]))
            return

        for name, jar_url in jar_urls.items():
            with open(Path(output_path, name), "wb") as f:
                r = requests.get(jar_url, auth=auth,
                                 allow_redirects=True)

                f.write(r.content)
                print("{}/{} successfully fetched {}".format(org, repo, name))
    else:
        print("{}/{} does not contain a matching release".format(org, repo))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download Plugin Jars')
    parser.add_argument('-u', '--username', type=str, help='github username', required=True)
    parser.add_argument('-t', '--token', type=str, help='github token', required=True)
    parser.add_argument('file', type=argparse.FileType('r'), help='path to repo file')
    parser.add_argument('output_dir', type=str, help='output directory')

    args = parser.parse_args()

    auth = (args.username, args.token)

    config = yaml.safe_load(args.file)

    for org in config.get("github", []):
        org_name = org["org"]
        for repo_name, options in org["repos"].items():
            download_plugin_from_github(org_name, repo_name, args.output_dir,
                                        artifacts=options.get("artifacts", (r".*\.jar",)),
                                        tag=options.get("tag"), auth=auth)
