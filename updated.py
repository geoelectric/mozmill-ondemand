#!/usr/bin/env python

# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the 'License'); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an 'AS IS' basis,
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
# either the GNU General Public License Version 2 or later (the 'GPL'), or
# the GNU Lesser General Public License Version 2.1 or later (the 'LGPL'),
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
from optparse import OptionParser

# Globals shared with callback
platform = None
script = None
cluster = None
debug = False

# Update test a build
def test_update(branch, platform, channel, script):
    args = ('python', script, branch, platform, channel)
    print '  running: %s' % (' '.join(args))
    p = subprocess.Popen(args)
    retcode = p.wait()
    # XXX: should do something if failed
    print '  finished, return code: %s' % retcode

# Define a callback
def got_message(data, message):
    global platform
    global script
    global cluster
    global debug

    try:
        # Ignore heartbeats and other mozmill daemon traffic
        if data['_meta']['routing_key'] != 'mozmill.update':
            # Ignoring. Print some info if we're in debug mode. Commented out because this
            # really is a for-dev only thing.
            #
            # if debug:
            #     print 'Ignoring message on routing key "%s"' % (data['_meta']['routing_key'])
            return

        # If you made it here, it's an update daemon request.

        # Grab the cluster if there is one
        if 'cluster' in data['payload']:
            requested_cluster = data['payload']['cluster']
        else:
            requested_cluster = ''

        # Based on cluster, are we responding to this request?

        # If we specified a daemon cluster, we only want requests for that cluster
        # The boolean logic is simplest nested like this, rather than anded.
        if cluster:
            if requested_cluster != cluster:
                # Ignoring. Print some info if we're in debug mode
                if debug:
                    if requested_cluster:
                        print 'Received request for cluster "%s"' % (requested_cluster)
                    else:
                        print 'Received request for unclustered'
                    print '  request is not for my cluster "%s", ignoring' % (cluster)
                return
        # Otherwise, we only want requests that don't specify a cluster
        else:
            if requested_cluster:
                # Ignoring. Print some info if we're in debug mode
                if debug:
                    print 'Received request for cluster "%s"' % (requested_cluster)
                    print "  I'm listening for unclustered, ignoring"
                return

        # If you made it here, you weren't screened out based on cluster. Print some info.

        # Grab the platform if there is one
        if 'platform' in data['payload']:
            requested_platform = data['payload']['platform']
        else:
            requested_platform = ''

        # Based on platform, are we responding to this request?

        # If a particular platform was requested and we're not that, we ignore it.
        if requested_platform and (requested_platform != platform):
            # Ignoring. Print some info if we're in debug mode
            if debug:
                print 'Received request for platform "%s"' % requested_platform
                print '  request is not for my platform "%s", ignoring' % platform
            return

        # If you made it here, you weren't screened out based on platform. Print some info.

        # Made it through the gauntlet. Time to run some tests.
        print 'Processing update test request...'

        if requested_cluster:
            print '  cluster = "%s"' % (requested_cluster)
        else:
            print '  cluster = unclustered'

        if requested_platform:
            print '  platform = "%s"' % requested_platform
        else:
            print '  platform = all platforms'

        branch = data['payload']['branch']
        channel = data['payload']['channel']
        print '  branch = %s' % (branch)
        print '  platform = %s' % (platform)
        print '  channel = %s' % (channel)
        test_update(branch, platform, channel, script)

        print 'Listening for next update test request...'
    finally:
        message.ack()

def main():
    global platform
    global script
    global cluster
    global debug

    # args/opts
    usage = """usage: %prog [options] platform

  Launches a listening daemon for the on-demand update system.

  Platform must be supplied. If an update is requested without a platform
  or for the supplied platform, the daemon will run the specified update
  script (or the default script, if not specified).

  If a cluster is specified, the daemon will only run updates for requests
  on that cluster. If no cluster is specified, the daemon will only run
  updates for requests with no cluster."""

    parser = OptionParser(usage=usage)
    parser.add_option('-c', '--cluster',
                      action='store', type='string', dest='cluster',
                      help='name of cluster to listen for')
    parser.add_option('-d', '--debug',
                      action='store_true', dest='debug', default=False,
                      help='print out extra debug information on ignored messages')
    parser.add_option('-s', '--script',
                      action='store', type='string', dest='script',
                      default='./release_update.py',
                      help='update script to run [default: %default]')
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error('incorrect number of arguments. Use "-h" for help.');

    platform = args[0]
    script = options.script
    cluster = options.cluster
    debug = options.debug

    # Generate a unique applabel
    label = 'mozmill.update-%s' % (uuid.uuid1().hex)
    pulse = consumers.PulseTestConsumer(applabel=label)
    print 'Registered with pulse server as %s' % (label)

    if cluster:
        print 'Deployed on cluster "%s"' % (cluster)
    else:
        print 'Deployed unclustered'

    print 'Will run update tests for platform "%s" using script "%s"' % (platform, script)

    if debug:
        print '(in debug mode)'

    # Tell the broker what to listen for and give the callback
    pulse.configure(topic='mozmill.#', callback=got_message)

    # Block and call the callback function when a message comes in
    print 'Listening for update test requests...'
    pulse.listen()

if __name__ == '__main__':
    main()
