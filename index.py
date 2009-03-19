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

# An example showing how to use mod_python to show
# your Myth backend's status on a web page.

from mod_python import apache
import urllib, time


from xml.dom import minidom
try:
    from MythTV.MythTV import *

except:
    print "MythTV module cannot be initialized."

# Put this last to avoid circular import error, which gives
# mod_python object 'datetime.datetime' has no attribute 'datetime' error.
import datetime

# Return human readable file sizes.
def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0

def get_date_time():
    """
    Returns a date time formatted as an html header.
    """
    timestamp = datetime.datetime.now()
    date_time =  timestamp.strftime('%a %b %Y,  %H:%M %p') 
    return "<h2> %s </h2>" % (date_time)


def get_xml_data():
    """
    Query Myth backend and get xml data. Returns the data as
    an html formatted string for writing out to a web page.
    """
    output = '' 
    dom = minidom.parse(urllib.urlopen("http://mythtv.banter.local:6544/xml"))

    node = dom.getElementsByTagName("Storage")
    bitref = node[0]

    drive_total_total = ''
    drive_total_used = ''
    drive_1_used = ''
    drive_2_used = ''
    drive_1_free = ''
    drive_2_free = ''   
    drive_1_percent_free = ''
    drive_2_percent_free = ''
    percent_used = 0
    for key in bitref.attributes.keys():
        if (key == "drive_total_total"):
            drive_total_total = sizeof_fmt(int(bitref.attributes[key].value)*1000000)
        elif (key == "drive_total_used"):
            total_used = sizeof_fmt(int(bitref.attributes[key].value)*1000000)
        elif (key == "drive_1_used"):
            drive_1_used = sizeof_fmt(int(bitref.attributes[key].value)*1000000)
        elif (key == "drive_1_free"):
            drive_1_free = sizeof_fmt(int(bitref.attributes[key].value)*1000000)
        elif (key == "drive_2_used"):
            drive_2_used = sizeof_fmt(int(bitref.attributes[key].value)*1000000)
        elif (key == "drive_2_free"):
            drive_2_free = sizeof_fmt(int(bitref.attributes[key].value)*1000000)
    output = "<h2>Drive 1</h2><ul><li>%s free with %s used </li></ul>" % (drive_1_free, drive_1_used)
    output = "%s <h2>Drive 2</h2><ul><li>%s free with %s used </li></ul>" % (output, drive_2_free, drive_2_used)
    output = "%s <h2>Total disk space:</h2> <ul><li> %s with %s used</li></ul>" % (output, drive_total_total, total_used)

    return output

def get_myth_data():
    """
    Use the python bindings to query Mythtv for data that can be
    obtained from the xml status page. Returns the data in
    html.
    """
    myMyth = MythTV()

    recorders = myMyth.getRecorderList()


    output = "<h2>Tuners:</h2><ul>"
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

        output = output + "<li>%s (%s) %s</li>" % (recorder_data.hostname, recorder_data.cardid, status)
    output = output + "</ul>"
    upcoming_recordings = myMyth.getUpcomingRecordings()
    upcoming = ''

    for i in range(len(upcoming_recordings)):
        upcoming = upcoming + "<li>%s - %s (%s) </li>" % (upcoming_recordings[i].starttime, upcoming_recordings[i].title, upcoming_recordings[i].channame)

        if i > 3:
            break

    output = output + "<h2>Scheduled recordings:</h2><ul>%s</ul>" % (upcoming)

    output = output + "<h2>Previously Recorded: </h2><ul>"
    previously_recorded = myMyth.getRecordingList("Delete")
    

    for i in range(len(previously_recorded)):
        if not(previously_recorded[i].recgroup == "LiveTV"):
            output = output + "<li>%s %s</li>" % (previously_recorded[i].starttime, previously_recorded[i].title)
        if i > 3:
            break
    return output + "</ul>"



def handler(req):
    req.content_type = 'text/html'
    req.write ( "<html>" )
    req.write ( "<head>" )
    req.write ( "<title>MythTV Status</title>" )
    req.write("<link rel='stylesheet' type='text/css' media='screen' href='./mobile.css' />")
    req.write ( "</head>" )

    req.write("<body />")
    req.write("<h1>MythTV Status</h1>")
    req.write(get_date_time())
    req.write(get_xml_data())
    req.write(get_myth_data())
    req.write("</body>")
    req.write("</html>")
    return apache.OK

