import argparse
import csv
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests


def get_plugin(org: str, repo: str, artifact_name: str, output_path: Path, workflow_name: str = None,
               workflow_id: str = None, auth: tuple = None):
    repo_endpoint = 'https://api.github.com/repos/{org}/{repo}'.format(org=org, repo=repo)

    if workflow_id is None:
        workflows = requests.get("{repo_endpoint}/actions/workflows".format(repo_endpoint=repo_endpoint),
                                 auth=auth).json()

        workflow_id = next(x for x in workflows["workflows"] if x['name'] == workflow_name)["id"]

    runs = requests.get("{repo_endpoint}/actions/workflows/{workflow_id}/runs".format(repo_endpoint=repo_endpoint,
                                                                                      workflow_id=workflow_id),
                        auth=auth,
                        params={"branch": "master", "status": "success"}).json()

    if runs['total_count'] >= 0:
        latest_run = runs['workflow_runs'][0]

        artifacts_url = latest_run['artifacts_url']

        artifacts = requests.get(artifacts_url, auth=auth).json()['artifacts']

        archive_download_url = next(x for x in artifacts if x['name'] == artifact_name)['archive_download_url']

        with NamedTemporaryFile(delete=True) as f:
            r = requests.get(archive_download_url, auth=auth,
                             allow_redirects=True)

            f.write(r.content)

            with zipfile.ZipFile(f) as fz:
                if len(fz.namelist()) != 1:
                    print("Artifact should have only one jar")
                    return
                zipinfo = fz.getinfo(fz.namelist()[0])

                fz.extract(zipinfo, str(output_path))


def process_line(values: list, output_dir: str, auth: tuple):
    org_name, repo_name, artifact_name, workflow_name = values

    print("Fetching plugin {repo_name}...".format(repo_name=repo_name))
    get_plugin(org_name, repo_name, artifact_name, Path(output_dir), workflow_name=workflow_name, auth=auth)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download Plugin Jars')
    parser.add_argument('-u', '--username', type=str, help='github username', required=True)
    parser.add_argument('-t', '--token', type=str, help='github token', required=True)
    parser.add_argument('file', type=argparse.FileType('r'), help='path to repo file')
    parser.add_argument('output_dir', type=str, help='output directory')

    args = parser.parse_args()

    auth = (args.username, args.token)

    repo_reader = csv.reader(args.file, skipinitialspace=True)
    for row in repo_reader:
        process_line(row, args.output_dir, auth)
