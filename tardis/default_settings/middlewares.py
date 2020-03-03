MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tardis.tardis_portal.logging_middleware.LoggingMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'tardis.tardis_portal.auth.token_auth.TokenAuthMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
