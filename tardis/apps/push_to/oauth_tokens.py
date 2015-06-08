import json
import requests

OAUTH_AUTH_TOKENS = 'push_to_oauth_tokens'


def get_token(request, oauth_service):
    service_id = str(oauth_service.pk)
    auth_token = None
    if OAUTH_AUTH_TOKENS in request.session:
        tokens = request.session[OAUTH_AUTH_TOKENS]
    else:
        tokens = {}
        request.session[OAUTH_AUTH_TOKENS] = tokens
    if service_id in tokens and 'access_token' in tokens[service_id]:
        auth_token = tokens[service_id]['access_token']
    return auth_token


def get_token_data(oauth_service, token):
    if token is None:
        return
    # Verify=False is a bad thing, but I need it for now
    r = requests.get(
        oauth_service.oauth_check_token_url, {
            'token': token}, verify=False)
    decoded_token = json.loads(r.text)
    if 'error' in decoded_token:
        return
    else:
        return decoded_token


def set_token(request, oauth_service, token):
    service_id = oauth_service.pk
    if OAUTH_AUTH_TOKENS in request.session:
        tokens = request.session[OAUTH_AUTH_TOKENS]
    else:
        tokens = {}
    tokens[service_id] = token
    request.session[OAUTH_AUTH_TOKENS] = tokens
