OPENID_NOTIFICATION_SENDER_EMAIL = 'sender@sender.com'

OPENID_MIGRATION_EMAIL_MESSAGES = {
    'migration_complete': ('[{site_title}] User Migration Completed Successfully',
                           '''\
Hello!

Your account with username "{user_name}" has been successfully migrated. \

Your old user account has been disabled.\
Please use "{auth_method}" \
to login to "{site_title}".

Please contact your site administrators if you think this is an error.

Regards,
{site_title} Team.
'''),
}

# OPENID_MIGRATE_FROM_LOGO = '/static/openid_migration/images/monash-uni-logo.png'
OPENID_MIGRATE_FROM_LOGO = ''
