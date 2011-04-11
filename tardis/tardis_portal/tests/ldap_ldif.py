# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# Copyright (c) 2010 VPAC
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


from django.conf import settings


test_ldif = [
    "dn: " + settings.LDAP_GROUP_BASE,
    "objectClass: organizationalUnit",
    "ou: Group",
    "",
    "dn: " + settings.LDAP_USER_BASE,
    "objectClass: organizationalUnit",
    "ou: People",
    "",
    'dn: uid=testuser1, ' + settings.LDAP_USER_BASE,
    'cn: Test User',
    'objectClass: inetOrgPerson',
    'objectClass: top',
    'userPassword:: kklk',
    'o: Example Org',
    'sn: User',
    'mail: t.user@example.com',
    'givenName: Test',
    'uid: testuser1',
    '',
    'dn: uid=testuser2, ' + settings.LDAP_USER_BASE,
    'cn: Test User2',
    'objectClass: inetOrgPerson',
    'objectClass: top',
    'userPassword:: gfgf',
    'o: Example Org2',
    'sn: User2',
    'mail: t.user2@example.com',
    'givenName: Test',
    'uid: testuser2',
    '',
    'dn: uid=testuser3, ' + settings.LDAP_USER_BASE,
    'cn: Test User3',
    'objectClass: inetOrgPerson',
    'objectClass: top',
    'userPassword:: asdf',
    'o: Example Org3',
    'sn: User3',
    'mail: t.user3@example.com',
    'givenName: Test',
    'uid: testuser3',
    '',
    'dn: cn=systems, ' + settings.LDAP_GROUP_BASE,
    'objectClass: posixGroup',
    'gidNumber: 10001',
    'cn: systems',
    'description: Systems Services',
    'memberUid: testuser1',
    '',
    'dn: cn=empty, ' + settings.LDAP_GROUP_BASE,
    'objectClass: posixGroup',
    'gidNumber: 10002',
    'cn: empty',
    'description: Empty Group',
    '',
    'dn: cn=full,' + settings.LDAP_GROUP_BASE,
    'objectClass: posixGroup',
    'gidNumber: 10003',
    'cn: full',
    'description: Full Group',
    'memberUid: testuser1',
    'memberUid: testuser2',
    'memberUid: testuser3',
    '',
    ]
