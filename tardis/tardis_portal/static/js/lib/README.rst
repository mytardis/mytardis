Libraries (and what we use them for)
====================================

jQuery
------
URL: http://jquery.org

Hopefully you know what this is! We use it pretty much everywhere.


jQuery UI
---------
URL: http://jqueryui.com/

While we're phasing this out in favour of Bootstrap widgets where possible,
it provides useful widgets like "autocomplete" that are unlikely to be
replaced any time soon.

If you're going to use it, ask yourself if Bootstrap has an equivalent first.


Mustache.js (from django-mustachejs)
------------------------------------
URL: http://pypi.python.org/pypi/django-mustachejs/0.5.0

Regular logic-less `Mustache <http://mustache.github.com/>`_ templates, but
with Django integration.

If you're about to send HTML to the client, consider using a Mustache template
and some JSON first. (Reusing JSON services is much easier!)

For Javascript tests, mustache-0.3.0.js is copied into this directory, because
we can't use {% static ... %} to access it in the django-mustachejs package
because Django is not running during the Javascript tests.


Underscore.js
-------------
URL: http://underscorejs.org/

Functional programming support for JS which doesn't extend built-in objects.

Even if you're not a functional programmer, you'll see situations where "map"
would be really useful. MyTardis is written in Python, so this just continues
the theme. (Sorry, list comprehensions not included!)


Underscore.string.js
--------------------
URL: http://epeli.github.com/underscore.string/

String utility functions for Underscore.js. Some of them you'd assume JS should
already have, but it doesn't.

Site says it best:

    Underscore.string provides you several useful functions:
    capitalize, clean, includes, count, escapeHTML, unescapeHTML,
    insert, splice, startsWith, endsWith, titleize, trim, truncate
    and `so on <https://github.com/epeli/underscore.string#readme>`_.


Async.js
--------
URL: https://github.com/caolan/async

Essentially an asynchronous version of Underscore.js. Overkill for most
situations, it does implement useful functions like asynchronous memoize and
asynchronous mapping.
