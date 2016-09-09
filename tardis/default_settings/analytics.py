# If you want enable user agent sensing, copy this to settings.py
# and uncomment it.
#
# USER_AGENT_SENSING = True
# if USER_AGENT_SENSING:
#    from os import environ
#    # Workaround for bug in ua_parser ... can't find its builtin copy
#    # of regexes.yaml ... in versions 0.3.2 and earlier.  Remove when fixed.
#    environ['UA_PARSER_YAML'] = '/opt/mytardis/current/ua_parser_regexes.yaml'
#
#    INSTALLED_APPS = INSTALLED_APPS + ('django_user_agents',)
#    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + \
#        ('django_user_agents.middleware.UserAgentMiddleware',)
