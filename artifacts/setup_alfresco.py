import base64
import requests
import json
from os import environ
#from time import sleep
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# This sets up an Alfresco 7.0.0 instance to work with ArkCase
# It reads values from environment variables
# For example:
# ALFRESCO_BASE_URL = http://ec2-54-224-31-118.compute-1.amazonaws.com:8080
# ALFRESCO_ADMIN_USERNAME = admin
# ALFRESCO_ADMIN_PASSWORD = admin
# USERS = yasser
# GROUPS = ARKCASE_ENTITY_ADMINISTRATOR,ARKCASE_CONSUMER,ARKCASE_SUPERVISOR,ARKCASE_ADMINISTRATOR,ARKCASE_EXTERNAL,ARKCASE_CONTRIBUTOR
# SITES = acm
# CREATE_RM_SITE = true
# FOLDERS = Case Files,Complaints,Document Repositories,Expenses,People,Recycle Bin,Tasks,Timesheets,User Profile,Business Processes,Consultations,SAR,Requests
# ROOT_CATEGORY = ACM
# CATEGORIES = Case Files,Complaints,Document Repositories,Requests,Tasks,Consultations,SAR
# SITE_MEMBERSHIP_ROLE = SiteManager
# RM_ROLE = Records Management Administrator
# CONNECTION_RETRIES: 5
# CONNECTION_BACKOFF_FACTOR: 10


content_services_path = '/alfresco/api/-default-/public/alfresco/versions/1'
ags_services_path = '/alfresco/api/-default-/public/gs/versions/1'

hostname = environ['ALFRESCO_BASE_URL']
username = environ['ALFRESCO_ADMIN_USERNAME']
password = environ['ALFRESCO_ADMIN_PASSWORD']
base64string = base64.b64encode(bytes('%s:%s' % (username, password), 'ascii'))
headers = {"Authorization": "Basic %s" % base64string.decode('utf-8'), 'Content\u002DType': "application/json",
           "Accept": "application/json"}

line = environ.get('USERS', '')
users = line.split(',')

line = environ.get('GROUPS', '')
groups = line.split(',')

line = environ.get('SITES', '')
sites = line.split(',')

line = environ.get('FOLDERS', '')
folders = line.split(',')

site_membership_role = environ['SITE_MEMBERSHIP_ROLE']

line = environ['CREATE_RM_SITE']
create_rm_site = False
if line.lower() == 'true':
    create_rm_site = True

    line = environ['ROOT_CATEGORY']
    root_category = line.split(',')

    line = environ['CATEGORIES']
    rm_categories = line.split(',')

    rm_role = environ['RM_ROLE']


def handle_user(user_id):
    """Check if user exists, create it if it doesn't."""
    user_path = '/people'
    get_url = hostname + content_services_path + user_path + '/' + user_id

    got_user = requests.get(url=get_url, headers=headers)

    status_code = got_user.status_code

    if status_code == 200:
        print('User already exists, skipping creation of ' + user_id)
    elif status_code == 404:
        print('User doesn\'t exist, creating user with id ' + user_id)
        post_url = hostname + content_services_path + user_path
        user_payload = json.dumps(
            {'id': user_id, 'firstName': user_id, 'email': user_id + '@email.com', 'password': user_id})
        create_user = requests.post(post_url, data=user_payload, headers=headers)
        print('User created with below values')
        print(create_user.json())
    else:
        print(status_code)
        print('Unknown error occurred when checking user')


def handle_groups(group_id):
    """Check if group exists, create it if it doesn't."""
    group_path = '/groups'
    get_url = hostname + content_services_path + group_path + '/' + 'GROUP_' + group_id
    got_group = requests.get(url=get_url, headers=headers)

    status_code = got_group.status_code

    if status_code == 200:
        print('Group already exists, skipping creation of ' + group_id)
    elif status_code == 404:
        print('Group doesn\'t exist, creating group with id ' + group_id)
        post_url = hostname + content_services_path + group_path
        group_payload = json.dumps({'id': group_id, 'displayName': group_id})
        create_group = requests.post(post_url, data=group_payload, headers=headers)
        print('Group created with below values')
        print(create_group.json())
    else:
        print(status_code)
        print('Unknown error occurred when checking group')


def handle_folder(folder, site_id, site_guid):
    folder_payload = json.dumps({'name': folder, 'nodeType': 'cm:folder', 'relativePath': 'documentLibrary'})
    create_folder_url = hostname + content_services_path + '/nodes/' + site_guid + '/children'
    create_folder = requests.post(create_folder_url, data=folder_payload, headers=headers)
    status_code = create_folder.status_code
    if status_code == 201:
        print('Folder ' + folder + ' created in ' + site_id)
    elif status_code == 409:
        print('Folder with name ' + folder + ' already exists in ' + site_id)
    else:
        print(status_code)
        print('Unknown error occurred when creating folder')


def handle_site_memberships(member, role, site_path, site_id):
    user_role_payload = json.dumps({'role': role, 'id': member})
    if member.startswith('GROUP_'):
        assign_role_url = hostname + content_services_path + site_path + '/' + site_id + '/group-members'
    else:
        assign_role_url = hostname + content_services_path + site_path + '/' + site_id + '/members'
    assign_role = requests.post(assign_role_url, data=user_role_payload, headers=headers)
    status_code = assign_role.status_code
    if status_code == 409:
        print(member + ' is already a member of ' + site_id)
    elif status_code == 201:
        print(member + ' added as a site manager to ' + site_id)
    else:
        print(status_code)
        print('Unknown error occurred when creating membership')


def handle_site(site_id, user_list, group_list, folder_list):
    """Check if site exists, create it if it doesn't."""
    site_path = '/sites'
    get_url = hostname + content_services_path + site_path + '/' + site_id
    got_site = requests.get(url=get_url, headers=headers)
    status_code = got_site.status_code

    if status_code == 200:
        print('Site already exists, skipping creation of ' + site_id)
        site_json = got_site.json()
        entry = site_json["entry"]
        site_guid = entry["guid"]
    elif status_code == 404:
        print('Site doesn\'t exist, creating site with id ' + site_id)
        post_url = hostname + content_services_path + site_path
        site_payload = json.dumps({'title': site_id, 'visibility': 'PUBLIC'})
        create_site = requests.post(post_url, data=site_payload, headers=headers)
        print('Site created with below values')
        print(create_site.json())
        entry = create_site.json()["entry"]
        site_guid = entry["guid"]
        # Create json is not the same as 200 json
    else:
        print(status_code)
        print('Unknown error occurred when checking site.  Stopping subsequent activity.')
        return
    for user in user_list:
        handle_site_memberships(user, site_membership_role, site_path, site_id)
    for group in group_list:
        handle_site_memberships('GROUP_' + group, site_membership_role, site_path, site_id)
    for folder in folder_list:
        handle_folder(folder, site_id, site_guid)


def handle_root_category(root):
    root_payload = json.dumps({'name': root})
    root_post_url = hostname + ags_services_path + '/file-plans/' + '-filePlan-' + '/categories'
    post_root = requests.post(url=root_post_url, data=root_payload, headers=headers)
    if post_root.status_code == 409:
        root_get_url = hostname + ags_services_path + '/file-plans/' + '-filePlan-' + '/categories'
        get_root = requests.get(url=root_get_url, headers=headers)
        root_json = get_root.json()
        for root_entry in root_json['list']['entries']:
            print('Root category already exists: ' + root_entry['entry']['id'])
            return root_entry['entry']['id']
    elif post_root.status_code == 201:
        root_json = post_root.json()
        print('Created root category: ' + root + ' with id ' + root_json['entry']['id'])
        return root_json['entry']['id']
    else:
        print(status_code)
        print('Unknown error occurred when creating root category')


def handle_category(category_name, root_guid):
    category_payload = json.dumps({'name': category_name, 'nodeType': 'rma:recordCategory'})
    create_category_url = hostname + ags_services_path + '/record-categories/' + root_guid + '/children'
    create_category = requests.post(url=create_category_url, data=category_payload, headers=headers)
    status_code = create_category.status_code
    if status_code == 201:
        print('Category ' + category_name + ' created in ' + root_guid)
    elif status_code == 409:
        print('Category with name ' + category_name + ' already exists in ' + root_guid)
    else:
        print(status_code)
        print('Unknown error occurred when creating category')


def find_rm_role(rm_role):
    groups_get = hostname + content_services_path + '/groups'
    get_groups = requests.get(url=groups_get, headers=headers)
    json_resp = get_groups.json()
    for entry in json_resp['list']['entries']:
        group_id = str(entry['entry']['id'])
        display_name = str(entry['entry']['displayName'])
        if display_name == rm_role:
            print('RM Role Name: ' + display_name + ' RM Role ID: ' + group_id)
            return group_id


def add_user_as_rm_admin(admin_id, user_name):
    groups_post = hostname + content_services_path + '/groups/' + admin_id + '/members'
    groups_payload = json.dumps({'id': user_name, 'memberType': 'PERSON'})
    post_groups = requests.post(url=groups_post, data=groups_payload, headers=headers)
    status_code = post_groups.status_code
    if status_code == 201:
        print('Success adding ' + user_name + ' to role ' + admin_id)
    elif status_code == 409:
        print(user_name + ' is already a member of ' + admin_id)
    else:
        print('Error [' + str(status_code) + '] adding ' + user_name + ' to role ' + admin_id)


def add_group_as_rm_admin(admin_id, group_name):
    groups_post = hostname + content_services_path + '/groups/' + admin_id + '/members'
    groups_payload = json.dumps({'id': group_name, 'memberType': 'GROUP'})
    post_groups = requests.post(url=groups_post, data=groups_payload, headers=headers)
    status_code = post_groups.status_code
    if status_code == 201:
        print('Success adding ' + group_name + ' to role ' + admin_id)
    elif status_code == 409:
        print(group_name + ' is already a member of ' + admin_id)
    else:
        print('Error [' + str(status_code) + '] adding ' + group_name + ' to role ' + admin_id)


def handle_rm_site(rm_site_name, user_list, group_list, root_cat, category_list):
    site_id = rm_site_name
    site_path = '/sites'
    get_url = hostname + content_services_path + site_path + '/' + site_id
    got_site = requests.get(url=get_url, headers=headers)
    status_code = got_site.status_code
    if status_code == 200:
        print('Site already exists, skipping creation of ' + site_id)
        site_json = got_site.json()
        entry = site_json["entry"]
        site_guid = entry["guid"]
    else:
        print('RM site does not exist, creating RM site')
        rm_site_post_url = hostname + ags_services_path + '/gs-sites'
        rm_site_payload = json.dumps({'title': 'Records Management'})
        post_rm_site = requests.post(url=rm_site_post_url, data=rm_site_payload, headers=headers)
        print('Created RM site')
    for user in user_list:
        handle_site_memberships(user, site_membership_role, site_path, site_id)
    for group in group_list:
        handle_site_memberships('GROUP_' + group, site_membership_role, site_path, site_id)
    for root_c in root_cat:
        root_guid = handle_root_category(root_c)
        for category in category_list:
            handle_category(category, root_guid)

######################
# Start of main code
######################

line = environ.get('USERS', '')
connection_retries = int(environ.get('CONNECTION_RETRIES', 5))
connection_backoff_factor = int(environ.get('CONNECTION_BACKOFF_FACTOR', 10))
connection_failure = True
print ('retries: ' + str(connection_retries) + ' interval: ' + str(connection_backoff_factor))

alfresco_probe_url = hostname + content_services_path + "/probes/-live-"

retry_strategy = Retry(
    total=connection_retries,
    backoff_factor=connection_backoff_factor
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)
get_probe = http.get(url=alfresco_probe_url, headers=headers)

if get_probe.status_code == 200:
    print('Alfresco finished starting')

for user in users:
    handle_user(user)

for group in groups:
    handle_groups(group)

for site in sites:
    handle_site(site, users, groups, folders)

if create_rm_site:
    handle_rm_site('rm', users, groups, root_category, rm_categories)

    rm_admin_id = find_rm_role(rm_role)

    if rm_admin_id:
        for group in groups:
            add_group_as_rm_admin(rm_admin_id, 'GROUP_' + group)
