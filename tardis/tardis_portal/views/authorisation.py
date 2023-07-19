# pylint: disable=http-response-with-json-dumps,http-response-with-content-type-json
"""
views that have to do with authorisations
"""

import json
import logging
from operator import itemgetter
from urllib.parse import parse_qs, urlencode, urlparse

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.core.exceptions import SuspiciousOperation
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.utils.html import escape
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from ..auth import decorators as authz
from ..models import (
    Experiment,
    ExperimentACL,
    GroupAdmin,
    Token,
    UserAuthentication,
    UserProfile,
)
from ..shortcuts import render_response_index

logger = logging.getLogger(__name__)


@never_cache
@login_required()
def retrieve_user_list(request):
    # TODO: Hook this up to authservice.searchUsers() to actually get
    # autocompletion data directly from auth backends.
    # The following local DB query would be moved to
    # auth.localdb_auth.SearchUsers.
    query = request.GET.get("q", "")
    limit = int(request.GET.get("limit", "10"))

    # Search all user fields and also the UserAuthentication username.
    q = (
        Q(username__icontains=query)
        | Q(email__icontains=query)
        | Q(userprofile__userauthentication__username__icontains=query)
    )

    # Tokenize query string so "Bob Sm" matches (first_name~=Bob &
    # last_name~=Smith).
    tokens = query.split()
    if len(tokens) < 2:
        q |= Q(first_name__icontains=query.strip())
        q |= Q(last_name__icontains=query.strip())
    else:
        q |= Q(first_name__icontains=" ".join(tokens[:-1])) & Q(
            last_name__icontains=tokens[-1]
        )

    users_query = (
        User.objects.filter(is_active=True)
        .exclude(pk=settings.PUBLIC_USER_ID)
        .filter(q)
        .distinct()
        .select_related("userprofile")
    )

    # HACK FOR ORACLE - QUERY GENERATED DOES NOT WORK WITH LIMIT SO USING
    # ITERATOR INSTEAD
    from itertools import islice

    first_n_users = list(islice(users_query, limit))

    user_auths = list(
        UserAuthentication.objects.filter(userProfile__user__in=first_n_users)
    )
    auth_methods = {ap[0]: ap[1] for ap in settings.AUTH_PROVIDERS}
    users = []
    for u in users_query:
        fields = ("first_name", "last_name", "username", "email")
        # Convert attributes to dictionary keys and make sure all values
        # are strings.
        user = {k: str(getattr(u, k)) for k in fields}
        try:
            user["auth_methods"] = [
                "%s:%s:%s"
                % (
                    ua.username,
                    ua.authenticationMethod,
                    auth_methods[ua.authenticationMethod],
                )
                for ua in user_auths
                if ua.userProfile == u.userprofile
            ]
        except UserProfile.DoesNotExist:
            user["auth_methods"] = []

        if not user["auth_methods"]:
            user["auth_methods"] = [
                "%s:localdb:%s" % (u.username, auth_methods["localdb"])
            ]
        users.append(user)

    users.sort(key=itemgetter("first_name"))
    return HttpResponse(json.dumps(users))


@never_cache
@login_required()
def retrieve_group_list(request):
    grouplist = " ~ ".join(map(str, Group.objects.all().order_by("name")))
    return HttpResponse(grouplist)


@never_cache
@authz.experiment_ownership_required
def retrieve_access_list_user(request, experiment_id):
    from ..forms import AddUserPermissionsForm

    user_acls = Experiment.safe.user_acls(experiment_id)

    c = {
        "user_acls": user_acls,
        "experiment_id": experiment_id,
        "addUserPermissionsForm": AddUserPermissionsForm(),
    }
    return render_response_index(request, "tardis_portal/ajax/access_list_user.html", c)


@never_cache
def retrieve_access_list_user_readonly(request, experiment_id):
    user_acls = Experiment.safe.user_acls(experiment_id)

    c = {"user_acls": user_acls, "experiment_id": experiment_id}
    return render_response_index(
        request, "tardis_portal/ajax/access_list_user_readonly.html", c
    )


@never_cache
@authz.experiment_ownership_required
def retrieve_access_list_group(request, experiment_id):
    group_acls_system_owned = Experiment.safe.group_acls_system_owned(experiment_id)

    group_acls_user_owned = Experiment.safe.group_acls_user_owned(experiment_id)

    c = {
        "group_acls_user_owned": group_acls_user_owned,
        "group_acls_system_owned": group_acls_system_owned,
        "experiment_id": experiment_id,
    }
    return render_response_index(
        request, "tardis_portal/ajax/access_list_group.html", c
    )


@never_cache
def retrieve_access_list_group_readonly(request, experiment_id):
    group_acls_system_owned = Experiment.safe.group_acls_system_owned(experiment_id)

    group_acls_user_owned = Experiment.safe.group_acls_user_owned(experiment_id)

    group_acls = group_acls_system_owned | group_acls_user_owned

    c = {"experiment_id": experiment_id, "group_acls": group_acls}
    return render_response_index(
        request, "tardis_portal/ajax/access_list_group_readonly.html", c
    )


@never_cache
@authz.experiment_ownership_required
def retrieve_access_list_external(request, experiment_id):
    groups = Experiment.safe.external_users(experiment_id)
    c = {"groups": groups, "experiment_id": experiment_id}
    return render_response_index(
        request, "tardis_portal/ajax/access_list_external.html", c
    )


@never_cache
@authz.experiment_download_required
def retrieve_access_list_tokens(request, experiment_id):
    tokens = Token.objects.prefetch_related(
        Prefetch("experimentacls", ExperimentACL.objects.select_related("experiment"))
    ).filter(experimentacls__experiment__id=experiment_id)

    def token_url(url, token):
        if not url:
            return ""
        u = urlparse(url)
        query = parse_qs(u.query)
        query.pop("token", None)
        query["token"] = token.token
        u = u._replace(query=urlencode(query, True))
        return u.geturl()
        # return '%s?token=%s' % (request.META['HTTP_REFERER'], token.token)

    page_url = request.META.get("HTTP_REFERER")
    download_urls = Experiment.objects.get(id=experiment_id).get_download_urls()

    tokens = [
        {
            "expiry_date": token.expiry_date,
            "user": token.user,
            "url": request.build_absolute_uri(token_url(page_url, token)),
            "download_url": request.build_absolute_uri(
                token_url(download_urls.get("tar", None), token)
            ),
            "id": token.id,
            "experiment_id": experiment_id,
            "is_owner": request.user.has_perm(
                "tardis_acls.owns_experiment", Experiment.objects.get(pk=experiment_id)
            ),
        }
        for token in tokens
    ]

    has_archive_download_url = False
    for t in tokens:
        if t.get("download_url", False):
            has_archive_download_url = True

    c = {"tokens": tokens, "has_archive_download_url": has_archive_download_url}

    return render_response_index(
        request, "tardis_portal/ajax/access_list_tokens.html", c
    )


@never_cache
@authz.group_ownership_required
def retrieve_group_userlist(request, group_id):
    # TODO: Probably a smarter way to retrieve Users and admin status rather than
    # iterating over each user and checking, as below
    from ..forms import ManageGroupPermissionsForm

    users = User.objects.filter(groups__id=group_id).exclude(pk=settings.PUBLIC_USER_ID)
    group_admins = []
    for user in users:
        query = GroupAdmin.objects.filter(admin_user=user, group__id=group_id)
        admin_groups = Group.objects.filter(user=user)
        for admin_group in admin_groups:
            query |= GroupAdmin.objects.filter(
                admin_group=admin_group, group__id=group_id
            )
        if query.exists():
            group_admins.append(user)
    c = {
        "users": users,
        "group_id": group_id,
        "group_admins": group_admins,
        "manageGroupPermissionsForm": ManageGroupPermissionsForm(),
    }
    return render_response_index(request, "tardis_portal/ajax/group_user_list.html", c)


@never_cache
def retrieve_group_userlist_readonly(request, group_id):
    # TODO: Probably a smarter way to retrieve Users and admin status rather than
    # iterating over each user and checking, as below
    from ..forms import ManageGroupPermissionsForm

    users = User.objects.filter(groups__id=group_id).exclude(pk=settings.PUBLIC_USER_ID)
    group_admins = []
    for user in users:
        query = GroupAdmin.objects.filter(admin_user=user, group__id=group_id)
        admin_groups = Group.objects.filter(user=user)
        for admin_group in admin_groups:
            query |= GroupAdmin.objects.filter(
                admin_group=admin_group, group__id=group_id
            )
        if query.exists():
            group_admins.append(user)
    c = {
        "users": users,
        "group_id": group_id,
        "group_admins": group_admins,
        "manageGroupPermissionsForm": ManageGroupPermissionsForm(),
    }
    return render_response_index(
        request, "tardis_portal/ajax/group_user_list_readonly.html", c
    )


@never_cache
def retrieve_group_list_by_user(request):
    # TODO: Probably a smarter way to retrieve Users and admin status rather than
    # iterating over each user and checking, as below
    groups = Group.objects.filter(groupadmin__admin_user=request.user)
    admin_groups = Group.objects.filter(user=request.user)
    for admin_group in admin_groups:
        groups |= Group.objects.filter(groupadmin__admin_group=admin_group)
    c = {"groups": groups.order_by("name")}
    return render_response_index(request, "tardis_portal/ajax/group_list.html", c)


@never_cache
@permission_required("auth.change_group")
@login_required()
def manage_groups(request):
    c = {}
    return render_response_index(request, "tardis_portal/manage_group_members.html", c)


@never_cache  # too complex # noqa
@authz.group_ownership_required
def add_user_to_group(request, group_id, username):
    isAdmin = False
    logger.info("isAdmin: %s", str(isAdmin))

    if "isAdmin" in request.GET:
        if request.GET["isAdmin"] == "true":
            isAdmin = True
    logger.info("isAdmin: %s", str(isAdmin))

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse(
            {
                "message": "User %s does not exist." % username,
                "field": "id_adduser-%s" % group_id,
            },
            status=400,
        )

    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        return JsonResponse(
            {
                "message": "Group does not exist",
            },
            status=400,
        )

    if user.groups.filter(name=group.name).count() > 0:
        return JsonResponse(
            {
                "message": "User %s is already a member of this group." % username,
                "field": "id_adduser-%s" % group_id,
            },
            status=400,
        )

    user.groups.add(group)
    user.save()

    logger.info("isAdmin: %s", str(isAdmin))
    if isAdmin:
        groupadmin = GroupAdmin(admin_user=user, group=group)
        groupadmin.save()
    users = User.objects.filter(groups__id=group_id).exclude(pk=settings.PUBLIC_USER_ID)
    group_admins = []
    for user in users:
        if GroupAdmin.objects.filter(admin_user=user, group__id=group_id).exists():
            group_admins.append(user)
    c = {"user": user, "group_id": group_id, "group_admins": group_admins}
    return render_response_index(
        request, "tardis_portal/ajax/add_user_to_group_result.html", c
    )


@never_cache
@authz.group_ownership_required
def remove_user_from_group(request, group_id, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse("User %s does not exist." % escape(username), status=400)
    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        return HttpResponse("Group does not exist.", status=400)

    if user.groups.filter(name=group.name).count() == 0:
        return HttpResponse(
            "User %s is not member of that group." % escape(username), status=400
        )

    if request.user == user:
        return HttpResponse("You cannot remove yourself from that group.", status=400)

    user.groups.remove(group)
    user.save()

    try:
        groupadmin = GroupAdmin.objects.filter(admin_user=user, group=group)
        groupadmin.delete()
    except GroupAdmin.DoesNotExist:
        pass

    return HttpResponse("OK")


@never_cache  # too complex # noqa
@transaction.atomic
@authz.experiment_ownership_required
def add_experiment_access_user(request, experiment_id, username):
    try:
        # cast experiment_id into it's expected integer type
        experiment_id = int(experiment_id)
    except ValueError:
        # Raises badrequest(400) error - if experiment_id isn't castable to int
        # then either the codebase is wrong, or someone's sending dodgy requests.
        return SuspiciousOperation("Bad URL: Expected an integer Experiment ID")

    canRead = False
    canDownload = False
    canWrite = False
    canDelete = False
    canSensitive = False
    isOwner = False

    if "canRead" in request.GET:
        if request.GET["canRead"] == "true":
            canRead = True

    if "canDownload" in request.GET:
        if request.GET["canDownload"] == "true":
            canDownload = True

    if "canWrite" in request.GET:
        if request.GET["canWrite"] == "true":
            canWrite = True

    if "canDelete" in request.GET:
        if request.GET["canDelete"] == "true":
            canDelete = True

    if "canSensitive" in request.GET:
        if request.GET["canSensitive"] == "true":
            canSensitive = True

    if "isOwner" in request.GET:
        if request.GET["isOwner"] == "true":
            isOwner = True

    authMethod = request.GET["authMethod"]
    try:
        user = User.objects.get(username=username)
        if not user.is_active:
            return HttpResponse("User %s is inactive." % escape(username), status=400)
    except User.DoesNotExist:
        return HttpResponse("User %s does not exist." % escape(username), status=400)

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        return HttpResponse(
            "Experiment (id=%d) does not exist." % (experiment_id), status=400
        )

    acl = ExperimentACL.objects.filter(
        experiment=experiment, user=user, aclOwnershipType=ExperimentACL.OWNER_OWNED
    )

    if acl.count() == 0:
        acl = ExperimentACL(
            experiment=experiment,
            user=user,
            canRead=canRead,
            canDownload=canDownload,
            canWrite=canWrite,
            canDelete=canDelete,
            canSensitive=canSensitive,
            isOwner=isOwner,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )

        acl.save()
        c = {
            "authMethod": authMethod,
            "user": user,
            "user_acl": acl,
            "username": username,
            "experiment_id": experiment_id,
        }

        return render_response_index(
            request, "tardis_portal/ajax/add_user_result.html", c
        )

    return HttpResponse("User already has experiment access.", status=400)


@never_cache
@authz.experiment_ownership_required
def remove_experiment_access_user(request, experiment_id, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse("User %s does not exist" % escape(username), status=400)

    try:
        Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        return HttpResponse("Experiment does not exist", status=400)

    expt_acls = Experiment.safe.user_acls(experiment_id)

    target_acl = expt_acls.filter(user=user)
    owner_acls = [acl for acl in expt_acls if acl.isOwner]

    if target_acl.count() == 0:
        return HttpResponse(
            "The user %s does not have access to this "
            "experiment." % escape(username),
            status=400,
        )

    if expt_acls.count() >= 1:
        if len(owner_acls) > 1 or (len(owner_acls) == 1 and not target_acl[0].isOwner):
            target_acl[0].delete()
            return HttpResponse("OK")
        return HttpResponse(
            "All experiments must have at least one user as "
            "owner. Add an additional owner first before "
            "removing this one.",
            status=400,
        )

    # the user shouldn't really ever see this in normal operation
    return HttpResponse(
        "Experiment has no permissions (of type OWNER_OWNED) !", status=400
    )


@transaction.atomic  # too complex # noqa
@never_cache
def create_group(request):
    if "group" not in request.GET:
        response = render_response_index(
            request, "tardis_portal/ajax/create_group.html", {}
        )
        return response

    admin = None
    groupname = None

    if "group" in request.GET:
        groupname = request.GET["group"]

    if not groupname:
        return JsonResponse(
            {"message": "Group name cannot be blank", "field": "id_addgroup"},
            status=400,
        )

    if "admin" in request.GET:
        admin = request.GET["admin"]

    try:
        with transaction.atomic():
            group = Group(name=groupname)
            group.save()
    except IntegrityError:
        return JsonResponse(
            {
                "message": (
                    "Could not create group %s "
                    "(It is likely that it already exists)" % escape(groupname)
                ),
                "field": "id_addgroup",
            },
            status=409,
        )

    adminuser = None
    if admin:
        try:
            adminuser = User.objects.get(username=admin)
        except User.DoesNotExist:
            return JsonResponse(
                {"message": "User %s does not exist" % admin, "field": "id_groupadmin"},
                status=400,
            )

        # create admin for this group and add it to the group
        groupadmin = GroupAdmin(admin_user=adminuser, group=group)
        groupadmin.save()

        adminuser.groups.add(group)
        adminuser.save()

    # add the current user as admin as well for newly created groups
    if request.user != adminuser:
        user = request.user

        groupadmin = GroupAdmin(admin_user=user, group=group)
        groupadmin.save()

        user.groups.add(group)
        user.save()

    c = {"group": group}

    response = render_response_index(request, "tardis_portal/ajax/create_group.html", c)
    return response


@never_cache  # too complex # noqa
@transaction.atomic
@authz.experiment_ownership_required
def add_experiment_access_group(request, experiment_id, groupname):
    canRead = request.GET.get("canRead") == "true"
    canDownload = request.GET.get("canDownload") == "true"
    canWrite = request.GET.get("canWrite") == "true"
    canDelete = request.GET.get("canDelete") == "true"
    canSensitive = request.GET.get("canSensitive") == "true"
    isOwner = request.GET.get("isOwner") == "true"

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        return HttpResponse(
            "Experiment (id=%d) does not exist" % escape(experiment_id), status=400
        )

    try:
        group = Group.objects.get(name=groupname)
    except Group.DoesNotExist:
        return HttpResponse("Group %s does not exist" % escape(groupname), status=400)

    acl = ExperimentACL.objects.filter(
        experiment=experiment, group=group, aclOwnershipType=ExperimentACL.OWNER_OWNED
    )

    if acl.count() > 0:
        # An ACL already exists for this experiment/group.
        return HttpResponse(
            "Could not add group %s " "(It has already been added)" % escape(groupname),
            status=400,
        )

    acl = ExperimentACL(
        experiment=experiment,
        group=group,
        canRead=canRead,
        canDownload=canDownload,
        canWrite=canWrite,
        canDelete=canDelete,
        canSensitive=canSensitive,
        isOwner=isOwner,
        aclOwnershipType=ExperimentACL.OWNER_OWNED,
    )
    acl.save()

    c = {"group": group, "group_acl": acl, "experiment_id": experiment_id}
    return render_response_index(request, "tardis_portal/ajax/add_group_result.html", c)


@never_cache
@authz.experiment_ownership_required
def remove_experiment_access_group(request, experiment_id, group_id):
    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        return HttpResponse("Group does not exist")

    try:
        experiment = Experiment.objects.get(pk=experiment_id)
    except Experiment.DoesNotExist:
        # This will never be reached because the
        # @authz.experiment_ownership_required has already
        # checked this.
        return HttpResponse("Experiment does not exist")

    acl = ExperimentACL.objects.filter(
        experiment=experiment, group=group, aclOwnershipType=ExperimentACL.OWNER_OWNED
    )

    if acl.count() == 1:
        acl[0].delete()
        return HttpResponse("OK")
    if acl.count() == 0:
        return HttpResponse(
            "No ACL available."
            "It is likely the group doesnt have access to"
            "this experiment."
        )
    return HttpResponse("Multiple ACLs found")


@require_POST
@authz.experiment_ownership_required
def create_token(request, experiment_id):
    experiment = Experiment.objects.get(id=experiment_id)
    token = Token(user=request.user)
    token.save()
    # For now, tokens are Read only
    acl = ExperimentACL(
        token=token,
        experiment=experiment,
        canRead=True,
        aclOwnershipType=ExperimentACL.OWNER_OWNED,
    )
    acl.save()
    token.save_with_random_token()
    logger.info("created token: %s" % token)
    return HttpResponse('{"success": true}', content_type="application/json")


@require_POST
def token_delete(request, token_id):
    token = Token.objects.get(id=token_id)
    # To refactor once token more generic than just an experiment
    experiment_ids = token.experimentacls.select_related("experiment").values_list(
        "experiment__id", flat=True
    )
    is_owner_of_any = []
    for exp_id in experiment_ids:
        is_owner_of_any.append(authz.has_ownership(request, exp_id, "experiment"))
    if any(is_owner_of_any):
        token.delete()
        return HttpResponse('{"success": true}', content_type="application/json")
    return HttpResponse('{"success": false}', content_type="application/json")


def share(request, experiment_id):
    """
    Choose access rights and licence.
    """
    experiment = Experiment.objects.get(id=experiment_id)
    user = request.user

    c = {}

    c["has_write_permissions"] = authz.has_write(request, experiment_id, "experiment")
    c["has_download_permissions"] = authz.has_download_access(
        request, experiment_id, "experiment"
    )
    if user.is_authenticated:
        c["is_owner"] = authz.has_ownership(request, experiment_id, "experiment")
        c["is_superuser"] = user.is_superuser

    domain = Site.objects.get_current().domain
    public_link = experiment.public_access >= Experiment.PUBLIC_ACCESS_METADATA

    c["experiment"] = experiment
    c["public_link"] = public_link
    c["domain"] = domain

    return render_response_index(request, "tardis_portal/ajax/share.html", c)
