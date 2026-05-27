import os
import shutil
import re
from fastapi import HTTPException, UploadFile, File, status

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "app/public")


def _copy_existing_files(src, dst):
    if not os.path.exists(src):
        return
    for root, dirs, files in os.walk(src):
        rel_path = os.path.relpath(root, src)
        dest_dir = os.path.join(dst, rel_path) if rel_path != "." else dst
        os.makedirs(dest_dir, exist_ok=True)
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_dir, file)
            try:
                shutil.copy2(src_file, dest_file)
            except Exception as e:
                print(f"Failed to copy {src_file} to {dest_file}: {e}")


try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except Exception as e:
    # If it fails (e.g. read-only filesystem on Vercel), fall back to /tmp/public
    print(f"Warning: Failed to create upload directory '{UPLOAD_DIR}' ({e}). Falling back to temporary directory.")
    fallback_dir = "/tmp/public"
    try:
        os.makedirs(fallback_dir, exist_ok=True)
        # Copy existing public files to /tmp/public so they can be read/served
        _copy_existing_files(UPLOAD_DIR, fallback_dir)
        UPLOAD_DIR = fallback_dir
    except Exception as fallback_err:
        print(f"Error: Failed to create fallback directory '{fallback_dir}': {fallback_err}")



def sanitize_filename(filename: str) -> str:
    """Sanitize filename by replacing invalid characters with underscores.
    
    """
    # Replace invalid filename characters with underscore
    invalid_chars = r'[/\\:*?"<>|]'
    sanitized = re.sub(invalid_chars, '_', filename)
    return sanitized


def handle_upload(
    new_filename: str,
    file: UploadFile = File(...),
    type: str = "contact",
):
    try:
        directory_path = os.path.join(UPLOAD_DIR, type)
        os.makedirs(directory_path, exist_ok=True)
        save_path = os.path.join(directory_path, new_filename)
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file.file.close()
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload file: {str(e)}",
        )


def delete_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
