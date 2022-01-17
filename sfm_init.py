from __future__ import absolute_import



#discord
#------------------------------------------------------------------------
# DISCORD RPC MODULE WRITTEN BY https://github.com/niveshbirangal PORTED
# FROM PYTHON 3 TO PYTHON 2 BY "valance"
# DISCORD RPC PLUGIN FOR SOURCE FILMMAKER WRITTEN AS OF 12/01/2022 "valance"
# FEEL FREE TO  ALTER CODE BUT DO NOT REDISTRIBUTE
# v1.0
#------------------------------------------------------------------------


import time
from time import mktime
from abc import ABCMeta, abstractmethod
import json
import logging
import os
import stat
import socket
import sys
import struct
import uuid
from io import open

import sfm, sfmApp, sfmConsole
import PySide
from PySide import QtCore, QtGui, shiboken
from PySide.QtGui import *
from PySide.QtCore import *

import ast
# References:
# * https://github.com/devsnek/discord-rpc/tree/master/src/transports/IPC.js
# * https://github.com/devsnek/discord-rpc/tree/master/example/main.js
# * https://github.com/discordapp/discord-rpc/tree/master/documentation/hard-mode.md
# * https://github.com/discordapp/discord-rpc/tree/master/src
# * https://discordapp.com/developers/docs/rich-presence/how-to#updating-presence-update-presence-payload-fields


OP_HANDSHAKE = 0
OP_FRAME = 1
OP_CLOSE = 2
OP_PING = 3
OP_PONG = 4

logger = logging.getLogger(__name__)

# Clear console log so you don't eventually lag because python is reading 1000+ lines....
file = open(os.getcwd() + r"/usermod/console.log","w")
file.close()

class DiscordIpcError(Exception):
    pass


class DiscordIpcClient(object):

    __metaclass__ = ABCMeta
    #Work with an open Discord instance via its JSON IPC for its rich presence API.

    #In a blocking way.
    #Classmethod `for_platform`
    #will resolve to one of WinDiscordIpcClient or UnixDiscordIpcClient,
    #depending on the current platform.
    #Supports context handler protocol.
    

    def __init__(self, client_id):
        self.client_id = client_id
        self._connect()
        self._do_handshake()

        logger.info("connected via ID %s", client_id)

    @classmethod
    def for_platform(cls, client_id, platform=sys.platform):
        if platform == 'win32':
            return WinDiscordIpcClient(client_id)
        else:
            return UnixDiscordIpcClient(client_id)

    @abstractmethod
    def _connect(self):
        pass

    def _do_handshake(self):
        ret_op, ret_data = self.send_recv({'v': 1, 'client_id': self.client_id}, op=OP_HANDSHAKE)
        # {'cmd': 'DISPATCH', 'data': {'v': 1, 'config': {...}}, 'evt': 'READY', 'nonce': None}
        if ret_op == OP_FRAME and ret_data['cmd'] == 'DISPATCH' and ret_data['evt'] == 'READY':
            return
        else:
            if ret_op == OP_CLOSE:
                self.close()
            raise RuntimeError(ret_data)

    @abstractmethod
    def _write(self, date):
        pass

    @abstractmethod
    def _recv(self, size):
        pass
    def _recv_header(self):
        header = self._recv_exactly(8)
        return struct.unpack('<II', header)

    def _recv_exactly(self, size):
        buf = ""
        size_remaining = size
        while size_remaining:
            chunk = self._recv(size_remaining)
            buf += chunk
            size_remaining -= len(chunk)
        return buf

    def close(self):
        logger.warning("closing connection")
        try:
            self.send({}, op=OP_CLOSE)
        finally:
            self._close()

    @abstractmethod
    def _close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def send_recv(self, data, op=OP_FRAME):
        self.send(data, op)
        return self.recv()

    def send(self, data, op=OP_FRAME):
        logger.debug("sending %s", data)
        data_str = json.dumps(data, separators=(',', ':'))
        data_bytes = data_str.encode('utf-8')
        header = struct.pack("<II", op, len(data_bytes))
        self._write(header)
        self._write(data_bytes)

    def recv(self):
      # Receives a packet from discord.

      # Returns op code and payload.

        op, length = self._recv_header()
        payload = self._recv_exactly(length)
        data = json.loads(payload.decode('utf-8'))
        logger.debug("received %s", data)
        return op, data

    def set_activity(self, act):
        # act
        data = {
            'cmd': 'SET_ACTIVITY',
            'args': {'pid': os.getpid(),
                     'activity': act},
            'nonce': unicode(uuid.uuid4())
        }
        self.send(data)


class WinDiscordIpcClient(DiscordIpcClient):
    _pipe_pattern = R"\\?\pipe\discord-ipc-{}"

    def _connect(self):
        for i in xrange(10):
            os.chmod(self._pipe_pattern.format(i), 0777)
            path = self._pipe_pattern.format(i)

            try:
                self._f = open(path, "w+b")
            except OSError, e:
                logger.error("failed to open {!r}: {}".format(path, e))
            else:
                break
        else:
            return DiscordIpcError("Failed to connect to Discord pipe")

        self.path = path

    def _write(self, data):
        self._f.write(data)
        self._f.flush()

    def _recv(self, size):
        return self._f.read(size)

    def _close(self):
        self._f.close()


class UnixDiscordIpcClient(DiscordIpcClient):

    def _connect(self):
        self._sock = socket.socket(socket.AF_UNIX)
        pipe_pattern = self._get_pipe_pattern()

        for i in xrange(10):
            path = pipe_pattern.format(i)
            if not os.path.exists(path):
                continue
            try:
                self._sock.connect(path)
            except OSError, e:
                logger.error("failed to open {!r}: {}".format(path, e))
            else:
                break
        else:
            return DiscordIpcError("Failed to connect to Discord pipe")

    @staticmethod
    def _get_pipe_pattern():
        env_keys = ('XDG_RUNTIME_DIR', 'TMPDIR', 'TMP', 'TEMP')
        for env_key in env_keys:
            dir_path = os.environ.get(env_key)
            if dir_path:
                break
        else:
            dir_path = '/tmp'
        return os.path.join(dir_path, 'discord-ipc-{}')

    def _write(self, data):
        self._sock.sendall(data)

    def _recv(self, size):
        return self._sock.recv(size)

    def _close(self):
        self._sock.close()

client_id = '776865330437292052'  # Send the client ID to the rpc module

rpc_obj = DiscordIpcClient.for_platform(str(client_id))
print("SourceFilmmaker Discord Rich Presence by valance deployed.")
start_time = mktime(time.localtime())
tempo = 0

# Here's how it works, app gets added to menu, as the class is instanced it starts
# a timer even though the window isn't open, then we use
# sfm modules to retrieve data and some basic python to store settings
# when update happens, function opens file, reads settings, retrieve data
# and then sends discord the info.

class RPCSettingsUI(QtGui.QWidget):
    def __init__(self):
        
        super(RPCSettingsUI, self).__init__()
        self.Window()
        self.updateRPC()
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.updateRPC)
        timer.start(15000)

    def Window(self):

        with open(os.getcwd() + r'/usermod/rpcConfig.cfg', 'r') as rpcread:
            file = rpcread.readlines()
            for line in file:
                info = ast.literal_eval(line)

        grid = QtGui.QGridLayout()

        font = QtGui.QFont()
        font.setPointSize(13)

        self.showMapCheckBox = QtGui.QCheckBox()
        self.showMapCheckBox.setText("Show Map")
        self.showMapCheckBox.setToolTip("Show the map you're currently on")
        self.showMapCheckBox.setFont(font)
        self.showMapCheckBox.setChecked(info[0])
        grid.addWidget(self.showMapCheckBox, 0, 0, 1, 1, Qt.AlignHCenter)

        self.showProjectCheckBox = QtGui.QCheckBox()
        self.showProjectCheckBox.setText("Show Project Name")
        self.showProjectCheckBox.setToolTip("Show the session name you are currently working on")
        self.showProjectCheckBox.setChecked(info[1])
        grid.addWidget(self.showProjectCheckBox, 0, 1, 1, 1, Qt.AlignHCenter)
        self.showProjectCheckBox.setFont(font)

        self.showActivityCheckBox = QtGui.QCheckBox()
        self.showActivityCheckBox.setText("Show Activity")
        self.showActivityCheckBox.setToolTip("Show what you're currently doing, it's more like what is your goal, animating? finishing up a comission? rendering?")
        self.showActivityCheckBox.setChecked(info[2])
        grid.addWidget(self.showActivityCheckBox, 1, 0, 1, 1, Qt.AlignHCenter)
        self.showActivityCheckBox.setFont(font)

        self.showTimelineCheckBox = QtGui.QCheckBox()
        self.showTimelineCheckBox.setText("Show Current Timeline State")
        self.showTimelineCheckBox.setToolTip("Show if you are on the graph editor, clip or motion")
        self.showTimelineCheckBox.setChecked(info[3])
        grid.addWidget(self.showTimelineCheckBox, 1, 1, 1, 1, Qt.AlignHCenter)
        self.showTimelineCheckBox.setFont(font)

        self.showShotInfoCheckBox = QtGui.QCheckBox()
        self.showShotInfoCheckBox.setText("Show shot info")
        self.showShotInfoCheckBox.setToolTip("Show fps and shot name when hovering sfm icon")
        self.showShotInfoCheckBox.setChecked(info[5])
        grid.addWidget(self.showShotInfoCheckBox, 2, 0, 1, 1, Qt.AlignHCenter)
        self.showShotInfoCheckBox.setFont(font)

        self.enableCustomStatusCheckBox = QtGui.QCheckBox()
        self.enableCustomStatusCheckBox.setText("Enable Custom Activity")
        self.enableCustomStatusCheckBox.clicked.connect(lambda: self.updateUI())
        self.enableCustomStatusCheckBox.setChecked(info[4])
        grid.addWidget(self.enableCustomStatusCheckBox, 2, 1, 1, 1, Qt.AlignHCenter)
        self.enableCustomStatusCheckBox.setFont(font)



        self.activityComboBox = QtGui.QComboBox()
        self.activityComboBox.setToolTip("Grab a template of my current activities")
        self.activityComboBox.addItem("Working")
        self.activityComboBox.addItem("Working on")
        self.activityComboBox.addItem("Animating")
        self.activityComboBox.addItem("Rendering")
        self.activityComboBox.addItem("Studying")
        self.activityComboBox.addItem("Scenebuilding")
        self.activityComboBox.addItem("Open for comissions")
        self.activityComboBox.addItem("Finishing up a comission")
        self.activityComboBox.addItem("Looking for inspiration")
        self.activityComboBox.addItem("Blocking")
        self.activityComboBox.addItem("Splining")
        self.activityComboBox.addItem("Polishing")
        self.activityComboBox.setCurrentIndex(info[6])
        self.activityComboBox.setMinimumSize(0, 30)
        grid.addWidget(self.activityComboBox, 3, 0, 1, 2)

    

        self.customStatus = QtGui.QLineEdit()
        self.customStatus.setMinimumSize(0, 30)
        self.customStatus.setText(info[7])
        grid.addWidget(self.customStatus, 4, 0, 1, 2)

        self.iconComboBox = QtGui.QComboBox()
        self.iconComboBox.setToolTip("SELECT YOUR ICON")
        self.iconComboBox.addItem("Icon Style: 1")
        self.iconComboBox.addItem("Icon Style: 2")
        self.iconComboBox.setMinimumSize(0, 30)
        grid.addWidget(self.iconComboBox, 5, 0, 1, 2)
        self.iconComboBox.setCurrentIndex(info[8])

        self.buttonUpdate = QtGui.QPushButton()
        self.buttonUpdate.setText("Update Rich Presence")
        self.buttonUpdate.clicked.connect(lambda: self.buttonUpdateClicked())
        self.buttonUpdate.setMinimumSize(QSize(0, 40))
        grid.addWidget(self.buttonUpdate, 7, 0, 1, 2)

        self.buttonSave = QtGui.QPushButton()
        self.buttonSave.setText("Save Settings")
        self.buttonSave.clicked.connect(lambda: self.saveSettings())
        self.buttonSave.setMinimumSize(QSize(0, 40))
        grid.addWidget(self.buttonSave, 6, 0, 1, 2)

        # Reads configuration file to guarantee statuses don't get messy
        if info[4] == True: #If custom status enabled then disable the combobox and enable the input
            self.customStatus.setEnabled(True)
            self.activityComboBox.setEnabled(False)
        else:
            self.customStatus.setEnabled(False)
            self.activityComboBox.setEnabled(True)

            
        self.resize(842, 440)
        self.setLayout(grid)

    def messageBox(self, message):
        mensagem = QtGui.QMessageBox()
        mensagem.setText(message)
        mensagem.exec_()


    def saveSettings(self):
        info = []
        info.append(self.showMapCheckBox.isChecked()) # 0 
        info.append(self.showProjectCheckBox.isChecked()) # 1
        info.append(self.showActivityCheckBox.isChecked()) # 2
        info.append(self.showTimelineCheckBox.isChecked()) # 3
        info.append(self.enableCustomStatusCheckBox.isChecked()) # 4
        info.append(self.showShotInfoCheckBox.isChecked()) # 5
        info.append(self.activityComboBox.currentIndex()) # 6
        info.append(self.customStatus.text()) # 7
        info.append(self.iconComboBox.currentIndex()) # 7

        with open(os.getcwd() + r'/usermod/rpcConfig.cfg', 'w') as rpcwrite:
            rpcwrite.write(unicode(str(info), "utf-8"))
        self.messageBox("Settings Saved")

    def buttonUpdateClicked(self):
        self.messageBox("RPC Updated")
        #print("Updated")
        info = []
        with open(os.getcwd() + r'/usermod/rpcConfig.cfg', 'r') as rpcread:
            file = rpcread.readlines()
            for line in file:
                info = ast.literal_eval(line)

        # Dictionary starts a little bit empty so your configuration can be added later
        activity = { 
                "timestamps": {
                    "start": start_time
                },
                "assets": {

                }
            }

        ## READING CONF FILE
        
        if info[8] == 0: 
            activity['assets']['large_image'] = 'sfm1'
        else:
            
            activity['assets']['large_image'] = 'sfm2'
                
        if sfmApp.GetDocumentRoot() != None:
            state = ''
            
            if info[2] == True: # Show Activity
                if info[4] == True:
                    state =  self.customStatus.text()
                else:
                    self.activityComboBox.setCurrentIndex(info[6])
                    state = str(self.activityComboBox.currentText())

        
            if info[1] == True: # Show Project Name
                try:
                    state = state + ' on ' + str(sfmApp.GetMovie()).split('"')[1]
                except IndexError:  
                    state = state + " | Loading project..."
            
            if info[0] == True: # Show Map Name
                try:
                    consoleFile = open(os.getcwd() + r"/usermod/console.log", 'rb')
                    consoleText = consoleFile.read().splitlines()
                    consoleFile.close()


                    #This if serves the purpose of only getting the mapname if a session is loaded
                    if sfmApp.GetDocumentRoot() != None:
                        for i in range(0, len(consoleText)-1):
                        
                            activity['state'] = "Waiting for map to load..."
                            lineNumber = (len(consoleText)-1)-i
                            if str(consoleText[(len(consoleText)-1)-i]).startswith("Server Number:"):
                                mapname = consoleText[lineNumber - 3].split(':')[1]
                                #print(mapname)
                                activity['state'] = 'at ' + mapname
                                break
                    else:
                        activity['state'] = "| No map loaded "
                    
                except IndexError:
                    print("Index Error at map Name")
        
            if info[3] == True: # Show Timeline State
                activity['assets']['small_text'] = str(sfmApp.GetNameForTimelineMode(sfmApp.GetTimelineMode()))
                activity['assets']['small_image'] = str(sfmApp.GetNameForTimelineMode(sfmApp.GetTimelineMode())).lower().replace(" ", "")
            if info[5] == True: # Show Shot Stats
                activity['assets']['large_text'] = str(sfmApp.GetShotAtCurrentTime()).split('"')[1] + " " + str(sfmApp.GetFramesPerSecond()) + "fps | Currently at frame: " + str(sfmApp.GetHeadTimeInFrames())

            if state != '': # If any option related to activity appeared it should be added to state.
                activity['details'] = state
        else:
            activity['details'] = 'Loading project...'
            
        try:
            rpc_obj.set_activity(activity)
        except IOError:
            print("Discord not found")
        
    def updateRPC(self):
        #print("Updated")
        info = []
        with open(os.getcwd() + r'/usermod/rpcConfig.cfg', 'r') as rpcread:
            file = rpcread.readlines()
            for line in file:
                info = ast.literal_eval(line)

        # Dictionary starts a little bit empty so your configuration can be added later
        activity = { 
                "timestamps": {
                    "start": start_time
                },
                "assets": {

                }
            }

        ## READING CONF FILE
        
        if info[8] == 0: 
            activity['assets']['large_image'] = 'sfm1'
        else:
            
            activity['assets']['large_image'] = 'sfm2'
                
        if sfmApp.GetDocumentRoot() != None:
            state = ''
            
            if info[2] == True: # Show Activity
                if info[4] == True:
                    state =  self.customStatus.text()
                else:
                    self.activityComboBox.setCurrentIndex(info[6])
                    state = str(self.activityComboBox.currentText())

        
            if info[1] == True: # Show Project Name
                try:
                    state = state + ' on ' + str(sfmApp.GetMovie()).split('"')[1]
                except IndexError:  
                    state = state + " | Loading project..."
            
            if info[0] == True: # Show Map Name
                try:
                    consoleFile = open(os.getcwd() + r"/usermod/console.log", 'rb')
                    consoleText = consoleFile.read().splitlines()
                    consoleFile.close()


                    #This if serves the purpose of only getting the mapname if a session is loaded
                    if sfmApp.GetDocumentRoot() != None:
                        for i in range(0, len(consoleText)-1):
                        
                            activity['state'] = "Waiting for map to load..."
                            lineNumber = (len(consoleText)-1)-i
    
                            if str(consoleText[(len(consoleText)-1)-i]).startswith("Server Number:"):
                                mapname = consoleText[lineNumber - 3].split(':')[1]
                                #print(mapname)
                                activity['state'] = 'at ' + mapname
                                break
                    else:
                        activity['state'] = "| No map loaded "
                    
                except IndexError:
                    print("Index Error at map Name")
        
            if info[3] == True: # Show Timeline State
                activity['assets']['small_text'] = str(sfmApp.GetNameForTimelineMode(sfmApp.GetTimelineMode()))
                activity['assets']['small_image'] = str(sfmApp.GetNameForTimelineMode(sfmApp.GetTimelineMode())).lower().replace(" ", "")
            if info[5] == True: # Show Shot Stats
                activity['assets']['large_text'] = str(sfmApp.GetShotAtCurrentTime()).split('"')[1] + " " + str(sfmApp.GetFramesPerSecond()) + "fps | Currently at frame: " + str(sfmApp.GetHeadTimeInFrames())

            if state != '': # If any option related to activity appeared it should be added to state.
                activity['details'] = state
        else:
            activity['details'] = 'Loading project...'
        try:
            rpc_obj.set_activity(activity)
        except IOError:
            print("Discord not found")
            

        

    def updateUI(self):
        if self.enableCustomStatusCheckBox.isChecked() == True: #If custom status enabled then disable the combobox and enable the input
            self.customStatus.setEnabled(True)
            self.activityComboBox.setEnabled(False)
        else:
            self.customStatus.setEnabled(False)
            self.activityComboBox.setEnabled(True)

    # This section is responsible for adding the script
    # Into a proper menu section on SFM
    # Props to walropodes https://steamcommunity.com/id/walropodes
    
# This section is responsible for adding the script
# Into a proper menu section on SFM
# Props to walropodes https://steamcommunity.com/id/walropodes

main_window = sfmApp.GetMainWindow()

janela = RPCSettingsUI()
sfmApp.RegisterTabWindow( "RPCSettingsUI", "RPC Settings", shiboken.getCppPointer(janela)[0] )

for widget in main_window.children():
    if isinstance(widget, PySide.QtGui.QMenuBar):
        menu_bar = widget
        break

for menu_item in menu_bar.actions():
    if menu_item.text() == 'Windows':
        windows_menu = menu_item.menu()
        break

for action in windows_menu.actions():
    if action.text() == 'Script Editor':
        script_editor_action = action
        break

janelaDoRPC = QAction(QIcon(), u'RPC Settings', windows_menu)
janelaDoRPC.triggered.connect(lambda: sfmApp.ShowTabWindow("RPCSettingsUI"))
windows_menu.insertAction(script_editor_action, janelaDoRPC)
#end discord
