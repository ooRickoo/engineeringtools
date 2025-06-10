import json
import os
import argparse

LDAP_DATA_DIR = 'ldap-data'
USERS_FILE = os.path.join(LDAP_DATA_DIR, 'users.json')
GROUPS_FILE = os.path.join(LDAP_DATA_DIR, 'groups.json')

def load_data(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as f:
        return json.load(f)

def save_data(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def add_user(username, password, **kwargs):
    users = load_data(USERS_FILE)
    if username in users:
        print(f"Error: User '{username}' already exists.")
        return
    users[username] = {'password': password, **kwargs}
    save_data(USERS_FILE, users)
    print(f"User '{username}' added successfully.")

def remove_user(username):
    users = load_data(USERS_FILE)
    if username not in users:
        print(f"Error: User '{username}' not found.")
        return
    del users[username]
    save_data(USERS_FILE, users)
    print(f"User '{username}' removed successfully.")

def modify_user(username, password=None, **kwargs):
    users = load_data(USERS_FILE)
    if username not in users:
        print(f"Error: User '{username}' not found.")
        return
    if password:
        users[username]['password'] = password
    for key, value in kwargs.items():
        if value is not None: # Allow unsetting attributes by passing None or handle explicitly
            users[username][key] = value
        elif key in users[username]: # If value is None and key exists, remove it
            del users[username][key]

    save_data(USERS_FILE, users)
    print(f"User '{username}' modified successfully.")

def add_group(group_name, members=None):
    groups = load_data(GROUPS_FILE)
    if group_name in groups:
        print(f"Error: Group '{group_name}' already exists.")
        return
    groups[group_name] = {'members': members if members else []}
    save_data(GROUPS_FILE, groups)
    print(f"Group '{group_name}' added successfully.")

def remove_group(group_name):
    groups = load_data(GROUPS_FILE)
    if group_name not in groups:
        print(f"Error: Group '{group_name}' not found.")
        return
    del groups[group_name]
    save_data(GROUPS_FILE, groups)
    print(f"Group '{group_name}' removed successfully.")

def modify_group_members(group_name, add_members=None, remove_members=None):
    groups = load_data(GROUPS_FILE)
    if group_name not in groups:
        print(f"Error: Group '{group_name}' not found.")
        return

    if add_members:
        groups[group_name]['members'] = list(set(groups[group_name].get('members', []) + add_members))
    if remove_members:
        groups[group_name]['members'] = [m for m in groups[group_name].get('members', []) if m not in remove_members]
    
    save_data(GROUPS_FILE, groups)
    print(f"Group '{group_name}' members modified successfully.")

def main():
    parser = argparse.ArgumentParser(description="LDAP Admin Tool")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # User commands
    user_parser = subparsers.add_parser('user', help='Manage users')
    user_subparsers = user_parser.add_subparsers(dest='action', required=True)

    add_user_parser = user_subparsers.add_parser('add', help='Add a new user')
    add_user_parser.add_argument('username', help='Username')
    add_user_parser.add_argument('password', help='Password')
    add_user_parser.add_argument('--attrs', help='Additional attributes as a JSON string (e.g., \'{"email": "user@example.com"}\')', type=json.loads, default={})


    remove_user_parser = user_subparsers.add_parser('remove', help='Remove a user')
    remove_user_parser.add_argument('username', help='Username')

    modify_user_parser = user_subparsers.add_parser('modify', help='Modify a user')
    modify_user_parser.add_argument('username', help='Username')
    modify_user_parser.add_argument('--password', help='New password (optional)')
    modify_user_parser.add_argument('--attrs', help='Attributes to modify as a JSON string (e.g., \'{"email": "new@example.com", "phone": null}\') to remove phone', type=json.loads, default={})


    # Group commands
    group_parser = subparsers.add_parser('group', help='Manage groups')
    group_subparsers = group_parser.add_subparsers(dest='action', required=True)

    add_group_parser = group_subparsers.add_parser('add', help='Add a new group')
    add_group_parser.add_argument('group_name', help='Group name')
    add_group_parser.add_argument('--members', nargs='*', help='List of member usernames', default=[])

    remove_group_parser = group_subparsers.add_parser('remove', help='Remove a group')
    remove_group_parser.add_argument('group_name', help='Group name')

    modify_group_parser = group_subparsers.add_parser('modify', help='Modify group members')
    modify_group_parser.add_argument('group_name', help='Group name')
    modify_group_parser.add_argument('--add-members', nargs='*', help='Usernames to add to the group', default=[])
    modify_group_parser.add_argument('--remove-members', nargs='*', help='Usernames to remove from the group', default=[])

    args = parser.parse_args()

    if args.command == 'user':
        if args.action == 'add':
            add_user(args.username, args.password, **args.attrs)
        elif args.action == 'remove':
            remove_user(args.username)
        elif args.action == 'modify':
            modify_user(args.username, args.password, **args.attrs)
    elif args.command == 'group':
        if args.action == 'add':
            add_group(args.group_name, args.members)
        elif args.action == 'remove':
            remove_group(args.group_name)
        elif args.action == 'modify':
            modify_group_members(args.group_name, args.add_members, args.remove_members)

if __name__ == '__main__':
    main()
