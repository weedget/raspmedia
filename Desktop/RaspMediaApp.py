import packages.rmnetwork as network
from packages.rmnetwork.constants import *
import os, sys
try:
	import wx
except ImportError:
	raise ImportError,"Wx Python is required."

class ConnectFrame(wx.Frame):
	def __init__(self,parent,id,title):
		wx.Frame.__init__(self,parent,id,title)
		self.parent = parent
		self.Bind(wx.EVT_CLOSE, self.close)
		self.mediaCtrlFrame = None
		self.hosts = []
		self.mainSizer = wx.GridBagSizer()
		self.initGui()
		self.searchHosts()

	def close(self, event):
		self.Destroy()
		sys.exit(0)

	def initGui(self):
		# Text label
		label = wx.StaticText(self,-1,label="Available RaspMedia Players:")
		self.mainSizer.Add(label,(0,0),(1,2),wx.EXPAND)
		
		label = wx.StaticText(self,-1,label="(double-click to connect)")
		self.mainSizer.Add(label,(1,0),(1,2),wx.EXPAND)

		id=wx.NewId()
		self.hostList=wx.ListCtrl(self,id,size=(300,200),style=wx.LC_REPORT|wx.SUNKEN_BORDER)
		self.hostList.Show(True)

		self.hostList.InsertColumn(0,"Host Address", width = 200)
		self.hostList.InsertColumn(1,"Port", width = 100)
		self.mainSizer.Add(self.hostList, (2,0))
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.HostListDoubleClicked, self.hostList)

		self.SetSizerAndFit(self.mainSizer)
		self.Show(True)

	def HostFound(self, host):
		# self.hosts.Add(host)
		idx = self.hostList.InsertStringItem(0, host[0])

		port = str(host[1])
		print "Host insert in row " + str(idx) + ": " + host[0] + " - " + port
		self.hostList.SetStringItem(idx, 1, port)

	def searchHosts(self):
		network.udpresponselistener.registerObserver([OBS_HOST_SEARCH, self.HostFound])
		network.udpresponselistener.registerObserver([OBS_STOP, self.UdpListenerStopped])
		msgData = network.messages.getMessage(SERVER_REQUEST)
		dlgStyle =  wx.PD_AUTO_HIDE
		self.prgDialog = wx.ProgressDialog("Searching...", "Searching available RaspMedia Players...", maximum = 1, parent = self, style = dlgStyle)
		self.prgDialog.Pulse()
		network.udpconnector.sendMessage(msgData)

	def UdpListenerStopped(self):
		if self.prgDialog:
			self.prgDialog.Update(1)

	def HostListDoubleClicked(self, event):
		print "You double clicked ", event.GetText()
		self.Hide()
		self.mediaCtrlFrame = RaspMediaCtrlFrame(self.parent,-1,'RaspMedia Control')
		self.mediaCtrlFrame.setHost(event.GetText())
		self.mediaCtrlFrame.Bind(wx.EVT_CLOSE, self.ChildFrameClosed)
		self.mediaCtrlFrame.Show(True)
		self.mediaCtrlFrame.LoadRemoteFileList(None)

	def ChildFrameClosed(self, event):
		self.mediaCtrlFrame.Destroy()
		self.Show(True)
		pass


class RaspMediaCtrlFrame(wx.Frame):
	def __init__(self,parent,id,title):
		wx.Frame.__init__(self,parent,id,title)
		self.parent = parent
		self.path = os.getcwd()
		self.mainSizer = wx.GridBagSizer()
		self.configSizer = wx.GridBagSizer()
		self.playerSizer = wx.GridBagSizer()
		self.filesSizer = wx.GridBagSizer()
		self.prgDialog = None
		self.initialize()

	def setHost(self, hostAddress):
		self.host = hostAddress

	def initialize(self):

		self.SetupMenuBar()
		self.SetupFileLists()
		self.SetupPlayerSection()
		self.SetupConfigSection()
		# Text Entry
		# self.entry = wx.TextCtrl(self,-1,value=u"Enter text here...",style=wx.TE_PROCESS_ENTER)
		# sizer.Add(self.entry,(0,0),(1,1),wx.EXPAND)
		# self.Bind(wx.EVT_TEXT_ENTER, self.OnPressEnter, self.entry)

		# Text label
		#self.label = wx.StaticText(self,-1,label="Hello!")
		#self.label.SetBackgroundColour(wx.BLUE)
		#self.label.SetForegroundColour(wx.WHITE)
		#sizer.Add(self.label,(1,0),(1,2),wx.EXPAND)
		
		self.mainSizer.Add(self.playerSizer,(0,0))
		self.mainSizer.Add(self.filesSizer, (2,0))

		self.SetSizerAndFit(self.mainSizer)
		# self.SetSizeHints(self.GetSize().x,self.GetSize().y,-1,self.GetSize().y)
		self.Show(True)

	def SetupPlayerSection(self):
		# Text label
		label = wx.StaticText(self,-1,label="Remote Control:")
		self.playerSizer.Add(label,(0,0),(1,2),wx.EXPAND)
		
		# Play and Stop Button
		button = wx.Button(self,-1,label="Play")
		self.playerSizer.Add(button,(1,0))
		self.Bind(wx.EVT_BUTTON, self.playClicked, button)

		button = wx.Button(self,-1,label="Stop")
		self.playerSizer.Add(button,(2,0))
		self.Bind(wx.EVT_BUTTON, self.stopClicked, button)

	def SetupConfigSection(self):
		pass

	def SetupFileLists(self):
		# local list
		self.AddLocalList()
		self.AddRemoteList()

		button = wx.Button(self,-1,label="Change directory")
		self.filesSizer.Add(button,(1,0))
		self.Bind(wx.EVT_BUTTON, self.ChangeDir, button)
		button = wx.Button(self,-1,label="Refresh remote filelist")
		self.filesSizer.Add(button,(1,1))
		self.Bind(wx.EVT_BUTTON, self.LoadRemoteFileList, button)

	def AddLocalList(self):
		id=wx.NewId()
		self.localList=wx.ListCtrl(self,id,size=(300,400),style=wx.LC_REPORT|wx.SUNKEN_BORDER)
		self.localList.Show(True)

		self.localList.InsertColumn(0,"Local Files: " + self.path, width = 298)
		self.filesSizer.Add(self.localList, (0,0))
		self.UpdateLocalFiles()

	def AddRemoteList(self):
		id=wx.NewId()
		self.remoteList=wx.ListCtrl(self,id,size=(300,400),style=wx.LC_REPORT|wx.SUNKEN_BORDER)
		self.remoteList.Show(True)
		self.remoteList.InsertColumn(0,"Remote Files: ", width = 298)	
		self.filesSizer.Add(self.remoteList, (0,1))	

	def UpdateLocalFiles(self):
		self.localList.DeleteAllItems()
		for file in os.listdir(self.path):
			if not file.startswith('.') and '.' in file:
				self.localList.InsertStringItem(self.localList.GetItemCount(), file)

	def InsertReceivedFileList(self, serverAddr, files):
		self.remoteList.DeleteAllItems()
		files.sort()
		for file in files:
			if not file.startswith('.') and '.' in file:
				self.remoteList.InsertStringItem(self.remoteList.GetItemCount(), file)

	def SetupMenuBar(self):
		# menus
		fileMenu = wx.Menu()

		#FILE MENU
		menuOpen = fileMenu.Append(wx.ID_OPEN, "&Change directory"," Change directory")  #add open to File
		menuExit = fileMenu.Append(wx.ID_EXIT, "&Exit"," Terminate the program")  #add exit to File
		self.Bind(wx.EVT_MENU, self.ChangeDir, menuOpen)
		#MENUBAR
		menuBar = wx.MenuBar()
		menuBar.Append(fileMenu,"&File") # Adding the "filemenu" to the MenuBar

		self.SetMenuBar(menuBar)

	def ChangeDir(self, event):
		dlg = wx.DirDialog(self, message="Select a directory that contains images or videos you would like to browse and upload to your media player.", defaultPath=self.path, style=wx.DD_CHANGE_DIR)


		# Call the dialog as a model-dialog so we're required to choose Ok or Cancel
		if dlg.ShowModal() == wx.ID_OK:
			# User has selected something, get the path, set the window's title to the path
			filename = dlg.GetPath()
			print filename
			self.path = filename
			self.UpdateLocalFiles()
		dlg.Destroy() # we don't need the dialog any more so we ask it to clean-up

	def LoadRemoteFileList(self, event):
		network.udpresponselistener.registerObserver([OBS_FILE_LIST, self.InsertReceivedFileList])
		network.udpresponselistener.registerObserver([OBS_STOP, self.UdpListenerStopped])
		msgData = network.messages.getMessage(FILELIST_REQUEST)
		dlgStyle =  wx.PD_AUTO_HIDE
		self.prgDialog = wx.ProgressDialog("Loading...", "Loading filelist from player...", maximum = 1, parent = self, style = dlgStyle)
		self.prgDialog.Pulse()
		network.udpconnector.sendMessage(msgData, self.host)

	def UdpListenerStopped(self):
		if self.prgDialog:
			self.prgDialog.Update(1)

	def playClicked(self, event):
		msgData = network.messages.getMessage(PLAYER_START)
		network.udpconnector.sendMessage(msgData, self.host)

	def stopClicked(self, event):
		msgData = network.messages.getMessage(PLAYER_STOP)
		network.udpconnector.sendMessage(msgData, self.host)


# MAIN ROUTINE
if __name__ == '__main__':
	app = wx.App()
	# frame = RaspMediaCtrlFrame(None, -1, 'RaspMedia Control')
	frame = ConnectFrame(None, -1, 'RaspMedia Control')
	app.MainLoop()