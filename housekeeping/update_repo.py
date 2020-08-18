#!/usr/bin/env python
import sys
import os
import subprocess
import tempfile
from datetime import datetime
import semver
import pprint

pp = pprint.PrettyPrinter(indent=4)

now = datetime.now()

current_time = now.strftime("%H:%M:%S")
print("Current Time =", current_time)

if len(sys.argv) < 2 :
    print ('Small utility to update a local git repo to the latest (remote) tag')
    print ('Does nothing if the remote repository has no tags\n')
    print ('Usage: ')
    print (sys.argv[0], '<directory with local repo> [command after update] [cmd options]' )
    print ('\nExample:')
    print (sys.argv[0], '/home/ddosdb/ddosdb cp -R /home/ddosdb/ddosdb/ddosdb/. /opt/ddosdb/' )
    exit(1)

LOCAL_DIR  = sys.argv[1]

# get the remote URL from the local repo

sp = subprocess.run(
    ["git", "config", "--get", "remote.origin.url"],
    cwd = LOCAL_DIR,
    stdout=subprocess.PIPE)

REMOTE_GIT = sp.stdout.decode("utf-8")[:-1]

print("Checking updates for "+REMOTE_GIT)

# git ls-remote --tags  https://github.com/ddos-clearing-house/ddosdb
# lists the tags along with the commit hash (separated by a tab), e.g.
# 04637330ce55843d8fe7dcc1db92578fb7effa04	refs/tags/v0.1.0
# git log --pretty=oneline shows all commits
sp = subprocess.run(
    ["git", "ls-remote", "--tags", REMOTE_GIT],
    cwd = LOCAL_DIR,
    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

# One line per tag, so split on \n,
# but ignore the trailing \n of the last line to start with
taglines = sp.stdout.decode("utf-8")[:-1].split('\n')

if len(taglines) < 2:
    # No tags. Nothing to be done then
    print("No tags --> no updates needed")
    exit(0)

vdict = {}
cdict = {}
vlist = []
vlatest = "0.0.0"
# Put (commit) and (tag) into a dictonary,
# so we can print what version we're on

for tl in taglines:
    # commit is the first bit (before the tab '\t')
    cmt = tl.split('\t')[0]
    # tag is the last bit (from the last slash / to the end)
    v = tl.split('\t')[1].split('/')[-1]
    # if it doesn't start with a digit, assume it is vMajor.Minor.Patch
    if not v[0].isdigit():
        v = v[1:]
    try:
        version = semver.VersionInfo.parse(v)
    except ValueError as ve:
        print("Ignoring tag {} : {}".format(v, ve))
    else:
        vdict[v] = cmt
        cdict[cmt] = v
        vlist.append(v)
        if semver.compare(v, vlatest) == 1:
            vlatest = v

if len(vdict) == 0:
    # No tags. Nothing to be done then
    print("No (valid) tags --> no updates needed")
    exit(0)

# By using semantic version comparison we should now have the latest version
print("Latest version : {0} ({1})".format(vlatest, vdict[vlatest]))

# git show -s --format=%H
# Shows the local commit hash
sp = subprocess.run(
    ["git", "show", "-s", "--format=%H"],
    cwd = LOCAL_DIR,
    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

this_commit  = sp.stdout.decode("utf-8")[:-1]

if (this_commit in cdict):
    print ("This instance  : {0} ({1})".format(cdict[this_commit], this_commit))
else:
    print("This instance  : <Unknown>")

if this_commit != vdict[vlatest]:
    print("Updating to " + vlatest)
    # Do an update 'git pull origin master'
    # then a hard reset to the right commit
    # of the latest tag
    # Not very subtle, but it works...
    sp = subprocess.run(
        ["git", "pull", "origin", "master"],
        cwd = LOCAL_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Now reset hard
    sp = subprocess.run(
        ["git", "reset", "--hard", vdict[vlatest]],
        cwd = LOCAL_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Execute possible command specified
    if len(sys.argv) > 1 :
        print ("Command to execute after update: ", end="")
        for arg in sys.argv[2:]:
            print(arg+" ", end="")
        print()
        sp = subprocess.run(
            sys.argv[2:])

else:
    print("We are up to date")
