import os
import sys
import site
import django_env

if __name__ == '__main__':
    # Setup environ
    os.environ['DJANGO_SETTINGS_MODULE'] = "tardis.settings"
    site.addsitedir('/opt/mytardis/current/eggs')
    sys.path.append('/opt/mytardis/current')
        
import json
from django.contrib.auth.models import User
'''
Created on Oct 3, 2013

@author: sindhue
'''
def loadJsonFor(filename):
    try:
        jsonfile = open(filename, 'r')
    except IOError:
        print 'Error opening ', filename
        sys.exit()
    except:
        print 'Unexpected error while opening file, ', filename
        raise
    else:
        json_data = json.loads(jsonfile.read())  
        jsonfile.close()
        return json_data
    
def importUsers(filename, txt_file):
    ''' Import users from users.json '''
    users = loadJsonFor(filename)
    txt_file_sys1 = open(txt_file, 'w')
    
    for e in users:
        pk = e['pk']
        fields = e['fields']
        username = fields['username']
        txt_file_sys1.write('%d,%s\n' % (pk, username))
    txt_file_sys1.close() 

def importGroups(filename, txt_file):
    ''' Import groups from groups.json '''
    groups = loadJsonFor(filename)
    txt_file_sys1 = open(txt_file, 'w')
    
    for e in groups:
        pk = e['pk']
        fields = e['fields']
        name = fields['name']
        txt_file_sys1.write('%d,%s\n' % (pk, name))
    txt_file_sys1.close() 
    
def loadTextFileSys1(txt_file):
    ''' Returns a dictionary with userid and username '''
    d = {}
    with open(txt_file) as f:
        for line in f:
           (key, val) = line.split()
           d[int(key)] = val
        return d

def loadTextFileSys2(txt_file):
    ''' Returns a dictionary with userid and username '''
    d = {}
    with open(txt_file) as f:
        for line in f:
           (key, val) = line.split()
           d[val] = int(key)
        return d

def updateObjctACL(filename, user_dict_sys1, group_dict_sys1, user_dict_sys2, group_dict_sys2):
    ''' UPpdate the entityId field with the entity id in the current system for the username '''
    objectacl = loadJsonFor(filename)
    
    for oacl in objectacl:
        pk = oacl['pk']
        fields = oacl['fields']
        entityId = fields['entityId']
        pluginId = fields['pluginId']
        
        if pluginId == 'django_user':
            name = user_dict_sys1(entityId)
            entityId = user_dict_sys2(name)
        else:
            name = group_dict_sys1(entityId)
            entityId = group_dict_sys2(name)
        
        fields['entityId'] = entityId
    
    output_file = open('output_file.json', 'w')
    json.dump(objectacl, output_file, indent=4)

# Load System2 info into dictionary.
#bin/django dumpdata --indent=4 auth.User > users.json
#bin/django dumpdata --indent=4 auth.Group > groups.json
users_sys2 = 'users_sys2.txt'
groups_sys2 = 'groups_sys2.txt'
importUsers('users.json', users_sys2)
importGroups('groups.json', groups_sys2)
user_dict_sys2 = loadTextFileSys2(users_sys2)    # Load the dict with sys2 user info
group_dict_sys2 = loadTextFileSys2(groups_sys2)    # Load the dict with sys2 groupinfo

#NOTE: Make sure you have copied users_sys1.txt and groups_sys1.txt files from system1 into system2.
users_sys1 = 'users_sys1.txt'
groups_sys1 = 'groups_sys1.txt'
user_dict_sys1 = loadTextFileSys1(users_sys2)    # Load the dict with sys1 user info
group_dict_sys1 = loadTextFileSys1(groups_sys2)    # Load the dict with sys1 groupinfo

# Update ObjctACL with the entity_id of system2
updateObjctACL(filename, user_dict_sys1, group_dict_sys1, user_dict_sys2, group_dict_sys2)

#Load the above updated json file using loaddata.