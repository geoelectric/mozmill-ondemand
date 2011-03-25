#!/usr/bin/env python

# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is MozMill Test code.
#
# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2010
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Geo Mealer <gmealer@mozilla.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK ***** */


# Import
from mozillapulse import consumers
import sys
import subprocess
import uuid

# Globals shared with callback
platform = None
script = None

# Update test a build
def test_update(branch, platform, channel, script):
    args = ("python", script, branch, platform, channel)
    print "  running: %s" % (" ".join(args))
    p = subprocess.Popen(args)
    retcode = p.wait()
    # XXX: should do something if failed
    print "  finished, return code: %s" % retcode
 
# Define a callback
def got_message(data, message):
    global platform
    global script

    print "Processing update test request ..."

    # If platform is specified, this is a single platform test
    if 'platform' in data['payload']:
        requested_platform = data['payload']['platform']
        print '  received request for %s' % requested_platform
    else:
        requested_platform = ""
        print "  received request for all platforms"

    # If this is a single platform test, are we it?
    if requested_platform and (requested_platform != platform):
        print '  request is not for %s, ignoring' % platform
    else:
        print "Running update tests"
        branch = data['payload']['branch']
        channel = data['payload']['channel']
        print '  branch = %s' % (branch)
        print '  platform = %s' % (platform)
        print '  channel = %s' % (channel)
        test_update(branch, platform, channel, script)

    print "Listening for next update test request..."

def main():
    global platform
    global script

    # args
    if len(sys.argv) < 2:
        sys.exit("Usage: updated.py $platform [$path_to_update_script]")

    platform = sys.argv[1]
    if len(sys.argv) == 2:
        script = './release_update.py'
    else:
        script = sys.argv[2]

    # unique applabel
    label = 'mozmill.update-%s' % (uuid.uuid1().hex)
    pulse = consumers.PulseTestConsumer(applabel=label)
    print "Registered with pulse server as %s" % (label)
    print "Will run update tests for %s using %s" % (platform, script)

    # Tell the broker what to listen for and give the callback
    pulse.configure(topic='mozmill.update', callback=got_message)

    # Block and call the callback function when a message comes in
    print "Listening for update test requests..."
    pulse.listen()

if __name__ == "__main__":
    main()
