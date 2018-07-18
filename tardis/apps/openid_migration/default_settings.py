OPENID_NOTIFICATION_SENDER_EMAIL = 'sender@sender.com'

OPENID_MIGRATION_EMAIL_MESSAGES = {
    'migration_complete': ('[Store.Monash] User Migration Completed Successfully',
                           '''\
Hello!

Your account with username "{user_name}" has been successfully migrated. \

Your old user account has been disabled.\
Please use "{auth_method}" \
to login to "{site_name}".

Please contact store.star.help@monash.edu if you think this is an error.

Regards,
Store.Monash Team.
                          
'''),
}
