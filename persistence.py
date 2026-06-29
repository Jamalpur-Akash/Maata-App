import os
import shutil
from pathlib import Path

HF_TOKEN = os.environ.get("HF_TOKEN", "")
DATASET_REPO = "Maata-team/Maata-data"

def load_all_from_hub():
    if not HF_TOKEN:
        return
    try:
        from huggingface_hub import HfApi, hf_hub_download
        api = HfApi()
        try:
            all_files = list(api.list_repo_files(
                repo_id=DATASET_REPO,
                repo_type="dataset",
                token=HF_TOKEN
            ))
        except Exception:
            all_files = []
        for filepath in all_files:
            try:
                local_path = Path(filepath)
                local_path.parent.mkdir(parents=True, exist_ok=True)
                downloaded = hf_hub_download(
                    repo_id=DATASET_REPO,
                    filename=filepath,
                    repo_type="dataset",
                    token=HF_TOKEN,
                    local_dir="."
                )
                if str(downloaded) != str(local_path):
                    shutil.copy(downloaded, local_path)
            except Exception as e:
                print(f"Could not load {filepath}: {e}")
    except Exception as e:
        print(f"Hub load failed: {e}")

def save_file_to_hub(filepath):
    if not HF_TOKEN:
        return
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        api.upload_file(
            path_or_fileobj=str(filepath),
            path_in_repo=str(filepath).replace("\\", "/"),
            repo_id=DATASET_REPO,
            repo_type="dataset",
            token=HF_TOKEN
        )
        print(f"Saved {filepath} to hub")
    except Exception as e:
        print(f"Could not save {filepath}: {e}")
