returnString = ""
from django.conf import settings

import os
def traverse(path):
    # print ' ' * traverse.level + data['text']
    global returnString
    dir_list = os.listdir(path)
    for f in dir_list:
        if not (f.startswith('.')):
            if os.path.isdir(f):
                #print '---' * traverse.level + '/' + f
                os.chdir(f)

                returnString = returnString + "<li id=\"" + os.path.abspath(f)[len(settings.STAGING_PATH)+1:] + "\"><a>" + f + "</a><ul>"
                returnString = traverse(".")
                returnString = returnString + "</ul></li>"

                os.chdir("..")
            else:
                returnString = returnString + "<li id=\"" + os.path.abspath(f)[len(settings.STAGING_PATH)+1:] + "\"><a>" + f + "</a></li>"
                #print '---' * traverse.level + f
    return returnString