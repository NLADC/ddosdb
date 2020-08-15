#!/usr/bin/env python
import sys
import os
import subprocess
import tempfile
from datetime import datetime

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

tldict = {}

# Put (commit) and (tag) into a dictonary,
# so we can print what version we're on
for tl in taglines:
    cmt = tl.split('\t')[0]
    v = tl.split('\t')[1].split('/')[-1]
    tldict[cmt] = v

# Assuming that the last line is the most recent tag...
tagline_newest = sp.stdout.decode("utf-8")[:-1].split('\n')[-1]

latest_commit  = tagline_newest.split('\t')[0]
latest_version = tagline_newest.split('\t')[1].split('/')[-1]

print("Latest version : {0} ({1})".format(latest_version, latest_commit))

# git show -s --format=%H
# Shows the local commit hash
sp = subprocess.run(
    ["git", "show", "-s", "--format=%H"],
    cwd = LOCAL_DIR,
    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

this_commit  = sp.stdout.decode("utf-8")[:-1]

if (this_commit in tldict):
    print ("This instance  : {0} ({1})".format(tldict[this_commit], this_commit))
else:
    print("This instance  : <Unknown>")

if this_commit != latest_commit:
    print("Updating to " + latest_version)
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
        ["git", "reset", "--hard", latest_commit],
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
