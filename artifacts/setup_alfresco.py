import base64
import requests
import json

# Template CSV file looks like
# line 1: Base URL, username, password
# line 2: user1, user2, ...
# line 3: group1, group2, ...
# line 4: public site1, public site2, ...
# line 5: rm site
# line 6: folder1, folder2
# line 7: rm root category
# line 8: rm category1, rm category2

# For example:
# http://localhost:8080,admin,admin
# yasser
# ARKCASE_ENTITY_ADMINISTRATOR,ARKCASE_CONSUMER,ARKCASE_SUPERVISOR,ARKCASE_ADMINISTRATOR,ARKCASE_EXTERNAL,ARKCASE_CONTRIBUTOR
# acm
# rm
# Case Files,Complaints,Document Repositories,Expenses,People,Recycle Bin,Tasks,Timesheets,User Profile,Business Processes,Consultations,SAR,Requests
# ACM
# Case Files,Complaints,Document Repositories,Requests,Tasks,Consultations,SAR

content_services_path = '/alfresco/api/-default-/public/alfresco/versions/1'
ags_services_path = '/alfresco/api/-default-/public/gs/versions/1'
filename = './alfresco_setup.properties'


def remove_eol(string: str):
    """When loading a line from a file, it has a \n on it.  This removes it."""
    if string.find('\n') != -1:
        return string[0:string.__len__() - 1]
    else:
        return string


properties = open(filename)

line = remove_eol(properties.readline())
env_vars = line.split(',')

hostname = env_vars[0]
username = env_vars[1]
password = env_vars[2]

base64string = base64.b64encode(bytes('%s:%s' % (username, password), 'ascii'))
headers = {"Authorization": "Basic %s" % base64string.decode('utf-8'), 'Content\u002DType': "application/json",
           "Accept": "application/json"}

line = remove_eol(properties.readline())
users = line.split(',')

line = remove_eol(properties.readline())
groups = line.split(',')

line = remove_eol(properties.readline())
sites = line.split(',')

line = remove_eol(properties.readline())
rm_sites = line.split(',')

line = remove_eol(properties.readline())
folders = line.split(',')

line = remove_eol(properties.readline())
root_category = line.split(',')

line = remove_eol(properties.readline())
rm_categories = line.split(',')

print(users)
print(groups)
print(sites)
print(rm_sites)
print(folders)
print(root_category)
print(rm_categories)


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


def handle_site_manager(user, site_path, site_id):
    user_role_payload = json.dumps({'role': 'SiteManager', 'id': user})
    assign_role_url = hostname + content_services_path + site_path + '/' + site_id + '/members'
    assign_role = requests.post(assign_role_url, data=user_role_payload, headers=headers)
    status_code = assign_role.status_code
    if status_code == 409:
        print(user + ' is already a member of ' + site_id)
    else:
        print(user + ' added as a site manager to ' + site_id)


def handle_site(site_id, user_list, folder_list):
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
        entry = create_site["entry"]
        site_guid = entry["guid"]
        # Create json is not the same as 200 json
    else:
        print(status_code)
        print('Unknown error occurred when checking site.  Stopping subsequent activity.')
        return
    for user in user_list:
        handle_site_manager(user, site_path, site_id)
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
            print('Got root ' + root_entry['entry']['id'])
            return root_entry['entry']['id']
    else: 
       root_json = post_root.json()
       print('Created root ' + root)
       return root_json['entry']['id']


def handle_category(category_name, root_guid):
    category_payload = json.dumps({'name': category_name, 'nodeType': 'rma:recordCategory'})
    category_post = hostname + ags_services_path + '/record-categories/' + root_guid + '/children'
    post_category = requests.post(url=category_post, data=category_payload, headers=headers)
    print(post_category)


def find_rm_role():
    groups_get = hostname + content_services_path + '/groups'
    get_groups = requests.get(url=groups_get, headers=headers)
    json_resp = get_groups.json()
    for entry in json_resp['list']['entries']:
        print(entry)
        group_id = str(entry['entry']['id'])
        display_name = str(entry['entry']['displayName'])
        if display_name == 'rm.role.administrator':
            return group_id


#def add_user_as_rm_admin(admin_id, user_name):
#    groups_post = hostname + content_services_path + '/groups/' + admin_id + '/members'
#    groups_payload = json.dumps({'id': user_name, 'memberType': 'PERSON'})
#    post_groups = requests.post(url=groups_post, data=groups_payload, headers=headers)
#    print(post_groups)


def add_group_as_rm_admin(admin_id, group_name):
    print ('admin_id: ' + admin_id + ' group_name: ' + group_name)
    groups_post = hostname + content_services_path + '/groups/' + admin_id + '/members'
    print ('groups_post URL: ' + groups_post)
    groups_payload = json.dumps({'id': group_name, 'memberType': 'GROUP'})
    post_groups = requests.post(url=groups_post, data=groups_payload, headers=headers)
    print(post_groups)


def handle_rm_site(rm_site_name, user_list, root_cat, category_list):
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
    for user in user_list:
        handle_site_manager(user, site_path, site_id)
    for root_c in root_cat:
        root_guid = handle_root_category(root_c)
        for category in category_list:
            handle_category(category, root_guid)

for user in users:
    handle_user(user)

for group in groups:
    handle_groups(group)

for site in sites:
    handle_site(site, users, folders)

for rm_site in rm_sites:
    handle_rm_site(rm_site, users, root_category, rm_categories)


rm_admin_id = find_rm_role()

for group in groups:
    print ('group: ' + group)
    add_group_as_rm_admin(rm_admin_id, group)
