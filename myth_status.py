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

import os, urllib
from optparse import OptionParser
import ConfigParser
from xml.dom import minidom

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


# Url of the MythTV status page.
STATUS_URL = "http://localhost:6544/xml"

# Configuration file.
# CONFIG_FILE = ".mythconkyconfig"

# Return human readable file sizes.
def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0

def set_defaults():
    """
    Set up some defaults if the .mythconkyconfig file
    does not exist.
    """

    config = ConfigParser.ConfigParser()
    #config.read(os.path.expanduser("~/.mythconkyconfig")
    config.add_section('mythtv')
    config.set('mythtv', 'host', STATUS_URL)

    # Writing our configuration file to 'example.cfg'
    with open(os.path.expanduser("~/.mythconkyconfig"), 'wb') as configfile:
        config.write(configfile)

def read_config():
    """
    Read the configuration data.
    """
    config = ConfigParser.ConfigParser()
    config.read(os.path.expanduser("~/.mythconkyconfig"))
    host = config.get('mythtv', 'host', 1)
    return host            



def get_xml_data(host):
    """
    Get the storage information from the MythTV xml status page.

    """
    output = '' 
    dom = minidom.parse(urllib.urlopen(host))
    
    #info = []
    #for node in dom.getElementsByTagName("Load"):
    #    info.append ({"avg1" : node.getAttribute('avg1'), "avg2" : node.getAttribute('avg2'), "avg3" : node.getAttribute('avg3')})


    node = dom.getElementsByTagName("Storage")
    bitref = node[0]

    drive_total_total = ''
    drive_total_used = ''
    drive_total_free = ''
    int_total_used = 0
    int_total = 0
    int_free = 0
    for key in bitref.attributes.keys():
        if (key == "drive_total_total"):
            drive_total_total = sizeof_fmt(int(bitref.attributes[key].value)*1000000)
            int_total = int(bitref.attributes[key].value)
        elif (key == "drive_total_used"):
            total_used = sizeof_fmt(int(bitref.attributes[key].value)*1000000)
            int_total_used  = int(bitref.attributes[key].value)

    int_free = int_total - int_total_used
    drive_total_free = sizeof_fmt(int_free *1000000)
    output = 'Total disk space: %s with %s used (% s free)' % (drive_total_total, total_used, drive_total_free)

    return output

def get_myth_data(tuners, scheduled, recorded, expiring):
    """
    Uses the python bindings to get information about the tuners,
    recent recordings and upcoming recordings.
    """
    myMyth = MythTV()
    output = ''

    if (tuners):
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

    if (scheduled > 0):
        upcoming_recordings = myMyth.getUpcomingRecordings()
        upcoming_progs = ''
        if ((len(upcoming_recordings)) > scheduled):
            for recording in upcoming_recordings[0:scheduled]:
                upcoming_progs = upcoming_progs + "%s - %s (%s)\n" % (recording.starttime, recording.title, recording.channame)
            
        else:    
            for recording in range(upcoming_recordings):
                upcoming_progs = upcoming_progs + "%s - %s (%s)\n" % (recording.starttime, recording.title, recording.channame)
            
        output = output + "\nScheduled recordings:\n%s" % (upcoming_progs)

    if (recorded > 0):
        recorded_programs = myMyth.getRecordingList("Delete")
        recorded_progs = ''
        if ((len(recorded_programs)) > recorded):
            for  recording in recorded_programs[0:recorded]:
                recorded_progs = recorded_progs + "%s - %s (%s)\n" % (recording.starttime, recording.title, recording.channame)
        else:                
            for recording in recorded_programs:
                recorded_progs = recorded_progs + "%s - %s (%s)\n" % (recoring.starttime, recording.title, recording.channame)

        output = output + "\nRecent Recordings:\n%s" % (recorded_progs)

    if (expiring > 0):
        expiring_programs = myMyth.getExpiring()
        expiring_progs = ''
        if ((len(expiring_programs)) > expiring):
            for  recording in expiring_programs[0:expiring]:
                expiring_progs = expiring_progs + "%s - %s (%s)\n" % (recording.starttime, recording.title, recording.channame)
        else:
            for  recording in expiring_programs:
                expiring_progs = expiring_progs + "%s - %s (%s)\n" % (recording.starttime, recording.title, recording.channame)
            
            
        output = output + "\nRecordings about to expire:\n%s" % (expiring_progs)
        

    return output

def main():
    """

    """
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    parser.add_option("-d", "--disk-space",
                  help="Show available disk space", action = "store_true", default = False, dest = "disk_space")

    parser.add_option("-t", "--tuners",
                  help="Show information about tuners", action = "store_true", default = False, dest = "tuners")

    parser.add_option("-s", "--scheduled",
                  help="Show scheduled programs", type="int", default = 0, dest = "scheduled")

    parser.add_option("-r", "--recorded",
                  help="Show the most recent programs", type="int", default = 0, dest = "recorded")

    parser.add_option("-e", "--expiring",
                  help="Show  programs due to auto expire", type="int", default = 0, dest = "expire")

    (options, args) = parser.parse_args()

    # Check the configuration file exists.
    # If it doesn't create it with some defaults.
    if not os.path.isfile((os.path.expanduser("~/.mythconkyconfig"))):
        print "======================================"
        print ".mythconkyconfig status does not exist."
        print "Creating a file with default settings."
        print "Please check your settings."
        print "======================================"
        set_defaults()
        sys.exit()
    else:
        host = read_config()    
        
    if options.disk_space:
        print get_xml_data(host)
    print get_myth_data(options.tuners, options.scheduled, options.recorded, options.expire)

if __name__ == '__main__':
    main()
