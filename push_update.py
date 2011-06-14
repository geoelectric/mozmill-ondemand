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

# Import the pulse publishers
from mozillapulse import publishers

# Import some pre-baked message types
# Note messages can really be anything, these are just to make it clear
# for consumers
from mozillapulse.messages import base

import sys
from optparse import OptionParser

def main():
    # args/opts
    usage = """usage: %prog [options] branch channel

  Pushes a request for an on-demand update test to the listening daemon.

  Branch and channel must be supplied, and will be passed to the update
  script run by the daemon.

  If platform is supplied as an option, only daemons for that platform
  will run update tests. If platform is not supplied, all daemons will
  run update tests.

  If cluster is supplied as an option, only daemons for that cluster
  will run update tests. If cluster is not supplied, only daemons that
  did not supply a cluster will run update tests."""

    parser = OptionParser(usage=usage)
    parser.add_option('-c', '--cluster',
                      action='store', type='string', dest='cluster',
                      help='name of cluster to push to')
    parser.add_option('-p', '--platform',
                      action='store', type='string', dest='platform',
                      help='platform to push to [default: all]')
    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.error('incorrect number of arguments. Use "-h" for help.');

    branch = args[0]
    channel = args[1]

    # Message to send
    mymessage = base.GenericMessage()
    mymessage.routing_parts.append('mozmill.update')
    mymessage.data['what'] = 'This is a mozmill on-demand update test request'
    mymessage.data['branch'] = branch
    mymessage.data['channel'] = channel

    # Did we specify cluster? If so, add the cluster key
    if options.cluster:
        mymessage.data['cluster'] = options.cluster
        cluster_string = 'cluster=%s' % (options.cluster)
    else:
        cluster_string = 'unclustered'

    # Did we specify platform? If so, add the platform key
    if options.platform:
        mymessage.data['platform'] = options.platform
        platform_string = 'platform "%s"' % (options.platform)
    else:
        platform_string = 'all platforms'

    # Let the user know what we're running
    print 'Requesting update tests (%s) for %s: branch=%s, channel=%s' % (cluster_string,
                                                                          platform_string,
                                                                          branch,
                                                                          channel)

    # Make a publisher
    pulse = publishers.PulseTestPublisher()

    # Send the message to the broker through the proper exchange with the correct
    # routing key and payload
    pulse.publish(mymessage)

    # Disconnect to be nice to the server
    pulse.disconnect()

if __name__ == "__main__":
    main()
