#!/usr/bin/python

"""
Provides classes for connecting to a MythTV backend.

The MythTV class to handle connection to and querying of a MythTV backend.
The Recorder class representing and storing details of a tuner card.
The Program class for storing details of a TV program.
The Channel class for storing details of a TV channel.
The Guide class for storing details from the program guide.
"""
import os
import sys
import socket
import shlex
import socket
import code
from datetime import datetime

from MythDB import *
from MythLog import *

log = MythLog(CRITICAL, '#%(levelname)s - %(message)s', 'MythTV')

RECSTATUS = {
                'TunerBusy': -8,
                'LowDiskSpace': -7,
                'Cancelled': -6,
                'Deleted': -5,
                'Aborted': -4,
                'Recorded': -3,
                'Recording': -2,
                'WillRecord': -1,
                'Unknown': 0,
                'DontRecord': 1,
                'PreviousRecording': 2,
                'CurrentRecording': 3,
                'EarlierShowing': 4,
                'TooManyRecordings': 5,
                'NotListed': 6,
                'Conflict': 7,
                'LaterShowing': 8,
                'Repeat': 9,
                'Inactive': 10,
                'NeverRecord': 11,
                }

BACKEND_SEP = '[]:[]'
PROTO_VERSION = 40
PROGRAM_FIELDS = 46
# CHANNEL_FIELDS = 29

class MythTV:
        """
        A connection to a MythTV backend.
        """
        def __init__(self, conn_type='Monitor'):
                self.db = MythDB(sys.argv[1:])
                self.master_host = self.db.getSetting('MasterServerIP')
                self.master_port = int(self.db.getSetting('MasterServerPort'))

                if not self.master_host:
                        log.Msg(CRITICAL, 'Unable to find MasterServerIP in database')
                        sys.exit(1)
                if not self.master_port:
                        log.Msg(CRITICAL, 'Unable to find MasterServerPort in database')
                        sys.exit(1)

                try:
                        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.socket.settimeout(10)
                        self.socket.connect((self.master_host, self.master_port))
                        res = self.backendCommand('MYTH_PROTO_VERSION %s' % PROTO_VERSION).split(BACKEND_SEP)
                        if res[0] == 'REJECT':
                                log.Msg(CRITICAL, 'Backend has version %s and we speak version %s', res[1], PROTO_VERSION)
                                sys.exit(1)
                        res = self.backendCommand('ANN %s %s 0' % (conn_type, socket.gethostname()))
                        if res != 'OK':
                                log.Msg(CRITICAL, 'Unexpected answer to ANN command: %s', res)
                        else:
                                log.Msg(INFO, 'Successfully connected mythbackend at %s:%d', self.master_host, self.master_port)
                except socket.error, e:
                        log.Msg(CRITICAL, 'Couldn\'t connect to %s:%d (is the backend running)', self.master_host, self.master_port)
                        sys.exit(1)

        def backendCommand(self, data):
                """
                Sends a formatted command via a socket to the mythbackend.

                Returns the result from the backend.
                """
                def recv():
                        """
                        Reads the data returned from the backend.
                        """
                        # The first 8 bytes of the response gives us the length
                        data = self.socket.recv(8)
                        try:
                                length = int(data)
                        except:
                                return ''
                        data = []
                        while length > 0:
                                chunk = self.socket.recv(length)
                                length = length - len(chunk)
                                data.append(chunk)
                        return ''.join(data)

                command = '%-8d%s' % (len(data), data)
                log.Msg(DEBUG, 'Sending command: %s', command)
                self.socket.send(command)
                return recv()
# IGB

        def getRecordingList(self, arg):
                """Returns a list of recordings as program objects.
                   Passing   arg 'Delete' returns the items in 
                   descending order based on start time.
                   Passing arg 'Recording' returns programs currently
                   being recorded
                   Passing arg 'Play' (or anything else): Returns all items.
                   Note the list includes live TV.
                """
                mythtv = MythTV()
                programs = []
                res = self.backendCommand('QUERY_RECORDINGS ' + arg).split(BACKEND_SEP)
                num_progs = int(res.pop(0))
                log.Msg(DEBUG, '%s recordings', num_progs)
                for i in range(num_progs):
                        programs.append(Program(res[i * PROGRAM_FIELDS:(i * PROGRAM_FIELDS)
                                + PROGRAM_FIELDS]))
                return programs


        def getUpcomingRecordings(self):
                """Returns a list of upcoming recordings as program objects."""
                recordings = ''
                mythtv = MythTV()
                upcoming =  mythtv.getUpcomingRecordings()
                for i in range(len(upcoming)):
                        recordings = ('%s%s: %s\n%s\n%s\n\n' % (recordings, recording.title, \
            recording.starttime, recording.subtitle, recording.description)) 
                return recordings

        def getAllScheduledRecordings(self):
                """
                Returns a list of all scheduled recordings as program objects.
                """
                mythtv = MythTV()
                programs = []
                res = self.backendCommand('QUERY_GETALLSCHEDULED').split(BACKEND_SEP)
                num_progs = int(res.pop(0))
                log.Msg(DEBUG, '%s recordings', num_progs)
                for i in range(num_progs):
                        programs.append(Program(res[i * PROGRAM_FIELDS:(i * PROGRAM_FIELDS)
                                + PROGRAM_FIELDS]))
                return programs

        def getExpiring(self):
                """
                Returns a list of recordings about to expire as program objects.
                """
                mythtv = MythTV()
                programs = []
                res = self.backendCommand('QUERY_GETEXPIRING').split(BACKEND_SEP)
                num_progs = int(res.pop(0))
                log.Msg(DEBUG, '%s recordings', num_progs)
                for i in range(num_progs):
                        programs.append(Program(res[i * PROGRAM_FIELDS:(i * PROGRAM_FIELDS)
                                + PROGRAM_FIELDS]))
                return programs


        def getGuideDataThrough(self):
                """
                Returns the last date for which guide data is available.
                If successful the date is returned in the form 2007-02-03 22:00.
                On error 0000-00-00 00:00 is returned.
                """
                mythtv = MythTV()
                res = self.backendCommand('QUERY_GUIDEDATATHROUGH').split(BACKEND_SEP)

                return res

        def queryUptime(self):
                """
                Returns the system uptime in seconds. On error returns
                Could not determine uptime.
                """
                mythtv = MythTV()
                # Time is returned in seconds or "Could not determine uptime."
                # if not available.
                res = self.backendCommand('QUERY_UPTIME').split(BACKEND_SEP)

                return res

        def getSetting(self, hostname, setting):
                """
                Queries the remote host for a specific setting. 
                The backend will look in the MySQL database table 
                'settings', and attempt to return the value for the 
                given setting. It seems only settings with the 
                hostname set can be retrieved by this call.

                On error returns -1.
                """
                mythtv = MythTV()
                res = self.backendCommand('QUERY_SETTING ' + hostname + ' ' + setting).split(BACKEND_SEP)

                return res

# /IGB

        def getPendingRecordings(self):
                """
                Returns a list of Program objects which are scheduled to be recorded.
                """
                programs = []
                res = self.backendCommand('QUERY_GETALLPENDING').split(BACKEND_SEP)
                has_conflict = int(res.pop(0))
                num_progs = int(res.pop(0))
                log.Msg(DEBUG, '%s pending recordings', num_progs)
                for i in range(num_progs):
                        programs.append(Program(res[i * PROGRAM_FIELDS:(i * PROGRAM_FIELDS)
                                + PROGRAM_FIELDS]))
                return programs

        def getScheduledRecordings(self):
                """
                Returns a list of Program objects which are scheduled to be recorded.
                """
                programs = []
                res = self.backendCommand('QUERY_GETALLSCHEDULED').split(BACKEND_SEP)
                num_progs = int(res.pop(0))
                log.Msg(DEBUG, '%s scheduled recordings', num_progs)
                for i in range(num_progs):
                        programs.append(Program(res[i * PROGRAM_FIELDS:(i * PROGRAM_FIELDS)
                                + PROGRAM_FIELDS]))
                return programs

        def getUpcomingRecordings(self):
                """
                Returns a list of Program objects which are scheduled to be recorded.

                Sorts the list by recording start time and only returns those with
                record status of WillRecord.
                """
                def sort_programs_by_starttime(x, y):
                        if x.starttime > y.starttime:
                                return 1
                        elif x.starttime == y.starttime:
                                return 0
                        else:
                                return -1
                programs = []
                res = self.getPendingRecordings()
                for p in res:
                        if p.recstatus == RECSTATUS['WillRecord']:
                                programs.append(p)
                programs.sort(sort_programs_by_starttime)
                return programs

        def getRecorderList(self):
                """
                Returns a list of recorders, or an empty list if none.
                """
                recorders = []
                c = self.db.cursor()
                c.execute('SELECT cardid FROM capturecard')
                row = c.fetchone()
                while row is not None:
                        recorders.append(int(row[0]))
                        row = c.fetchone()
                c.close()
                return recorders

        def getFreeRecorderList(self):
                """
                Returns a list of free recorders, or an empty list if none.
                """
                res = self.backendCommand('GET_FREE_RECORDER_LIST').split(BACKEND_SEP)
                recorders = [int(d) for d in res]
                return recorders

        def getRecorderDetails(self, recorder_id):
                """
                Returns a Recorder object with details of the recorder.
                """
                c = self.db.cursor()
                c.execute("""SELECT cardid, cardtype, videodevice, hostname
                                FROM capturecard WHERE cardid = %s""", recorder_id)
                row = c.fetchone()
                if row:
                        recorder = Recorder(row)
                        return recorder
                else:
                        return None

        def getCurrentRecording(self, recorder):
                """
                Returns a Program object for the current recorders recording.
                """
                res = self.backendCommand('QUERY_RECORDER %s[]:[]GET_CURRENT_RECORDING' % recorder)
                return Program(res.split(BACKEND_SEP))

        def isRecording(self, recorder):
                """
                Returns a boolean as to whether the given recorder is recording.
                """
                res = self.backendCommand('QUERY_RECORDER %s[]:[]IS_RECORDING' % recorder)
                if res == '1':
                        return True
                else:
                        return False

        def isActiveBackend(self, hostname):
                """
                Returns a boolean as to whether the given host is an active backend
                """
                res = self.backendCommand('QUERY_IS_ACTIVE_BACKEND[]:[]%s' % hostname)
                if res == 'TRUE':
                        return True
                else:
                        return False
        def getChannels(self):
                """
                Returns a list of channels defined in the database.
                """
                channels = []
                c = self.db.cursor()
                c.execute("""SELECT * FROM channel""")
                row = c.fetchone()
                while row is not None:
                        channels.append(Channel(row))
                        row = c.fetchone()
                c.close()



                #while row is not None:
                #       channels = Channel(row)
                #       row = c.fetchone()
                #c.close()
                return channels


        def getGuideData(self, chan_id, date):
                """
                Get guide data for the channel and date specified.
                """
                # !TODO Error checking on channel id and date values.
                guide = []
                sql = """SELECT * FROM `program` WHERE (`chanid` = """ + chan_id + """) AND  ('""" + date + """ ' = DATE(`starttime`)) ORDER BY `starttime` ASC"""

                c = self.db.cursor()
                c.execute(sql)
                row = c.fetchone()
                while row is not None:
                        guide.append(Guide(row))
                        row = c.fetchone()
                c.close()
                return guide


class Guide:
        """
        Represents a single program from the program guide.
        """
        def __str__(self):
                return "%s (%s)" % (self.title, self.starttime.strftime('%Y-%m-%d %H:%M:%S'))

        def __repr__(self):
                return "%s (%s)" % (self.title, self.starttime.strftime('%Y-%m-%d %H:%M:%S'))

        def __init__(self, data):
                """
                Load data into the object.
                """
                self.chanid = data[0]
                self.starttime  = data[1]
                self.endtime  = data[2]
                self.title  = data[3]
                self.subtitle  = data[4]
                self.description  = data[5]
                self.category  = data[6]
                self.category_type  = data[7]
                self.airdate  = data[8]
                self.stars  = data[9]
                self.previouslyshown  = data[10]
                self.title_pronounce  = data[11]
                self.stereo  = data[12]
                self.subtitled  = data[13]
                self.hdtv  = data[14]
                self.closecaptioned  = data[15]
                self.partnumber  = data[16]
                self.parttotal  = data[17]
                self.seriesid  = data[18]
                self.originalairdate  = data[19]
                self.showtype  = data[20]
                self.colorcode  = data[21]
                self.syndicatedepisodenumber  = data[22]
                self.programid = data[23]
                self.manualid  = data[24]
                self.generic  = data[25]
                self.listingsource  = data[26]
                self.first  = data[27]
                self.last  = data[28]
                self.audioprop  = data[29]
                self.subtitletypes  = data[30]
                self.videoprop  = data[31]

class Channel:
        """Represents a MythTV channel
        """

        def __str__(self):
                return "%s (%s)" % (self.chanid, self.name)

        def __repr__(self):
                return "%s (%s)" % (self.chanid, self.name)


        def __init__(self, data):
                """
                Load data into the object.
                """
                self.chanid = data[0]
                self.channum = data[1]
                self.freqid = data[2]
                self.sourceid = data[3]
                self.callsign = data[4]
                self.name = data[5]
                self.icon = data[6]
                self.finetune = data[7]
                self.videofilters = data[8]
                self.xmltvid = data[9]
                self.recpriority = data[10]
                self.contrast = data[11]
                self.brightness = data[12]
                self.colour = data[13]
                self.hue = data[14]
                self.tvformat = data[15]
                self.commfree = data[16]
                self.visible = data[17]
                self.outputfilters = data[18]
                self.useonairguide = data[19]
                self.mplexid = data[20]
                self.serviceid = data[21]
                self.atscsrcid = data[22]
                self.tmoffset = data[23]
                self.atsc_major_chan = data[24]
                self.atsc_minor_chan = data[25]
                self.last_record = data[26]
                self.default_authority = data[27]
                self.commethod = data[28]
        
class Recorder:
        """
        Represents a MythTV capture card.
        """
        def __str__(self):
                return "Recorder %s (%s)" % (self.cardid, self.cardtype)

        def __repr__(self):
                return "Recorder %s (%s)" % (self.cardid, self.cardtype)

        def __init__(self, data):
                """
                Load the list of data into the object.
                """
                self.cardid = data[0]
                self.cardtype = data[1]
                self.videodevice = data[2]
                self.hostname = data[3]

class Program:
        """
        Represents a program with all the detail known.
        """
        def __str__(self):
                return "%s (%s)" % (self.title, self.starttime.strftime('%Y-%m-%d %H:%M:%S'))

        def __repr__(self):
                return "%s (%s)" % (self.title, self.starttime.strftime('%Y-%m-%d %H:%M:%S'))

        def __init__(self, data):
                """
                Load the list of data into the object.
                """
                self.title = data[0]
                self.subtitle = data[1]
                self.description = data[2]
                self.category = data[3]
                try:
                        self.chanid = int(data[4])
                except ValueError:
                        self.chanid = None
                self.channum = data[5] #chanstr
                self.callsign = data[6] #chansign
                self.channame = data[7]
                self.filename = data[8] #pathname
                self.fs_high = data[9]
                self.fs_low = data[10]
                self.starttime = datetime.fromtimestamp(int(data[11])) # startts
                self.endtime = datetime.fromtimestamp(int(data[12])) #endts
                self.duplicate = int(data[13])
                self.shareable = int(data[14])
                self.findid = int(data[15])
                self.hostname = data[16]
                self.sourceid = int(data[17])
                self.cardid = int(data[18])
                self.inputid = int(data[19])
                self.recpriority = int(data[20])
                self.recstatus = int(data[21])
                self.recordid = int(data[22])
                self.rectype = data[23]
                self.dupin = data[24]
                self.dupmethod = data[25]
                self.recstartts = datetime.fromtimestamp(int(data[26]))
                self.recendts = datetime.fromtimestamp(int(data[27]))
                self.repeat = int(data[28])
                self.programflags = data[29]
                self.recgroup = data[30]
                self.commfree = int(data[31])
                self.outputfilters = data[32]
                self.seriesid = data[33]
                self.programid = data[34]
                self.lastmodified = data[35]
                self.stars = float(data[36])
                self.airdate = data[37]
                self.hasairdate = int(data[38])
                self.playgroup = data[39]
                self.recpriority2 = int(data[40])
                self.parentid = data[41]
                self.storagegroup = data[42]
                self.audio_props = data[43]
                self.video_props = data[44]
                self.subtitle_type = data[45]

if __name__ == '__main__':
        banner = '\'m\' is a MythTV instance.'
        try:
                import readline, rlcompleter
        except:
                pass
        else:
                readline.parse_and_bind("tab: complete")
                banner = banner + " TAB completion is available."
        m = MythTV()
        namespace = globals().copy()
        namespace.update(locals())
        code.InteractiveConsole(namespace).interact(banner)

# vim: ts=4 sw=4:
