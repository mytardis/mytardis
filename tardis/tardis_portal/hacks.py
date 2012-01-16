"""
    hacks.py
    For hacks which should be removed at a later stage
"""
from django.core.exceptions import ImproperlyConfigured

def oracle_dbops_hack(f):
    """ affects only oracle - safe for other database engines """
    #  see https://code.djangoproject.com/ticket/11580

    # If the import fails, then we can't be using Oracle.
    try:
        import django.db.backends.oracle.base
    except ImproperlyConfigured:
        # We're not using Oracle, so return "f" (ie. no-op).
        return f

    def wrap(*args, **kwargs):
        original = django.db.backends.oracle.base.DatabaseOperations.field_cast_sql
        django.db.backends.oracle.base.DatabaseOperations.field_cast_sql = _patched_cast
        try:
            return f(*args, **kwargs)
        finally:
            django.db.backends.oracle.base.DatabaseOperations.field_cast_sql = original


    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

def _patched_cast(self, db_type):
    """ a workaround for icontains searches on LOB fields """
    #  see https://code.djangoproject.com/ticket/11580
    if db_type and db_type.endswith('LOB'):
        return "DBMS_LOB.SUBSTR(%s,2000,1)"
    else:
        return "%s"
