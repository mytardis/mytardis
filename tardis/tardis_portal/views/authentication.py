"""
views that have to do with authentication
"""
import logging

from urllib.parse import urlparse

import jwt

from django.conf import settings
from django.contrib import auth as djauth
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.html import escape
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters

from ..auth import auth_service
from ..auth.localdb_auth import auth_key as localdb_auth_key
from ..forms import ManageAccountForm, CreateUserPermissionsForm
from ..models import JTI, UserProfile, UserAuthentication
from ..shortcuts import render_response_index
from ..views.utils import _redirect_303

logger = logging.getLogger(__name__)


@csrf_exempt
def rcauth(request):
    # Only POST is supported on this URL.
    if request.method != "POST":
        raise PermissionDenied

    # Rapid Connect authorization is disabled, so don't
    # process anything.
    if not settings.RAPID_CONNECT_ENABLED:
        raise PermissionDenied

    try:
        # Verifies signature and expiry time
        verified_jwt = jwt.decode(
            request.POST["assertion"],
            settings.RAPID_CONNECT_CONFIG["secret"],
            audience=settings.RAPID_CONNECT_CONFIG["aud"],
        )

        # Check for a replay attack using the jti value.
        jti = verified_jwt["jti"]
        if JTI.objects.filter(jti=jti).exists():
            logger.debug("Replay attack? " + str(jti))
            request.session.pop("attributes", None)
            request.session.pop("jwt", None)
            request.session.pop("jws", None)
            django_logout(request)
            return redirect("/")
        JTI(jti=jti).save()

        if (
            verified_jwt["aud"] == settings.RAPID_CONNECT_CONFIG["aud"]
            and verified_jwt["iss"] == settings.RAPID_CONNECT_CONFIG["iss"]
        ):
            request.session["attributes"] = verified_jwt[
                "https://aaf.edu.au/attributes"
            ]
            request.session["jwt"] = verified_jwt
            request.session["jws"] = request.POST["assertion"]

            institution_email = request.session["attributes"]["mail"]

            logger.debug(
                "Successfully authenticated %s via Rapid Connect." % institution_email
            )

            # Create a user account and profile automatically. In future,
            # support blacklists and whitelists.
            first_name = request.session["attributes"]["givenname"]
            c_name = request.session["attributes"].get("cn", "").split(" ")
            if not first_name and len(c_name) > 1:
                first_name = c_name[0]
            user_args = {
                "id": institution_email.lower(),
                "email": institution_email.lower(),
                "first_name": first_name,
                "last_name": request.session["attributes"]["surname"],
            }

            # Check for an email collision.
            edupersontargetedid = request.session["attributes"]["edupersontargetedid"]
            for matching_user in UserProfile.objects.filter(
                user__email__iexact=user_args["email"]
            ):
                if (
                    matching_user.rapidConnectEduPersonTargetedID is not None
                    and matching_user.rapidConnectEduPersonTargetedID
                    != edupersontargetedid
                ):
                    del request.session["attributes"]
                    del request.session["jwt"]
                    del request.session["jws"]
                    django_logout(request)
                    raise PermissionDenied

            user = auth_service.get_or_create_user(user_args)
            if user is not None:
                user.backend = "django.contrib.auth.backends.ModelBackend"
                djauth.login(request, user)
                return redirect("/")
        else:
            del request.session["attributes"]
            del request.session["jwt"]
            del request.session["jws"]
            django_logout(request)
            raise PermissionDenied  # Error: Not for this audience
    except jwt.ExpiredSignature:
        del request.session["attributes"]
        del request.session["jwt"]
        del request.session["jws"]
        django_logout(request)
        raise PermissionDenied  # Error: Security cookie has expired

    raise PermissionDenied


@login_required
def manage_user_account(request):
    user = request.user

    # Process form or prepopulate it
    if request.method == "POST":
        form = ManageAccountForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            user.save()
            return _redirect_303("tardis.tardis_portal.views.index")
    else:
        form = ManageAccountForm(instance=user)

    c = {"form": form}
    return render_response_index(request, "tardis_portal/manage_user_account.html", c)


def logout(request):
    if "datafileResults" in request.session:
        del request.session["datafileResults"]

    # Remove AAF attributes.
    del request.session["attributes"]
    del request.session["jwt"]
    del request.session["jws"]

    return redirect("tardis.tardis_portal.views.index")


@never_cache
def create_user(request):
    if "user" not in request.POST:
        c = {"createUserPermissionsForm": CreateUserPermissionsForm()}

        response = render_response_index(
            request, "tardis_portal/ajax/create_user.html", c
        )
        return response

    authMethod = localdb_auth_key

    if "user" in request.POST:
        username = request.POST["user"]

    if "authMethod" in request.POST:
        authMethod = request.POST["authMethod"]

    if "email" in request.POST:
        email = request.POST["email"]

    if "password" in request.POST:
        password = request.POST["password"]

    try:
        with transaction.atomic():
            validate_email(email)
            user = User.objects.create_user(username, email, password)

            authentication = UserAuthentication(
                userProfile=user.userprofile,
                username=username,
                authenticationMethod=authMethod,
            )
            authentication.save()

    except ValidationError:
        return HttpResponse(
            "Could not create user %s "
            "(Email address is invalid: %s)" % (escape(username), escape(email)),
            status=403,
        )
    except:  # FIXME
        return HttpResponse(
            "Could not create user %s "
            "(It is likely that this username already exists)" % escape(username),
            status=403,
        )

    c = {"user_created": username}
    transaction.commit()

    response = render_response_index(request, "tardis_portal/ajax/create_user.html", c)
    return response


@sensitive_post_parameters("password")
def login(request):
    """
    handler for login page
    """
    from ..auth import auth_service

    if request.user.is_authenticated:
        # redirect the user to the home page if he is trying to go to the
        # login page
        return HttpResponseRedirect(request.POST.get("next", "/"))

    # TODO: put me in SETTINGS
    if "username" in request.POST and "password" in request.POST:
        authMethod = request.POST.get("authMethod", None)

        user = auth_service.authenticate(authMethod=authMethod, request=request)

        if user:
            next_page = request.POST.get("next", request.GET.get("next", "/"))
            user.backend = "django.contrib.auth.backends.ModelBackend"
            djauth.login(request, user)
            return HttpResponseRedirect(next_page)

        c = {"status": "Sorry, username and password don't match.", "error": True}

        return HttpResponseForbidden(
            render_response_index(request, "tardis_portal/login.html", c)
        )

    url = request.META.get("HTTP_REFERER", "/")
    u = urlparse(url)
    if u.netloc == request.META.get("HTTP_HOST", ""):
        next_page = u.path
    else:
        next_page = "/"
    c = {"next": next_page}

    c["RAPID_CONNECT_ENABLED"] = settings.RAPID_CONNECT_ENABLED
    c["RAPID_CONNECT_LOGIN_URL"] = settings.RAPID_CONNECT_CONFIG["authnrequest_url"]

    return render_response_index(request, "tardis_portal/login.html", c)


@sensitive_post_parameters("password")
@permission_required("tardis_portal.change_userauthentication")
@login_required()
def manage_auth_methods(request):
    """Manage the user's authentication methods using AJAX."""
    from ..auth.authentication import (
        add_auth_method,
        merge_auth_method,
        remove_auth_method,
        edit_auth_method,
        list_auth_methods,
    )

    if request.method == "POST":
        operation = request.POST["operation"]
        if operation == "addAuth":
            return add_auth_method(request)
        if operation == "mergeAuth":
            return merge_auth_method(request)
        if operation == "removeAuth":
            return remove_auth_method(request)
        return edit_auth_method(request)
    # if GET, we'll just give the initial list of auth methods for the user
    return list_auth_methods(request)
