import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests

def get_plugin(org: str, repo: str, artifact_name: str, output_path: Path, workflow_name: str = None,
               workflow_id: str = None):
    repo_endpoint = f'https://api.github.com/repos/{org}/{repo}'

    if workflow_id is None:
        workflows = requests.get(f"{repo_endpoint}/actions/workflows").json()

        workflow_id = next(x for x in workflows["workflows"] if x['name'] == workflow_name)["id"]

    runs = requests.get(f"{repo_endpoint}/actions/workflows/{workflow_id}/runs",
                        params={"branch": "master", "status": "success"}).json()

    if runs['total_count'] >= 0:
        latest_run = runs['workflow_runs'][0]

        artifacts_url = latest_run['artifacts_url']

        artifacts = requests.get(artifacts_url).json()['artifacts']

        archive_download_url = next(x for x in artifacts if x['name'] == artifact_name)['archive_download_url']

        with NamedTemporaryFile(delete=True) as f:
            r = requests.get(archive_download_url, auth=("derongan", "<>"),
                             allow_redirects=True)

            f.write(r.content)

            with zipfile.ZipFile(f) as fz:
                fz.extractall(output_path)


if __name__ == "__main__":
    get_plugin("MineInAbyss", "StaminaClimb", "package", Path.cwd()/'../plugins', workflow_name="Java CI")
    get_plugin("MineInAbyss", "DangerousWaters", "package", Path.cwd()/'../plugins', workflow_name="Java CI")
    get_plugin("MineInAbyss", "MineInAbyss", "package", Path.cwd()/'../plugins', workflow_name="Java CI")
    get_plugin("MineInAbyss", "DeeperWorld", "package", Path.cwd()/'../plugins', workflow_name="Java CI")
    get_plugin("MineInAbyss", "geary", "package", Path.cwd()/'../plugins', workflow_name="Java CI")

