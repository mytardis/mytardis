from tardis.default_settings import USER_MENU_MODIFIERS

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

USER_MENU_MODIFIERS.extend([
    'tardis.apps.openid_migration.user_menu_modifiers.add_migrate_account_menu_item'
])
'''
Adds a Migrate My Account menu item to the user menu.
'''

# ACCOUNT_MIGRATION_INSTRUCTIONS_LINK = 'https://storemonash.readthedocs.io/en/latest/account_migration.html'
ACCOUNT_MIGRATION_INSTRUCTIONS_LINK = ''
