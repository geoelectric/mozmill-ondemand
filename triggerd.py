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
import urllib
import os
import sys
import subprocess

# Download a build
def download(url, destination):
    print '  downloading %s to %s' % (url, destination)
    urllib.urlretrieve(url, destination)
    # XXX: need to check result code
    print '  done downloading %s' % (destination)

# Update test a build
def test_update(binary, build, report_dest):
    python_loc = "/Users/geo/.virtualenvs/triggered/bin/python"
    update_loc = "/Users/geo/hg/mozmill-automation/testrun_update.py"
    args = (python_loc, update_loc, "--channel", "nightly",
                                    "--logfile", "/tmp/nightly.log",
                                    "--report", report_dest,
                                    "--target-buildid", build,
                                    binary)

    print "  running: %s" % (" ".join(args))
    p = subprocess.Popen(args)
    retcode = p.wait()
    # XXX: should do something if failed
    print "  finished, return code: %s" % retcode
 
# Define a callback
def got_message(data, message):
    print "processing new message..."
    print "%s" % (message)

    build = data['payload']['build']
    url = data['payload']['url']
    print "  build id = %s" % (build)
    print "  url = %s" % (url)

    # XXX: this should be improved w/ getopts/error handling
    destination_dir = sys.argv[1]

    # get full extension of the current filename
    current_file = url.split("/")[-1]
    current_ext = ".".join(current_file.split(".")[-3:]) # XXX: kludge!

    # does prev exist?
    # this should arguably be an open inside a try block
    prev_file = "%s/prev.%s" % (destination_dir, current_ext)
    print "  checking to see if '%s' exists" % (prev_file)
    if os.path.isfile(prev_file):
      print "  %s exists" % (prev_file)
      
      # XXX: needs getopts, etc.
      report_dest = sys.argv[2]
      test_update(prev_file, build, report_dest)

      print "  deleting %s" % (prev_file)
      os.remove(prev_file)
      
    download(url, prev_file)

def main():
    # unique applabel
    pulse = consumers.PulseTestConsumer(applabel='gmealer@mozilla.com|gmealer-pulse-build')

    # Tell the broker what to listen for and give the callback
    pulse.configure(topic='geo.build', callback=got_message)

    # Could also give multiple topics:
    # pulse.configure(topic=['topic1', 'topic2'], callback=got_message)

    # Block and call the callback function when a message comes in
    pulse.listen()

if __name__ == "__main__":
    main()
