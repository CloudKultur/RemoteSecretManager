import requests
import os
import json
from dotenv import load_dotenv
from pathlib import Path

from DatabaseModel import Project, Credentials


class GitlabService:
    DOMAIN_URL = "https://gitlab.com/api/v4"
    GROUPS_URL = "/groups"
    PROJECTS_URL = "/projects"
    USER_URL = "/user"
    USER_PROJECTS_URL = "/users/{0}/projects"
    USER_GROUPS = "/groups"
    GROUPS_PROJECTS_URL = "/groups/{0}/projects"
    PROJECT_VARIABLES_URL ="/projects/{0}/variables"

    def __init__(self):
        load_environment()
        self.Token = os.environ.get("TOKEN")
        self.header = {"Authorization":"Bearer {}".format(self.Token)}

    def get_user_id(self):
        result = requests.get(self.DOMAIN_URL + self.USER_URL, headers=self.header)
        if result.status_code == 200:
            result_json = json.loads(result.text)
            return result_json["id"]

    def get_all_projects_by_user(self, user_id):
        projects = []
        result = requests.get((self.DOMAIN_URL + self.USER_PROJECTS_URL).format(user_id), headers=self.header)
        if result.status_code == 200:
            result_json = json.loads(result.text)
            for project in result_json:
                projects.append(Project(project["id"], project["name_with_namespace"]))

        groups = self.get_all_groups_by_user()
        for group in groups:
            group_projects = self.get_all_projects_by_group(group)
            for project in group_projects:
                projects.append(project)
        return projects

    def get_all_groups_by_user(self):
        groups = []
        result = requests.get(self.DOMAIN_URL + self.USER_GROUPS, headers=self.header)
        if result.status_code == 200:
            result_json = json.loads(result.text)
            for group in result_json:
                groups.append(group["id"])
        return groups

    def get_all_projects_by_group(self, group_id):
        projects = []
        result = requests.get((self.DOMAIN_URL + self.GROUPS_PROJECTS_URL).format(group_id), headers=self.header)
        if result.status_code == 200:
            result_json = json.loads(result.text)
            for project in result_json:
                projects.append(Project(project["id"], project["name_with_namespace"]))
        return projects

    def get_keys_of_project(self, project_id):
        keys = []
        new_pages = True
        request_url = (self.DOMAIN_URL + self.PROJECT_VARIABLES_URL).format(project_id)
        while new_pages:
            result = requests.get(request_url, headers=self.header)
            if result.status_code == 200:
                result_json = json.loads(result.text)
                for key in result_json:
                    keys.append(Credentials(key["key"], key["value"], key["environment_scope"], project_id, key["protected"], key["masked"], key["raw"], key["description"], key["variable_type"]))
                if result.links.get('next'):
                    new_pages = True
                    request_url = result.links['next']['url']
                else:
                    new_pages = False
        return keys
    
    def create_key_for_project(self, project_id, key):
        request_url = (self.DOMAIN_URL + self.PROJECT_VARIABLES_URL).format(project_id)
        payload = key.credentials_to_forms()
        result = requests.post(request_url, headers=self.header, data=payload)
        if result.status_code != 201:
            print("[!] Error occured")
            print(result.text)
    
    def update_key_for_project(self, project_id, key):
        request_url = (self.DOMAIN_URL + self.PROJECT_VARIABLES_URL + "/{1}").format(project_id, key.key)
        payload = key.credentials_to_forms()
        result = requests.put(request_url, params="filter[environment_scope]={0}".format(key.environment), headers=self.header, data=payload)
        if result.status_code != 200:
            print("[!] Error occured")
            print(result.text)

    def delete_key_for_project(self, project_id, key, env):
        request_url = (self.DOMAIN_URL + self.PROJECT_VARIABLES_URL + "/{1}").format(project_id, key)
        result = requests.delete(request_url, params="filter[environment_scope]={0}".format(env), headers=self.header)
        if result.status_code != 204:
            print("[!] Error occured")
            print(result.text)

def load_environment():
    dotent_path = Path.home() / Path(".gcm/.env")
    if not dotent_path.exists():
        print("[!] .env file not found in ~/.gcm/.env, creating...")
        token = input("Gitlab Token: ")
        dotent_path.parent.mkdir(exist_ok=True, parents=True)
        f = dotent_path.open("w", encoding="utf-8")
        f.write("TOKEN=" + token)
        f.close
    load_dotenv(dotenv_path=dotent_path)


    