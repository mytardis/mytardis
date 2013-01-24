cmd = ["sphinx-apidoc",  # command
       "-o", "pydoc",  # output dir
       "-f",  # force overwrite
       "../tardis",
   ]

from subprocess import call
try:
    call(cmd)
except:
    print "command failed, trying import"
    import sphinx.apidoc as apidoc
    apidoc.main(cmd)
