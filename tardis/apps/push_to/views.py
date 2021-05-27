# pylint: disable=http-response-with-json-dumps,http-response-with-content-type-json
import json
import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import redirect, render

from tardis.apps.push_to.utils import list_subdirectories, can_copy, get_default_push_location
from tardis.tardis_portal.auth import decorators as authz
from . import tasks
from .exceptions import NoSuitableCredential
from .models import OAuthSSHCertSigningService, Credential, RemoteHost
from .oauth_tokens import get_token, get_token_data, set_token
from .ssh_authz import sign_certificate


def render_error_message(request, message, status=500):
    return render(
        request, 'error.html', {
            'message': message
        },
        status=status)


def render_success_message(request, message, status=200):
    return render(
        request, 'success.html', {
            'message': message
        },
        status=status)


def get_push_url_for_host(remote_host, obj_type, push_obj_id):
    """
    Constructs a push-to URL to trigger data transfer
    :param RemoteHost remote_host: the RemoteHost to which data should be copied
    :param obj_type: data type to be copied (experiment, dataset or datafile)
    :type obj_type: object
    :param int push_obj_id: the database object id
    :return: a push-to URL
    :rtype: basestring
    """
    push_view = None
    if obj_type == 'experiment':
        push_view = initiate_push_experiment
    elif obj_type == 'dataset':
        push_view = initiate_push_dataset
    elif obj_type == 'datafile':
        push_view = initiate_push_datafile

    if push_view is not None and push_obj_id is not None:
        return reverse(push_view,
                       kwargs={
                           obj_type + '_id': push_obj_id,
                           'remote_host_id': remote_host.pk
                       })
    return None


@login_required
def get_accessible_hosts(request, obj_type=None, push_obj_id=None):
    """
    Retrieves all accessible hosts (i.e. hosts for which the user already has
    credentials for) including push-to trigger URLs if the object type and id
    are supplied
    :param Request request: request object
    :param object obj_type: data type to be copied
        (experiment, dataset or datafile)
    :param int push_obj_id: the database object id
    :return: json object with accessible hosts
    :rtype: HttpResponse
    """
    hosts = RemoteHost.objects.filter(credential__user=request.user).distinct()
    response = []
    for h in hosts:
        try:
            Credential.get_suitable_credential(request.user, h)
            host = {'id': h.pk, 'name': h.nickname, 'hostname': h.host_name}
            if h.logo_img is not None:
                host['logo_img'] = h.logo_img
            push_url = get_push_url_for_host(h, obj_type, push_obj_id)
            if push_url is not None:
                host['push_url'] = push_url
            response.append(host)
        except NoSuitableCredential:
            pass

    return HttpResponse(json.dumps(response), content_type='application/json')


@login_required
def get_signing_services(request, obj_type=None, push_obj_id=None):
    """
    Retrieves all certificate signing services and associated hosts including
    push-to trigger URLs if the object type and id are supplied
    :param Request request: request object
    :param class obj_type: data type to be copied (experiment, dataset or datafile)
    :param int push_obj_id: the database object id
    :return: json object with signing services and hosts
    :rtype: HttpResponse
    """
    services = OAuthSSHCertSigningService.get_available_signing_services(
        request.user)
    response = []
    for svc in services:
        remote_hosts = []
        for h in svc.allowed_remote_hosts.all():
            host = {'id': h.pk, 'name': h.nickname, 'hostname': h.host_name}
            if h.logo_img is not None:
                host['logo_img'] = h.logo_img
            push_url = get_push_url_for_host(h, obj_type, push_obj_id)
            if push_url is not None:
                push_url = reverse(authorize_remote_access,
                                   kwargs={
                                       'remote_host_id': h.pk,
                                       'service_id': svc.pk
                                   }) + '?next=%s' % push_url
                host['push_url'] = push_url
            remote_hosts.append(host)
        service = {
            'id': svc.pk,
            'name': svc.nickname,
            'remote_hosts': remote_hosts
        }
        response.append(service)

    return HttpResponse(json.dumps(response), content_type='application/json')


@login_required
def validate_remote_path(request, remote_host_id):
    response = {}
    path = request.GET.get("path", None)

    try:
        remote_host = RemoteHost.objects.get(pk=remote_host_id)
    except:
        response["message"] = "Remote host does not exist."
        return HttpResponseNotFound(json.dumps(response), content_type="application/json")

    try:
        credential = get_credential(request, remote_host)
    except:
        response["message"] = "You don't have access to this host."
        return HttpResponseForbidden(json.dumps(response), content_type="application/json")

    try:
        ssh = credential.get_client_for_host(remote_host)
        sftp = ssh.open_sftp()
    except:
        response["message"] = "Unable to connect to this host."
        return HttpResponseForbidden(json.dumps(response), content_type="application/json")


    default_path = get_default_push_location(sftp)

    response["default"] = {
        "path": default_path,
        "valid_children": list_subdirectories(sftp, default_path)
    }

    if path is not None:
        real_path = []
        for current_dir in path.split("/"):
            test_path = "/".join(real_path + [current_dir])
            try:
                sftp.chdir(test_path)
                real_path.append(current_dir)
            except:
                break
        real_path = "/".join(real_path)
        response[path] = {
            "valid_children": list_subdirectories(sftp, real_path)
        }

    sftp.close()
    ssh.close()

    return HttpResponse(json.dumps(response), content_type="application/json")


@login_required
@authz.experiment_download_required
def initiate_push_experiment(request, experiment_id, remote_host_id=None):
    """
    Kicks off push for experiment data
    :param Request request: request object
    :param int experiment_id: experiment database id
    :param int remote_host_id: remote host database id
    :return: redirect or status message
    :rtype: HttpResponse
    """
    return _initiate_push(request, initiate_push_experiment, remote_host_id,
                          "experiment", experiment_id)


@login_required
@authz.dataset_download_required
def initiate_push_dataset(request, dataset_id, remote_host_id=None):
    """
    Kicks off push for dataset data
    :param Request request: request object
    :param int dataset_id: dataset database id
    :param int remote_host_id: remote host database id
    :return: redirect or status message
    :rtype: HttpResponse
    """
    return _initiate_push(request, initiate_push_dataset, remote_host_id,
                          "dataset", dataset_id)


@login_required
@authz.datafile_access_required
def initiate_push_datafile(request, datafile_id, remote_host_id=None):
    """
    Kicks off push for datafile data
    :param Request request: request object
    :param int datafile_id: datafile database id
    :param int remote_host_id: remote host database id
    :return: redirect or status message
    :rtype: HttpResponse
    """
    return _initiate_push(request, initiate_push_datafile, remote_host_id,
                          "datafile", datafile_id)


def _initiate_push(request, callback_view, remote_host_id, obj_type, push_obj_id):
    """
    Kicks off data push
    :param Request request: request object
    :param function callback_view: initiating view (e.g. initiate_push_datafile)
    :param int remote_host_id: database id of remote host
    :param class obj_type: the type of data
    :param int push_obj_id: the data object id
    :return: status message, host list or OAuth2 redirects
    :rtype: HttpResponse
    """

    # If the remote_host_id is not given, render a view to show a list of
    # acceptable hosts
    if remote_host_id is None:
        args = {
            'obj_type': obj_type,
            'push_obj_id': push_obj_id
        }
        c = {
            'cert_signing_services_url': reverse(get_signing_services, kwargs=args),
            'accessible_hosts_url': reverse(get_accessible_hosts, kwargs=args)
        }
        return render(request, 'host_list.html', c)

    remote_host = RemoteHost.objects.get(pk=remote_host_id)

    destination = request.GET.get("path", None)
    if destination is None:
        args = {
            "remote_host_id": remote_host_id
        }
        c = {
            'remote_path_verify_url': reverse(validate_remote_path, kwargs=args),
            'remote_destination_name': remote_host.nickname
        }
        return render(request, 'destination_selector.html', c)

    try:
        credential = get_credential(request, remote_host)
    except:
        callback_args = {
            'remote_host_id': remote_host_id,
            obj_type + '_id': push_obj_id
        }
        callback_url = reverse(callback_view, kwargs=callback_args)
        redirect_args = {'remote_host_id': remote_host_id}
        redirect_url = reverse(authorize_remote_access, kwargs=redirect_args) + \
                       "?next=%s" % callback_url
        return redirect(redirect_url)

    try:
        ssh = credential.get_client_for_host(remote_host)
        sftp = ssh.open_sftp()
        destination_ok, message = can_copy(sftp, obj_type, push_obj_id, destination)
        sftp.close()
        ssh.close()
    except Exception as e:
        return render_error_message(request, "Can't connect to this host: %s" % str(e))

    if not destination_ok:
        return render_error_message(request, "Invalid destination: %s" % message)

    priority = settings.DEFAULT_TASK_PRIORITY + 1

    params = [
        request.user.pk,
        credential.pk,
        remote_host_id,
        push_obj_id,
        destination
    ]

    if obj_type == "experiment":
        tasks.push_experiment_to_host.apply_async(args=params, priority=priority)
    elif obj_type == "dataset":
        tasks.push_dataset_to_host.apply_async(args=params, priority=priority)
    elif obj_type == "datafile":
        tasks.push_datafile_to_host.apply_async(args=params, priority=priority)

    # Log PushTo event
    if getattr(settings, "ENABLE_EVENTLOG", False):
        from tardis.apps.eventlog.utils import log
        log(
            action="PUSH_TO",
            extra={
                "id": push_obj_id,
                "type": obj_type
            },
            request=request
        )

    success_message = ('The requested item will be pushed to %s. <strong>You '
                       'will be notified by email once this has been '
                       'completed.</strong>'
                       '<br/>'
                       'Data will be pushed to '
                       '<pre>%s</pre>')
    success_message %= (remote_host.nickname, destination)
    return render_success_message(
        request,
        success_message)


def get_credential(request, remote_host):
    """
    Fetches a suitable credential for the remote host, or raises an exception
    if none found
    :param Request request: request object
    :param RemoteHost remote_host: the RemoteHost for which a credential
        should be found
    :return: the credential
    :rtype: object
    :raises NoSuitableCredential: raised when no credential is found
    """
    credential_id = request.GET.get('credential_id', None)

    # See if there are any suitable credentials, should none be supplied
    if credential_id is None:
        credential = Credential.get_suitable_credential(
            request.user, remote_host)
    else:
        try:
            credential = Credential.objects.get(
                pk=credential_id,
                user=request.user,
                remote_hosts=remote_host)
            if not credential.verify_remote_access(remote_host):
                # If the credential contains a certificate, it's probably no
                # longer valid - delete it
                if credential.key.public_blob:
                    credential.delete()
                    raise NoSuitableCredential()
        except Credential.DoesNotExist:
            raise NoSuitableCredential()

    return credential


def oauth_callback_url(request):
    """
    Builds the oauth callback URL
    :param Request request: request object
    :return: callback URL
    :rtype: basestring
    """
    return request.build_absolute_uri(reverse(oauth_callback))


def verify_redirect(request, redirect_url):
    if redirect_url[:1] != "/":
        root_url = "{0}://{1}/".format(request.scheme, request.get_host())
        if redirect_url.find(root_url) != 0:
            return root_url
    return redirect_url


@login_required
def authorize_remote_access(request, remote_host_id, service_id=None):
    """
    Generates an SSH certificate using an OAuth2 SSH signing service
    :param Request request: request object
    :param basestring remote_host_id: remote host id
    :param basestring service_id: OAuth2 SSH certificate signing service id
    :return: an error message or OAuth2 redirects
    :rtype: HttpRedirect
    """
    next_redirect = request.GET.get('next', '/')

    # Identify a suitable SSH cert signing service for the requested host
    try:
        if service_id is None:
            allowed_services = OAuthSSHCertSigningService \
                .get_available_signing_services(
                request.user).filter(
                allowed_remote_hosts__pk=remote_host_id)
            try:
                oauth_service = allowed_services[0]
                service_id = oauth_service.pk
            except IndexError:
                error_message = ('Could not find suitable cert signing service'
                                 ' for remote host')
                return render_error_message(
                    request,
                    error_message,
                    status=400)
        else:
            oauth_service = OAuthSSHCertSigningService.get_oauth_service(
                request.user, service_id)

        remote_host = oauth_service.allowed_remote_hosts.get(pk=remote_host_id)

    except OAuthSSHCertSigningService.DoesNotExist:
        return render_error_message(
            request, 'Invalid OAuth service',
            status=400)

    # Check whether we have a token already
    # get_token_data returns None if the token is missing or invalid
    auth_token = get_token(request, oauth_service)
    auth_token_data = get_token_data(oauth_service, auth_token)

    if auth_token_data is None:
        # No token, so redirect
        return redirect(
            oauth_service.oauth_authorize_url +
            '?response_type=code&client_id=%s&redirect_uri=%s&state=%s' %
            (oauth_service.oauth_client_id, oauth_callback_url(request),
             (str(service_id) + ',' + next_redirect)))
    # We have a token, so try to create a credential and sign it
    # remote_user is overwritten once the cert is signed
    remote_user = 'unknown'
    credential = Credential.generate_keypair_credential(
        request.user, remote_user, [remote_host])
    signing_result = sign_certificate(
        credential, auth_token,
        oauth_service.cert_signing_url) and \
                     credential.verify_remote_access(
                     )
    if signing_result:
        return redirect(
            verify_redirect(
                request,
                next_redirect + '?credential_id=%i' % credential.pk))
    # If key signing failed, delete the credential
    credential.delete()
    return render_error_message(
        request, 'Could not sign SSH certificate',
        status=500)


@login_required
def oauth_callback(request):
    """
    OAuth2 callback endpoint to continue the SSH certificate signing process
    :param Request request: request object
    :return: error message or redirect to the signing service with access token
    :rtype: HttpResponse
    """
    # Check for OAuth error message
    error = request.GET.get('error', None)
    if error is not None:
        error_message = ('Push failed! MyTardis was not authorized to access '
                         'the remote system.')
        return render_error_message(
            request,
            error_message)

    try:
        service_id, next_redirect = request.GET.get('state', '/').split(',')
    except ValueError:
        return render_error_message(request, 'Invalid state', status=400)

    try:
        oauth_service = OAuthSSHCertSigningService.get_oauth_service(
            request.user, service_id)
    except OAuthSSHCertSigningService.DoesNotExist:
        return render_error_message(
            request, 'Invalid OAuth service',
            status=404)
    auth_code = request.GET.get('code')
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'client_id': oauth_service.oauth_client_id,
        'redirect_uri': oauth_callback_url(request)
    }

    r = requests.post(
        oauth_service.oauth_token_url, data,
        auth=(
            oauth_service.oauth_client_id, oauth_service.oauth_client_secret))
    token = json.loads(r.text)
    set_token(request, oauth_service, token)

    return redirect(
        verify_redirect(
            request,
            next_redirect))
