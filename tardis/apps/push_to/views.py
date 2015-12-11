import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render
import requests

from paramiko import RSACert

from .exceptions import NoSuitableCredential
from .models import OAuthSSHCertSigningService, Credential, RemoteHost
from .oauth_tokens import get_token, get_token_data, set_token
from . import tasks
from tardis.tardis_portal.auth import decorators as authz
from ssh_authz import sign_certificate

# TODO: Remove 'verify=False' for requests


def render_error_message(request, message, status=500):
    return HttpResponse(
        render(
            request, 'error.html', {
                'message': message
            },
            status=status))


def render_success_message(request, message, status=200):
    return HttpResponse(
        render(
            request, 'success.html', {
                'message': message
            },
            status=status))


def get_push_url_for_host(remote_host, obj_type, push_obj_id):
    """
    Constructs a push-to URL to trigger data transfer
    :param remote_host: the RemoteHost to which data should be copied
    :param obj_type: data type to be copied (experiment, dataset or datafile)
    :param push_obj_id: the database object id
    :return: a push-to URL
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
    else:
        return None


@login_required
def get_accessible_hosts(request, obj_type=None, push_obj_id=None):
    """
    Retrieves all accessible hosts (i.e. hosts for which the user already has
    credentials for) including push-to trigger URLs if the object type and id
    are supplied
    :param request: request object
    :param obj_type: data type to be copied (experiment, dataset or datafile)
    :param push_obj_id: the database object id
    :return: json object with accessible hosts
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
    :param request: request object
    :param obj_type: data type to be copied (experiment, dataset or datafile)
    :param push_obj_id: the database object id
    :return: json object with signing services and hosts
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
@authz.experiment_download_required
def initiate_push_experiment(request, experiment_id, remote_host_id=None):
    """
    Kicks off push for experiment data
    :param request: request object
    :param experiment_id: experiment database id
    :param remote_host_id: remote host database id
    :return: redirect or status message
    """
    return _initiate_push(
        request, initiate_push_experiment, remote_host_id, 'experiment',
        experiment_id)


@login_required
@authz.dataset_download_required
def initiate_push_dataset(request, dataset_id, remote_host_id=None):
    """
    Kicks off push for dataset data
    :param request: request object
    :param dataset_id: dataset database id
    :param remote_host_id: remote host database id
    :return: redirect or status message
    """
    return _initiate_push(
        request, initiate_push_dataset, remote_host_id, 'dataset', dataset_id)


@login_required
@authz.datafile_access_required
def initiate_push_datafile(request, datafile_id, remote_host_id=None):
    """
    Kicks off push for datafile data
    :param request: request object
    :param datafile_id: datafile database id
    :param remote_host_id: remote host database id
    :return: redirect or status message
    """
    return _initiate_push(
        request, initiate_push_datafile, remote_host_id, 'datafile',
        datafile_id)


def _initiate_push(
    request, callback_view, remote_host_id, obj_type, push_obj_id
):
    """
    Kicks off data push
    :param request: request object
    :param callback_view: initiating view (e.g. initiate_push_datafile)
    :param remote_host_id: database id of remote host
    :param obj_type: the type of data
    :param push_obj_id: the data object id
    :return: status message, host list or OAuth2 redirects
    """
    # If the remote_host_id is not given, render a view to show a list of
    # acceptable hosts
    if remote_host_id is None:
        args = {'obj_type': obj_type, 'push_obj_id': push_obj_id}
        c = {
            'cert_signing_services_url': reverse(
                get_signing_services,
                kwargs=args),
            'accessible_hosts_url': reverse(
                get_accessible_hosts,
                kwargs=args)
        }
        return HttpResponse(render(request, 'host_list.html', c))

    try:
        remote_host = RemoteHost.objects.get(pk=remote_host_id)
        credential = get_credential(request, remote_host)
    except NoSuitableCredential:
        callback_args = {
            'remote_host_id': remote_host_id,
            obj_type + '_id': push_obj_id
        }
        callback_url = reverse(callback_view, kwargs=callback_args)
        redirect_args = {'remote_host_id': remote_host_id}
        redirect_url = reverse(
            authorize_remote_access,
            kwargs=redirect_args) + '?next=%s' % callback_url
        return redirect(redirect_url)

    if obj_type == 'experiment':
        tasks.push_experiment_to_host.delay(
            request.user.pk, credential.pk, remote_host_id, push_obj_id)
    elif obj_type == 'dataset':
        tasks.push_dataset_to_host.delay(
            request.user.pk, credential.pk, remote_host_id, push_obj_id)
    elif obj_type == 'datafile':
        tasks.push_datafile_to_host.delay(
            request.user.pk, credential.pk, remote_host_id, push_obj_id)

    success_message = ('The requested item will be pushed to %s. <strong>You '
                       'will be notified by email once this has been '
                       'completed.</strong>'
                       '<br/>'
                       'In most cases, your data will be pushed to your home '
                       'directory.'
                       '<pre>~/mytardis-data/&lt;timestamp&gt;/...</pre>')
    success_message %= remote_host.nickname
    return render_success_message(
        request,
        success_message)


def get_credential(request, remote_host):
    """
    Fetches a suitable credential for the remote host, or raises an exception
    if none found
    :param request: request object
    :param remote_host: the RemoteHost for which a credential should be found
    :return: the credential
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
                # If the credential contains a certificate, it's probably not
                # longer valid - delete it
                if isinstance(credential.key, RSACert):
                    credential.delete()
                    raise NoSuitableCredential()
        except Credential.DoesNotExist:
            raise NoSuitableCredential()

    return credential


def oauth_callback_url(request):
    """
    Builds the oauth callback URL
    :param request: request object
    :return: callback URL
    """
    return request.build_absolute_uri(reverse(oauth_callback))


@login_required
def authorize_remote_access(request, remote_host_id, service_id=None):
    """
    Generates an SSH certificate using an OAuth2 SSH signing service
    :param request: request object
    :param remote_host_id: remote host id
    :param service_id: OAuth2 SSH certificate signing service id
    :return: an error message or OAuth2 redirects
    """
    next_redirect = request.GET.get('next', '/')

    # Identify a suitable SSH cert signing service for the requested host
    try:
        if service_id is None:
            allowed_services = OAuthSSHCertSigningService\
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
    else:
        # We have a token, so try to create a credential and sign it
        # remote_user is overwritten once the cert is signed
        remote_user = 'unknown'
        credential = Credential.generate_keypair_credential(
            request.user, remote_user, [remote_host])
        if sign_certificate(
            credential, auth_token,
            oauth_service.cert_signing_url) and \
                credential.verify_remote_access(
        ):
            return redirect(next_redirect + '?credential_id=%i' % credential.pk)
        else:
            # If key signing failed, delete the credential
            credential.delete()
            return render_error_message(
                request, 'Could not sign SSH certificate',
                status=500)


@login_required
def oauth_callback(request):
    """
    OAuth2 callback endpoint to continue the SSH certificate signing process
    :param request: request object
    :return: error message or redirect to the signing service with access token
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

    # Verify=False is a bad thing, but I need it for now
    r = requests.post(
        oauth_service.oauth_token_url, data,
        auth=(
            oauth_service.oauth_client_id, oauth_service.oauth_client_secret),
        verify=False)
    token = json.loads(r.text)
    set_token(request, oauth_service, token)

    return redirect(next_redirect)
