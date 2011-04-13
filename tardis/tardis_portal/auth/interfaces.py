# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""

.. moduleauthor:: Russell Sim <russell.sim@gmail.com>
"""


class AuthProvider:

    def authenticate(self, request):
        """
        from a request authenticate try to authenticate the user.
        return a user dict if successful.
        """
        raise NotImplemented()

    def get_user(self, user_id):
        raise NotImplemented()


class UserProvider:

    def getUserById(self, id):
        """
        return the user dictionary in the format of::

            {"id": 123,
            "display": "John Smith",
            "email": "john@example.com"}

        """
        raise NotImplemented()

    def searchUsers(self, request):
        """
        return a list of user descriptions from the auth domain.

        each user is in the format of::

            {"id": 123,
            "display": "John Smith",
            "email": "john@example.com"}

        """
        raise NotImplemented()


class GroupProvider:

    def getGroups(self, request):
        """
        return an iteration of the available groups.
        """
        raise NotImplemented()

    def getGroupById(self, id):
        """
        return the group associated with the id
        """
        raise NotImplemented()

    def searchGroups(self, **filter):
        """
        return a list of groups that match the filter
        """
        raise NotImplemented()

    def getGroupsForEntity(self, id):
        """
        return a list of groups associated with a particular entity id
        """
        raise NotImplemented()
