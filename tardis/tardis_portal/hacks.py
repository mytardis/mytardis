"""
    hacks.py
    For hacks which should be removed at a later stage
"""
import django.db.backends.oracle.base

def oracle_dbops_hack(f):
    """ affects only oracle - safe for other database engines """
    #  see https://code.djangoproject.com/ticket/11580
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
