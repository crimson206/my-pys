import subprocess
import re
import os
import toml
from pathlib import Path

def get_github_token():
    result = subprocess.run(['gh', 'auth', 'status', '-t'], 
                          capture_output=True, text=True)
    output = result.stdout + result.stderr
    match = re.search(r'(gh[pous]_[A-Za-z0-9_]+)', output)
    return match.group(1) if match else None

def get_project_info():
    """Get project name and version from pyproject.toml"""
    try:
        with open('pyproject.toml', 'r') as f:
            data = toml.load(f)
        
        name = data['project']['name']
        version = data['project']['version']
        return name, version
    except Exception as e:
        print(f"Failed to read pyproject.toml: {e}")
        return None, None

def build_package():
    """Build the Python package"""
    print("Building package...")
    result = subprocess.run(['python', '-m', 'build'], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Build completed successfully!")
        return True
    else:
        print(f"Build failed: {result.stderr}")
        return False

def upload_assets(tag_name):
    """Upload built assets to GitHub release"""
    name, version = get_project_info()
    if not name or not version:
        return False
    
    # Expected file paths
    wheel_file = f"dist/{name}-{version}-py3-none-any.whl"
    tar_file = f"dist/{name}-{version}.tar.gz"
    
    files_to_upload = []
    for file_path in [wheel_file, tar_file]:
        if Path(file_path).exists():
            files_to_upload.append(file_path)
    
    if not files_to_upload:
        print("No build files found in dist/")
        return False
    
    cmd = ['gh', 'release', 'upload', tag_name] + files_to_upload
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"Assets uploaded to {tag_name}: {', '.join(files_to_upload)}")
        return True
    else:
        print(f"Upload failed: {result.stderr}")
        return False

def run_semantic_release(build=True, upload=True):
    token = get_github_token()
    if not token:
        print("Token not found.")
        return False

    if build:
        if not build_package():
            return False

    env = {'GH_TOKEN': token}
    result = subprocess.run(['semantic-release', 'version'], 
                          env={**os.environ, **env})
    
    if result.returncode != 0:
        return False
    
    if upload and build:
        # Get the latest tag for upload
        tag_result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], 
                                   capture_output=True, text=True)
        if tag_result.returncode == 0:
            tag_name = tag_result.stdout.strip()
            upload_assets(tag_name)
    
    return True

def clean_tag(tag_name=None):
    """Delete latest tag or specified tag from both local and remote"""
    
    if not tag_name:
        # Find latest tag
        result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            print("No tags found.")
            return False
        tag_name = result.stdout.strip()
    
    # Delete local tag
    subprocess.run(['git', 'tag', '-d', tag_name])
    
    # Delete remote tag
    subprocess.run(['git', 'push', 'origin', '--delete', tag_name])

    # Delete GitHub release (filter out note message)
    result = subprocess.run(['gh', 'release', 'delete', tag_name, '--yes'], 
                           capture_output=True, text=True)
    
    if result.returncode == 0:
        # Print output but filter out the "Note that" line
        output_lines = (result.stdout + result.stderr).strip().split('\n')
        filtered_lines = [line for line in output_lines if not line.startswith('! Note that')]
        if filtered_lines:
            print('\n'.join(filtered_lines))
    else:
        # Print error as is
        print(result.stderr.strip())
    
    print(f"Tag '{tag_name}' deleted successfully!")
    return True
