
def userinfo(claims, user):
    """
    If the OIDC provider app is installed, then this is needed to provide
    the default userinfo claim

    :param claims:
    :param user:
    :return claims:
    """
    # Populate claims dict.
    # import ipdb; ipdb.set_trace()
    claims['name'] = '{0} {1}'.format(user.first_name, user.last_name)
    if claims['name'].strip() == '':
        claims['name'] = user.username
    claims['given_name'] = user.first_name
    claims['family_name'] = user.last_name
    claims['email'] = user.email

    return claims
