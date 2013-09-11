from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

import re
import os

'''
Created on Sep 11, 2013

@author: Sindhu Emilda

 Command for replacing all pk field with null in all the json files in the folder
 mentioned in the argument.
 This can be used before loading the dumped data.
'''
class Command(BaseCommand):
    args = 'directory_name'
    help = 'Help text goes here'

    def handle(self, *args, **options):
        if len(args) == 1:
            folder = args[0]
            for jfile in os.listdir(folder):
                if jfile.endswith(".json"):
                    fname = folder + '/' + jfile
                    print 'Reading file: ', fname
                    json_file = open(fname, 'r')
                    data = json_file.read()
                    # Replace id values with null - adjust the regex to your needs
                    data = re.sub('"pk": [0-9]{1,5}', '"pk": null', data)
                    json_file.close()
                    json_file = open(fname, 'w')
                    json_file.write(data)
                    json_file.close()
        else:
            self.stdout.write('Usage: nullpks dir_name\n')
        
             
