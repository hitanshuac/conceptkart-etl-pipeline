import os

from huggingface_hub import HfApi


def upload():
    api = HfApi()
    repo_id = os.getenv("HF_SPACE_REPO")
    token = os.getenv("HF_TOKEN")

    if not repo_id or not token:
        print("Error: HF_SPACE_REPO or HF_TOKEN environment variables not set.")
        exit(1)

    print(f"Uploading to Hugging Face Space: {repo_id}")

    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type="space",
        token=token,
        ignore_patterns=[".git/*", "data/*", "__pycache__/*", "*.parquet"],
    )
    print("Upload complete!")


if __name__ == "__main__":
    upload()
