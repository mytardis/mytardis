from __future__ import print_function

cmd = [
    "sphinx-apidoc",  # command
    "-o",
    "pydoc",  # output dir
    "-f",  # force overwrite
    "../tardis",
]

from subprocess import call

try:
    call(cmd)
except:
    print("command failed, trying import")  # command always seems to fail
    import sphinx.apidoc as apidoc

    apidoc.main(cmd)
