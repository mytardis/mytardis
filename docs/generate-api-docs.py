cmd = [
    "sphinx-apidoc",  # command
    "-o", "pydoc",  # output dir
    "-f",  # force overwrite
    "../tardis",
]

from subprocess import call
try:
    call(cmd)
except:
    print "command failed, trying import"  # command always seems to fail
    import sphinx.apidoc as apidoc
    apidoc.main(cmd)

# delete api from auto docs because the Meta classes are interpreted by sphinx
# and lead to errors.

# apidoc can exclude whole paths, but not individual files. a future update
# may make this hack unnecessary, or a new API will

print 'fixing apidoc'
filename = 'pydoc/tardis.tardis_portal.rst'
with open(filename, 'r') as infile:
    lines = infile.readlines()

api_index = lines.index(':mod:`api` Module\n')
new_lines = lines[:api_index] + lines[api_index+8:]
with open(filename, 'w') as ofile:
    ofile.write(''.join(new_lines))

print 'removed:'
print ''.join(lines[api_index:api_index+8])
print 'end fixing apidoc'
