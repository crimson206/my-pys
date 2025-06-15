import subprocess
import re
import os

def get_github_token():
    result = subprocess.run(['gh', 'auth', 'status', '-t'], 
                          capture_output=True, text=True)
    output = result.stdout + result.stderr
    match = re.search(r'(gh[pous]_[A-Za-z0-9_]+)', output)
    return match.group(1) if match else None

def run_semantic_release():
    token = get_github_token()
    if not token:
        print("Token not found.")
        return False

    env = {'GH_TOKEN': token}
    result = subprocess.run(['semantic-release', 'version'], 
                          env={**os.environ, **env})
    return result.returncode == 0

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
    subprocess.run(['gh', 'release', 'delete', tag_name, '--yes'])

    print(f"Tag '{tag_name}' deleted successfully! Ignore the note message.")
    return True

# Usage example
run_semantic_release()
clean_tag('v3.0.1')