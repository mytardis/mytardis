# Authentication backends that requires admin approval process
# Should be same as AUTH_PROVIDERS entry format:
# ('name', 'display name', 'backend implementation')
# name - used as the key for the entry
# display name - used as the displayed value in the login form
# backend implementation points to the actual backend implementation
ADMIN_APPROVAL_REQUIRED = (
    ('Google', 'Google',
         'social_core.backends.google.GoogleOAuth2'),
)
