USE_TZ = True

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.

TIME_ZONE = "Australia/Melbourne"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html

LANGUAGE_CODE = "en-us"

# Date format to use by default. ("jS F Y" => "8th March 2012")
# https://docs.djangoproject.com/en/1.3/ref/templates/builtins/#std:templatefilter-date  # noqa

DATE_FORMAT = "jS F Y"
DATETIME_FORMAT = "jS F Y H:i"

# Setting IS_DST to True or False will avoid AmbiguousTimeError exception
# by moving the hour backwards or forwards by 1 respectively.
# For example, IS_DST=True would change a non-existent time of 2:30 to 1:30
# and IS_DST=False would change the time to 3:30.
# https://stackoverflow.com/questions/42399438/django-make-aware-usage
IS_DST = True
