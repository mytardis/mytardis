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
