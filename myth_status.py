#!/usr/bin/python

##   Copyright (C) 2008 Ian Barton.
##
##   This program is free software; you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation; either version 2, or (at your option)
##   any later version.
##
##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.




# Display mythtv status to stdout.
try:
    from MythTV.MythTV import *
    from MythTV.MythLog import *

except:
    print "MythTV module cannot be initialized."

import urllib
from xml.dom import minidom

# Url of the MythTV status page.
STATUS_URL = "http://mythtv.banter.local:6544/xml"

# Return human readable file sizes.
def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0


def get_xml_data():
    """
    Get the storage information from the MythTV xml status page.

    """
    output = '' 
    dom = minidom.parse(urllib.urlopen(STATUS_URL))
    
    #info = []
    #for node in dom.getElementsByTagName("Load"):
    #    info.append ({"avg1" : node.getAttribute('avg1'), "avg2" : node.getAttribute('avg2'), "avg3" : node.getAttribute('avg3')})


    node = dom.getElementsByTagName("Storage")
    bitref = node[0]

    drive_total_total = ''
    drive_total_used = ''
    percent_used = 0
    for key in bitref.attributes.keys():
        #print key, bitref.attributes[key].value
        if (key == "drive_total_total"):
            drive_total_total = sizeof_fmt(int(bitref.attributes[key].value)*1000)
        elif (key == "drive_total_used"):
            total_used = sizeof_fmt(int(bitref.attributes[key].value)*1000)

    output = 'Total disk space: %s with %s used' % (drive_total_total, total_used)

    return output

def get_myth_data():
    """
    Uses the python bindings to get information about the tuners,
    recent recordings and upcoming recordings.
    """
    myMyth = MythTV()

    recorders = myMyth.getRecorderList()


    output = 'Tuners:\n'
    status = 'Idle'
    for i in range(len(recorders)):
        recorder_data = myMyth.getRecorderDetails(recorders[i])
        is_recording = myMyth.isRecording(recorders[i])
        if (is_recording):
            status = "Recording"
            # Get the name of the recording.
            program = myMyth.getCurrentRecording(recorders[i])
            status = "Recording: %s (%s)" % (program.title, program.recgroup)
        else:
            status = "Idle"

        output = output + "%s (%s) %s\n" % (recorder_data.hostname, recorder_data.cardid, status)

    upcoming_recordings = myMyth.getUpcomingRecordings()
    upcoming = ''
    for i in range(len(upcoming_recordings)):
        upcoming = upcoming + "%s - %s (%s)\n" % (upcoming_recordings[i].starttime, upcoming_recordings[i].title, upcoming_recordings[i].channame)

        if i > 3:
            break
    output = output + "\nScheduled recordings:\n%s" % (upcoming)
    return output

def main():
    """

    """
    print get_xml_data()
    print get_myth_data()

if __name__ == '__main__':
    main()
