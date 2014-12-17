def email_pub_requires_authorisation(user_name, pub_url, approvals_url):
    return '''Hello!
A publication has been submitted by %s and requires approval by a publication administrator.
You may view the publication here: %s

This publication will not be publicly accessible until all embargo conditions are met following approval.
To approve this publication, please access the publication approvals interface here: %s
''' % (user_name,
       pub_url,
       approvals_url)


def email_pub_awaiting_approval(pub_title):
    return '''Hello!
Your publication, %s, has been submitted and is awaiting approval by an administrator.
You will receive a notification once his has occurred.''' % pub_title


def email_pub_approved(pub_title, message=None, doi=None):
    email_message='''Hello!
Your publication, %s, has been approved for release and will appear online following any embargo conditions.
''' % publication.title

    if doi is not None:
        email_message += '''A DOI has been assigned to this publication (%s) and will become active once your publication is released.
You may use cite using this DOI immediately.''' % doi

    if message:
        email_message += ''' ---
%s''' % message

    return email_message


def email_pub_rejected(pub_title, message=None):
    email_message='''Hello!
Your publication, %s, is unable to be released. Please contact your system administrator for further information.
''' % publication.title

    if message:
        email_message += ''' ---
%s''' % message

    return email_message


def email_pub_reverted_to_draft(pub_title, message=None):
    email_message='''Hello!
Your publication, %s, has been reverted to draft and may now be amended.
''' % publication.title

    if message:
        email_message += ''' ---
%s''' % message

    return email_message


def email_pub_released(pub_title, doi=None):
    email_message = '''Hello,
Your publication, %s, is now public!''' % pub.title
    if doi:
        email_message += 'You may view your publication here: http://dx.doi.org/%s' % doi
    return email_message
