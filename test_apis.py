import requests
import string
import random

BASE_URL = "http://localhost:8000/api/v1"

def generate_random_email():
    random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
    return f"test_{random_str}@example.com"

def test_apis():
    print("=== Starting API Tests ===")
    
    # 1. Register a new user
    email = generate_random_email()
    password = "password123"
    register_data = {
        "email": email,
        "full_name": "Test User",
        "password": password
    }
    print(f"\n[1] Registering user: {email}")
    res = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(res.status_code, res.text)
    if res.status_code != 201:
        print("Registration failed, stopping.")
        return

    # 2. Login to get token
    print(f"\n[2] Logging in...")
    login_data = {
        "username": email,
        "password": password
    }
    res = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    print(res.status_code, res.text)
    if res.status_code != 200:
        print("Login failed, stopping.")
        return
    
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create Workspace
    print(f"\n[3] Creating Workspace...")
    workspace_data = {"name": "Test Workspace"}
    res = requests.post(f"{BASE_URL}/workspaces/", json=workspace_data, headers=headers)
    print(res.status_code, res.text)
    if res.status_code != 201:
        print("Workspace creation failed, stopping.")
        return
    workspace_id = res.json()["id"]
    
    # 4. Get Workspaces
    print(f"\n[4] Getting Workspace...")
    res = requests.get(f"{BASE_URL}/workspaces/{workspace_id}", headers=headers)
    print(res.status_code, res.text)
    
    # 5. Create Project inside Workspace
    print(f"\n[5] Creating Project in Workspace {workspace_id}...")
    project_data = {"name": "Test Project", "description": "This is a test project"}
    res = requests.post(f"{BASE_URL}/workspaces/{workspace_id}/projects", json=project_data, headers=headers)
    print(res.status_code, res.text)
    if res.status_code != 201:
        print("Project creation failed, stopping.")
        return
    project_id = res.json()["id"]
    
    # 6. Create Task inside Project
    print(f"\n[6] Creating Task in Project {project_id}...")
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "status": "TODO",
        "priority": "MEDIUM"
    }
    res = requests.post(f"{BASE_URL}/projects/{project_id}/tasks", json=task_data, headers=headers)
    print(res.status_code, res.text)
    if res.status_code != 201:
        print("Task creation failed, stopping.")
        return
    task_id = res.json()["id"]
    
    # 7. Get Tasks in Project
    print(f"\n[7] Getting Tasks for Project {project_id}...")
    res = requests.get(f"{BASE_URL}/projects/{project_id}/tasks", headers=headers)
    print(res.status_code, res.text)
    
    print("\n=== API Tests Completed Successfully! ===")

if __name__ == "__main__":
    test_apis()
