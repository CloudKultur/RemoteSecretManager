import argparse
import base64
import os
import sys
import subprocess
from hashlib import sha256

from DatabaseService import DatabaseService
from GitlabService import GitlabService
from Converter import *
from cryptography.fernet import Fernet

db = DatabaseService("credentials")
service = GitlabService()


print_format_string_header = "{: <28} {:<48} {:<38} {:<18} {:<18} {:<18}"
print_format_string_body = "{: <20.20} {:<40.40} {:<30.30} {:<10} {:<10} {:<10}"


def main():
    parser = argparse.ArgumentParser(description='A credentials sync tool for GitLab')
    exclusive_options = parser.add_mutually_exclusive_group()
    exclusive_options.add_argument("--pull", help="populate the database", action="store_true")
    exclusive_options.add_argument("--rm", help="flushes all data", action="store_true")
    exclusive_options.add_argument("--select", help="selects project and pull keys", nargs="?")
    exclusive_options.add_argument("--projects", help="show known projects", action="store_true")
    exclusive_options.add_argument("--keys", help="update current projects keys", action="store_true")
    exclusive_options.add_argument("--show", help="print the environment variables to console", nargs="?", const=True)
    parser.add_argument("--env", help="Filter variables by environment", nargs="?", default=None)
    subparsers = parser.add_subparsers(help="", dest="subparser")
    use_parser = subparsers.add_parser("use", help="execute command with environment")
    use_parser.add_argument("use", help="enter the command which uses the variables", nargs="*", metavar="use")
    key_update_parser = subparsers.add_parser("set", help="sets or updates a key")
    key_update_parser.add_argument("-m", "--masked", action="store_true")
    key_update_parser.add_argument("-p", "--protected", action="store_true")
    key_update_parser.add_argument("-r", "--raw", action="store_true")
    key_update_parser.add_argument("-e", "--env", help="environment for variable", nargs='?', default='*')
    key_update_parser.add_argument("key", help="variable name", metavar="key")
    key_update_parser.add_argument("value", help="variable value", nargs='*', metavar="value")
    key_delete_parser = subparsers.add_parser("unset", help="removes a key")
    key_delete_parser.add_argument("-e", "--env", help="environment for variable", nargs='?', default='*')
    key_delete_parser.add_argument("key", help="variable name for deletion", metavar="key")
    key_show_parser = subparsers.add_parser("show", help="get a variable with full value")
    key_show_parser.add_argument("key", help="get a variable with full value", metavar="key", nargs="?")
    key_show_parser.add_argument("-e", "--env", help="environment for variable", nargs='?', default='*')

    args = parser.parse_args()

    user_id = service.get_user_id()
    if user_id is None:
        print("[!] Oops, something went wrong fetching users id")
        sys.exit(2)

    f = Fernet(token_to_key(service.Token))

    # check basic actions
    if args.pull:
        all_projects = service.get_all_projects_by_user(user_id)
        for project in all_projects:
            db.table = db.PROJECT_TABLE
            where = dict(key=["id"], value=[project.id])
            db.create_or_update(vars(project), where, db.PROJECT_TABLE)
        update_keys()
        print("[*] Done!")

    elif args.rm:
        db.delete_database()

    elif args.select:
        project = db.change_project(args.select)
        if not project:
            print("[!] Project not found")
            sys.exit(3)
        update_keys()
        print("[*] Done!")

    elif args.projects:
        projects = db.read(db.PROJECT_TABLE)
        parsed = []
        for project in projects:
            parsed.append(project_from_database(project))
        parsed.sort(key=lambda x: x.name)
        print("{: >18} {: >28}".format(set_bold("ID"), set_bold("Project Name")))
        for project in parsed:
            print(project)

    elif args.keys:
        update_keys()
        print("[*] Done!")

    elif args.subparser == "show":
        keys = list()
        if not args.key:
            credentials = db.read(db.CREDENTIALS_TABLE)
        else:
            credentials = db.read_where(dict(key="key", value=args.key), db.CREDENTIALS_TABLE)
        for c in credentials:
            cred = credentials_from_database(c)
            if args.env != "*" and cred.environment not in [args.env, "*"]:
                continue
            cred.value = f.decrypt(str.encode(cred.value)).decode("utf-8")
            keys.append(cred)
        print(print_format_string_header.format(set_bold("Environment"), set_bold("Key"), set_bold("Value"), set_bold("Protected"), set_bold("Masked"), set_bold("Raw")))
        for key in sorted(keys, key=lambda k:k.key):
            print(print_format_string_body.format(key.environment, key.key, key.value, bool_to_ticks(key.protected), bool_to_ticks(key.masked), bool_to_ticks(key.raw)))

    elif args.subparser == "use":
        env = {**os.environ}
        credentials = db.read(db.CREDENTIALS_TABLE)
        for c in credentials:
            cred = credentials_from_database(c)
            if args.env and cred.environment not in [args.env, "*"]:
                continue
            cred.value = f.decrypt(str.encode(cred.value)).decode("utf-8")
            env[cred.key] = cred.value
        try:
            with subprocess.Popen(args.use, env=env, bufsize=1, universal_newlines=True) as p:
                for line in p.stdout if p.stdout else []:
                    print(line, end='')
            if p.returncode != 0:
                raise subprocess.CalledProcessError(p.returncode, p.args)
        except subprocess.CalledProcessError as e:
            print(e.output)
        except Exception as e:
            print(e)

    elif args.subparser == "set":
        project = db.get_current_project()
        if (project == None):
            sys.exit(1)
        cred = Credentials(args.key, " ".join(args.value), args.env, project.id, args.protected, args.masked, args.raw)

        # if exists, update
        where = dict(key=["key", "environment"], value=[cred.key, cred.environment])
        result = db.read_where(where, db.CREDENTIALS_TABLE)
        if args.masked and len(cred.value) < 8:
                print("[!] Value must be at least 8 characters to be masked!") 
                sys.exit(2)
        if len(result) > 0:
            service.update_key_for_project(project.id, cred)
        else:
            service.create_key_for_project(project.id, cred)
        update_keys()
        print("[*] Done!")
        
    elif args.subparser == "unset":
        project = db.get_current_project()
        if (project == None):
            sys.exit(1)
        service.delete_key_for_project(project.id, args.key, args.env)
        print("[*] Done!")

    sys.exit(0)


def update_keys():
    project = db.get_current_project()
    f = Fernet(token_to_key(service.Token))
    if project:
        keys = service.get_keys_of_project(project.id)
        db.delete_table_contents(db.CREDENTIALS_TABLE)
        for key in keys:
            key.value = f.encrypt(str.encode(key.value)).decode("utf-8")
            where = dict(key=["key", "environment"], value=[key.key, key.environment])
            db.create_or_update(vars(key), where, db.CREDENTIALS_TABLE)
    else:
        print("[!] No project selected")


def token_to_key(token):
    sha = sha256()
    sha.update(str.encode(token))
    hashed = sha.digest()
    return base64.urlsafe_b64encode(hashed)


def bool_to_ticks(value):
    result = u'\u2713' if value else u'\u2715'
    return result

def set_bold(string):
    return "\033[1m{0}\033[0m".format(string)


if __name__ == "__main__":
    main()
