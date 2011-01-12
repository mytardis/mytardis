'''
Created on 06/01/2011

@author: Ulrich Felzmann
'''

from tardis.tardis_portal.auth.interfaces import GroupProvider


class IPGroupProvider(GroupProvider):
    name = u'ip_address'

    def getGroups(self, request):
        """
        return an iteration of the available groups.
        """

        addr = request.META['REMOTE_ADDR']
        groups = [addr]

        ip4 = addr.split('.')
        for i in range(4):
            ip4[3 - i] = '0'
            subnet = '%s.%s.%s.%s' % (ip4[0], ip4[1], ip4[2], ip4[3])
            groups += [subnet]

        return groups

    def getGroupById(self, id):
        """
        return the group associated with the id::

            {"id": 123,
            "display": "Group Name",}

         """
        raise NotImplemented()

    def searchGroups(self, **filter):
        return []
