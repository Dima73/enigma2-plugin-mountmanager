from . import _
from Screens.Screen import Screen
from enigma import eTimer
from Screens.MessageBox import MessageBox
from Screens.Setup import SetupSummary
from Screens.Standby import TryQuitMainloop
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config, ConfigSelection, NoSave
from Components.Sources.List import List
from Components.Console import Console
from Components.Sources.StaticText import StaticText
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Plugins.Plugin import PluginDescriptor
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists
from os import system
import fcntl
import os
from time import sleep
from re import search
from . import fstabViewer

plugin_version = "3.3"

# Equivalent of the _IO('U', 20) constant in the linux kernel.
USBDEVFS_RESET = ord('U') << (4 * 2) | 20 # same as USBDEVFS_RESET= 21780
EXT_LSUSB = "/usr/bin/lsusb"
update_usb_ids = "/usr/lib/enigma2/python/Plugins/SystemPlugins/MountManager/update-usbids.sh"
make_exfat = "/usr/lib/enigma2/python/Plugins/SystemPlugins/MountManager/make-exfat.sh"
umountfs = "/usr/lib/enigma2/python/Plugins/SystemPlugins/MountManager/umountfs.sh"
S99hdparm120 = "/usr/lib/enigma2/python/Plugins/SystemPlugins/MountManager/S99hdparm120.sh"
device2 = ''

BOX_NAME = "none"
MODEL_NAME = "none"
if os.path.exists("/proc/stb/info/vumodel") and not os.path.exists("/proc/stb/info/boxtype") and not os.path.exists("/proc/stb/info/hwmodel") and not os.path.exists("/proc/stb/info/gbmodel"):
	BOX_NAME = "vu"
	try:
		f = open("/proc/stb/info/vumodel")
		MODEL_NAME = f.read().strip()
		f.close()
	except:
		pass
elif os.path.exists("/proc/stb/info/boxtype") and not os.path.exists("/proc/stb/info/hwmodel") and not os.path.exists("/proc/stb/info/gbmodel"):
	BOX_NAME = "all"
	try:
		f = open("/proc/stb/info/boxtype")
		MODEL_NAME = f.read().strip()
		f.close()
	except:
		pass
elif os.path.exists("/proc/stb/info/model") and not os.path.exists("/proc/stb/info/hwmodel") and not os.path.exists("/proc/stb/info/gbmodel"):
	BOX_NAME = "dmm"
	try:
		f = open("/proc/stb/info/model")
		MODEL_NAME = f.read().strip()
		f.close()
	except:
		pass
elif os.path.exists("/proc/stb/info/hwmodel"):
	BOX_NAME = "all"
	try:
		f = open("/proc/stb/info/hwmodel")
		MODEL_NAME = f.read().strip()
		f.close()
	except:
		pass
elif os.path.exists("/proc/stb/info/gbmodel") and not os.path.exists("/proc/stb/info/hwmodel"):
	BOX_NAME = "all"
	try:
		f = open("/proc/stb/info/gbmodel")
		MODEL_NAME = f.read().strip()
		f.close()
	except:
		pass

if os.path.exists("/proc/stb/info/brandname"):
	try:
		f = open("/proc/stb/info/brandname")
		brandname = f.read().strip()
		if brandname == "Zgemma":
			MODEL_NAME = brandname
		f.close()
	except:
		pass


class DevicesMountPanel(Screen, ConfigListScreen):
	skin = """
	<screen position="center,center" size="680,462" title="Mount Manager">
		<ePixmap pixmap="skin_default/buttons/red.png" position="40,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="190,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="340,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="490,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="10,435" size="35,25" alphatest="on" />
		<widget name="key_red" position="40,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
		<widget name="key_green" position="190,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_yellow" position="340,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
		<widget name="key_blue" position="490,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
		<widget name="key_menu" position="50,435" zPosition="1" size="250,21" font="Regular;19" halign="center" valign="center" foregroundColor="#00ffc000" transparent="1" />
		<widget source="list" render="Listbox" position="10,50" size="660,340" scrollbarMode="showOnDemand" >
			<convert type="TemplatedMultiContent">
				{"template": [
				 MultiContentEntryText(pos = (90, 0), size = (480, 30), color = 0x0058bcff, color_sel = 0x00ffc000, font=0, text = 0),
				 MultiContentEntryText(pos = (110, 30), size = (600, 50), font=1, flags = RT_VALIGN_TOP, text = 1),
				  MultiContentEntryText(pos = (580, 0), size = (80, 18), font=2,color = 0x00999999, color_sel = 0x00999999, flags = RT_VALIGN_CENTER, text = 3),
				 MultiContentEntryPixmapAlphaBlend(pos = (0, 0), size = (80, 80), png = 2),
				],
				"fonts": [gFont("Regular", 23),gFont("Regular", 19),gFont("Regular", 17)],
				"itemHeight": 85
				}
			</convert>
		</widget>
		<widget name="lab1" zPosition="2" position="30,90" size="600,50" font="Regular;22" halign="center" transparent="1"/>
	</screen>"""

	def __init__(self, session):
		self.setup_title = _("Mount Manager - edit label/fstab")
		Screen.__init__(self, session)
		self['key_red'] = Label(" ")
		#self['key_green'] = Label(_("Reset USB devices"))
		self['key_green'] = Label()
		self['key_yellow'] = Label(_("Unmount"))
		self['key_blue'] = Label(_("Mount"))
		self['key_menu'] = Label(_("Setup Mounts"))
		self['lab1'] = Label()
		self.onChangedEntry = []
		self.list = []
		self.mbox = None
		self.Console = None
		self['list'] = List(self.list)
		self["list"].onSelectionChanged.append(self.selectionChanged)
		self['actions'] = ActionMap(['WizardActions', 'ColorActions', "MenuActions"], {'back': self.close, 'green': self.openListUSBdevice, 'red': self.saveMypoints, 'yellow': self.Unmount, 'blue': self.Mount, "menu": self.SetupMounts})
		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.updateList2)
		self.updateList()
		self.setTitle(self.setup_title + ": " + plugin_version)

	def createSummary(self):
		return DevicesMountPanelSummary

	def setMainTitle(self):
		self.setTitle(self.setup_title)

	def selectionChanged(self):
		#self.setMainTitle()
		self["key_red"].setText(" ")
		if len(self.list) == 0:
			return
		self.sel = self['list'].getCurrent()
		for line in self.sel:
			try:
				line = line.strip()
				#if line.find('Mount') >= 0:
				if _('Mount: ') in line:
					if line.find('/media/hdd') < 0:
						self["key_red"].setText(_("Use as HDD"))
			except:
				pass
		if self.sel:
			try:
				name = str(self.sel[0])
				desc = str(self.sel[1].replace('\t', '  '))
			except:
				name = ""
				desc = ""
		else:
			name = ""
			desc = ""
		for cb in self.onChangedEntry:
			cb(name, desc)

	def updateList(self, result=None, retval=None, extra_args=None):
		scanning = _("Wait please while scanning for devices...")
		self['lab1'].setText(scanning)
		self.activityTimer.start(500)

	def updateList2(self):
		self.activityTimer.stop()
		self.list = []
		list2 = []
		try:
			f = open('/proc/partitions', 'r')
			fd = open('/proc/mounts', 'r')
			mnt = fd.readlines()
			fd.close()
		except:
			self['list'].list = self.list
			self['lab1'].hide()
			self.selectionChanged()
			return
		for line in f.readlines():
			mount_list = []
			parts = line.strip().split()
			if not parts:
				continue
			device = parts[3]
			mmc = False
			if MODEL_NAME in ('Zgemma', 'sfx6008', 'sf8008', 'sf5008', 'sf8008m', 'et13000', 'et11000', 'et1x000', 'duo4k', 'duo4kse', 'uno4k', 'uno4kse', 'ultimo4k', 'solo4k', 'zero4k', 'hd51', 'hd52', 'dm820', 'dm7080', 'sf4008', 'dm900', 'dm920', 'gbquad4k', 'gbue4k', 'lunix3-4k', 'lunix-4k', 'vs1500', 'h7', '8100s', 'e4hd', 'gbmv200', 'multibox', 'multiboxse', 'h9se', 'h11', 'h9combo', 'h9combose', 'h9twin', 'h9twinse', 'h10', 'v8plus', 'hd60', 'hd61', 'hd66se', 'pulse4k', 'pulse4kmini', 'dual') and search('mmcblk0p[1-9]', device):
				continue
			if MODEL_NAME in ('xc7439', 'osmio4k', 'osmio4kplus', 'osmini4k') and search('mmcblk1p[1-9]', device):
				continue
			if device and search('mmcblk[0-9]p[1-9]', device):
				mmc = True
			if not mmc and not search('sd[a-z][1-9]', device):
				continue
			if device in list2:
				continue
			for x in mnt:
				if x.find(device) != -1 and x not in mount_list and '/omb' not in x:
					parts = x.strip().split()
					d1 = parts[1]
					mount_list.append(d1)
			self.buildMy_rec(device, mount_list)
			list2.append(device)
		f.close()
		self['list'].list = self.list
		self['lab1'].hide()
		self.selectionChanged()

	def buildMy_rec(self, device, moremount=[]):
		global device2
		device2 = ''
		card = False
		try:
			if device.find('1') > 1:
				device2 = device.replace('1', '')
		except:
			device2 = ''
		try:
			if device.find('2') > 1:
				device2 = device.replace('2', '')
		except:
			device2 = ''
		try:
			if device.find('3') > 1:
				device2 = device.replace('3', '')
		except:
			device2 = ''
		try:
			if device.find('4') > 1:
				device2 = device.replace('4', '')
		except:
			device2 = ''
		try:
			if device.find('5') > 1:
				device2 = device.replace('5', '')
		except:
			device2 = ''
		try:
			if device.find('6') > 1:
				device2 = device.replace('6', '')
		except:
			device2 = ''
		try:
			if device.find('7') > 1:
				device2 = device.replace('7', '')
		except:
			device2 = ''
		try:
			if device.find('8') > 1:
				device2 = device.replace('8', '')
		except:
			device2 = ''
		try:
			if device.find('p1') > 1:
				device2 = device.replace('p1', '')
		except:
			device2 = ''
		try:
			if device.find('p2') > 1:
				device2 = device.replace('p2', '')
		except:
			device2 = ''
		try:
			if device.find('p3') > 1:
				device2 = device.replace('p3', '')
		except:
			device2 = ''
		try:
			if device.find('p4') > 1:
				device2 = device.replace('p4', '')
		except:
			device2 = ''
		try:
			if device.find('p5') > 1:
				device2 = device.replace('p5', '')
		except:
			device2 = ''
		try:
			if device.find('p6') > 1:
				device2 = device.replace('p6', '')
		except:
			device2 = ''
		try:
			if device.find('p7') > 1:
				device2 = device.replace('p7', '')
		except:
			device2 = ''
		try:
			if device.find('p8') > 1:
				device2 = device.replace('p8', '')
		except:
			device2 = ''
		try:
			devicetype = os.path.realpath('/sys/block/' + device2 + '/device')
		except:
			devicetype = ''
		d2 = device
		model = "-?-"
		name = "USB: "
		if 'sdhci' in devicetype or device2.startswith('mmcblk'):
			name = _("MMC: ")
			card = True
			try:
				model = open('/sys/block/' + device2 + '/device/name').read()
				model = str(model).replace('\n', '')
			except:
				pass
			mypixmap = '/usr/lib/enigma2/python/Plugins/SystemPlugins/MountManager/icons/dev_mmc.png'
		else:
			mypixmap = '/usr/lib/enigma2/python/Plugins/SystemPlugins/MountManager/icons/dev_usb.png'
			try:
				model = open('/sys/block/' + device2 + '/device/model').read()
				model = str(model).replace('\n', '')
			except:
				pass
		try:
			if card:
				dev_name = 'mmcblk0'
			else:
				dev_name = device2
			data = open("/sys/block/%s/queue/rotational" % dev_name, "r").read().strip()
			rotational = int(data)
		except:
			rotational = True
		try:
			if card:
				dev_name = 'mmcblk0'
			else:
				dev_name = device2
			data = open("/sys/block/%s/removable" % dev_name, "r").read().strip()
			removable = int(data)
		except:
			removable = False
		des = ''
		if devicetype.find('/devices/pci') != -1 or devicetype.find('ahci') != -1 or devicetype.find('.sata/') != -1:
			name = _("HARD DISK: ")
			mypixmap = '/usr/lib/enigma2/python/Plugins/SystemPlugins/MountManager/icons/dev_hdd.png'
			if not card and not removable and not rotational:
				name = "SSD: "
				mypixmap = '/usr/lib/enigma2/python/Plugins/SystemPlugins/MountManager/icons/dev_ssd.png'
		if name == "USB: " and not removable and rotational:
			mypixmap = '/usr/lib/enigma2/python/Plugins/SystemPlugins/MountManager/icons/dev_usb_drive.png'
		try:
			vendor = open('/sys/block/' + device2 + '/device/vendor').read()
		except:
			vendor = ""
		if vendor and model:
			fullname = name + vendor + " (" + model + ")"
		elif vendor:
			fullname = name + vendor
		elif model:
			fullname = name + model
		else:
			fullname = name +  "-?-"
		self.Console = Console()
		if not os.path.exists("/usr/sbin/sfdisk"):
			self.Console.ePopen("opkg install util-linux-sfdisk > /dev/null")
			sleep(0.5)
		self.Console.ePopen("sfdisk -l /dev/sd? | grep swap | awk '{print $(NF-9)}' >/tmp/devices.tmp")
		sleep(0.5)
		try:
			f = open('/tmp/devices.tmp', 'r')
			swapdevices = f.read()
			f.close()
		except:
			swapdevices = ''
		if os.path.exists('/tmp/devices.tmp'):
			os.remove('/tmp/devices.tmp')
		swapdevices = swapdevices.replace('\n', '')
		swapdevices = swapdevices.split('/')
		f = open('/proc/mounts', 'r')
		for line in f.readlines():
			if line.find(device) != -1 and '/omb' not in line:
				parts = line.strip().split()
				d1 = parts[1]
				dtype = parts[2]
				rw = parts[3]
				break
				continue
			else:
				if device in swapdevices:
					parts = line.strip().split()
					d1 = _("None")
					dtype = 'swap'
					rw = _("None")
					break
					continue
				else:
					d1 = _("None")
					dtype = _("unavailable")
					rw = _("None")
		f.close()
		partition = False
		f = open('/proc/partitions', 'r')
		for line in f.readlines():
			if line.find(device) != -1:
				parts = line.strip().split()
				size = int(parts[2])
				if (((float(size) / 1024) / 1024) / 1024) > 1:
					des = "%s%s%s" % (_("Size: "), str(round((((float(size) / 1024) / 1024) / 1024), 2)), _("TB"))
				elif ((size / 1024) / 1024) > 1:
					des = "%s%s%s" % (_("Size: "), str(round(((float(size) / 1024) / 1024), 2)), _("GB"))
				else:
					des = "%s%s%s" % (_("Size: "), str(round((float(size) / 1024), 2)), _("MB"))
			else:
				try:
					size = open('/sys/block/' + device2 + '/' + device + '/size').read()
					size = str(size).replace('\n', '')
					size = int(size)
				except:
					size = 0
				if ((((float(size) / 2) / 1024) / 1024) / 1024) > 1:
					des = "%s%s%s" % (_("Size: "), str(round(((((float(size) / 2) / 1024) / 1024) / 1024), 2)), _("TB"))
				elif (((size / 2) / 1024) / 1024) > 1:
					des = "%s%s%s" % (_("Size: "), str(round((((float(size) / 2) / 1024) / 1024), 2)), _("GB"))
				else:
					des = "%s%s%s" % (_("Size: "), str(round(((float(size) / 2) / 1024), 2)), _("MB"))
		f.close()
		if des != '':
			if rw.startswith('rw'):
				rw = ' R/W'
			elif rw.startswith('ro'):
				rw = ' R/O'
			else:
				rw = ""
			prev_des = des
			des += '\t' + _("Mount: ") + d1 + '\n' + _("Device: ") + '/dev/' + device + '\t' + _("Type: ") + dtype + rw
			png = LoadPixmap(mypixmap)
			extmount = False
			num_mount = len(moremount)
			extmount = num_mount > 1 and _("%s points") % str(num_mount) or ""
			res = (fullname, des, png, extmount)
			self.list.append(res)
			if num_mount > 1:
				for mnt in moremount:
					if str(mnt) != d1:
						prev_des += '\t' + _("Mount: ") + str(mnt) + '\n' + _("Device: ") + '/dev/' + device + '\t' + _("Type: ") + dtype + rw
						res = (fullname, prev_des, png, extmount)
						if res not in self.list:
							self.list.append(res)

	def openListUSBdevice(self):
		pass
		#if fileExists(EXT_LSUSB):
		#	if not fileExists('/usr/share/usb.ids'):
		#		self.session.open(MessageBox, _("'/usr/share/usb.ids' not found!\nPlease install package usbutils!"), MessageBox.TYPE_ERROR, timeout=5)
		#	else:
		#		self.Console = Console()
		#		cmd = "%s > /tmp/ext_lsusb.tmp" % EXT_LSUSB
		#		self.Console.ePopen(cmd, self.openListUSBdeviceAnswer, [])
		#else:
		#	self.session.open(MessageBox, _("'%s' not found!") % EXT_LSUSB, MessageBox.TYPE_ERROR, timeout=5)

	def openListUSBdeviceAnswer(self, result=None, retval=None, extra_args=None):
		if result is None:
			self.session.open(MessageBox, _("Error response '%s'!") % EXT_LSUSB, MessageBox.TYPE_ERROR, timeout=5)
		else:
			entrylist = []
			try:
				f = open('/tmp/ext_lsusb.tmp', 'r')
			except:
				return
			for line in f.readlines():
				if line.startswith('Bus') and line.find('root hub') < 0 and line.find('dead:beef') < 0:
					parts = line.split()
					if len(parts) > 4:
						bus = parts[1]
						dev = parts[3][:3]
						dev_path = '/dev/bus/usb/%s/%s' % (bus, dev)
						entrylist.append((line, dev_path))
			f.close()
			if fileExists('/tmp/ext_lsusb.tmp'):
				try:
					os.remove('/tmp/ext_lsusb.tmp')
				except:
					pass
			if entrylist:
				def ChoiceAction(choice):
					if choice is not None:
						self.send_reset(choice[1])
				self.session.openWithCallback(ChoiceAction, ChoiceBox, list=entrylist, title=_("Select device for reset:"))

	def send_reset(self, dev_path=''):
		if dev_path != '':
			if not fileExists(dev_path):
				self.session.open(MessageBox, _("'%s' not found!") % dev_path, MessageBox.TYPE_ERROR, timeout=5)
				return
			try:
				#fd = os.open(dev_path, os.O_WRONLY)
				fd = open(dev_path, 'w', os.O_WRONLY)
			except:
				self.session.open(MessageBox, _("Error opening output file '%s'!") % dev_path, MessageBox.TYPE_ERROR, timeout=5)
				return
			try:
				fcntl.ioctl(fd, USBDEVFS_RESET, 0)
				#os.close(fd)
				fd.close()
				self.session.open(MessageBox, _("Reset successful '%s'!") % dev_path, MessageBox.TYPE_INFO, timeout=5)
				self.updateList()
			except:
				self.session.open(MessageBox, _("Error in ioctl '%s'!") % dev_path, MessageBox.TYPE_ERROR, timeout=5)

	def SetupMounts(self):
		self.session.openWithCallback(self.updateList, DeviceMountPanelConf)

	def Mount(self):
		if len(self['list'].list) < 1:
			return
		sel = self['list'].getCurrent()
		if sel:
			des = sel[1]
			des = des.replace('\n', '\t')
			parts = des.strip().split('\t')
			mountp = parts[1].replace(_("Mount: "), '')
			device = parts[2].replace(_("Device: "), '')
			moremount = sel[3]
			adv_title = moremount != "" and _("Warning, this device is used for more than one mount point!\n") or ""
			if device != '':
				devicemount = device[-5:]
				curdir = '/media%s' % (devicemount)
				mountlist = [
				(_("Mount current device from the fstab"), self.MountCur3),
				(_("Mount current device to %s") % (curdir), self.MountCur2),
				(_("Mount all device from the fstab"), self.MountCur1),
				]
				self.session.openWithCallback(
				self.menuCallback,
				ChoiceBox,
				list=mountlist,
				title=adv_title + _("Select mount action for %s:") % device,
				)

	def menuCallback(self, ret=None):
		ret and ret[1]()

	def MountCur3(self):
		sel = self['list'].getCurrent()
		if sel:
			parts = sel[1].split()
			self.device = parts[5]
			self.mountp = parts[3]
			des = sel[1]
			des = des.replace('\n', '\t')
			parts = des.strip().split('\t')
			device = parts[2].replace(_("Device: "), '')
			try:
				f = open('/proc/mounts', 'r')
			except IOError:
				return
			for line in f.readlines():
				if line.find(device) != -1 and '/omb' not in line:
					self.session.open(MessageBox, _("The device is already mounted!"), MessageBox.TYPE_INFO, timeout=5)
					f.close()
					return
			f.close()
			self.mbox = self.session.open(MessageBox, _("Please wait..."), MessageBox.TYPE_INFO)
			system('mount ' + device)
			self.Console = Console()
			self.Console.ePopen("/sbin/blkid | grep " + self.device, self.cur_in_fstab, [self.device, self.mountp])

	def MountCur1(self):
		if len(self['list'].list) < 1:
			return
		system('mount -a')
		self.updateList()

	def MountCur2(self):
		sel = self['list'].getCurrent()
		if sel:
			des = sel[1]
			des = des.replace('\n', '\t')
			parts = des.strip().split('\t')
			device = parts[2].replace(_("Device: "), '')
			try:
				f = open('/proc/mounts', 'r')
			except IOError:
				return
			for line in f.readlines():
				if line.find(device) != -1 and '/omb' not in line:
					f.close()
					self.session.open(MessageBox, _("The device is already mounted!"), MessageBox.TYPE_INFO, timeout=5)
					return
			f.close()
			if device != '':
				devicemount = device[-5:]
				mountdir = '/media/%s' % (devicemount)
				if not os.path.exists(mountdir):
					os.mkdir(mountdir, 0o755)
				system('mount ' + device + ' /media/%s' % (devicemount))
				mountok = False
				f = open('/proc/mounts', 'r')
				for line in f.readlines():
					if line.find(device) != -1 and '/omb' not in line:
						mountok = True
				f.close()
				if not mountok:
					self.session.open(MessageBox, _("Mount failed!"), MessageBox.TYPE_ERROR, timeout=5)
				self.updateList()

	def cur_in_fstab(self, result=None, retval=None, extra_args=None):
		self.device = extra_args[0]
		self.mountp = extra_args[1]
		if len(result) == 0 or " UUID=" not in result:
			print("[MountManager] error get UUID for device %s" % self.device)
			return
		self.device_tmp = result.split(' ')
		if str(self.device_tmp) != "['']":
			try:
				if self.device_tmp[0].startswith('UUID='):
					self.device_uuid = self.device_tmp[0].replace('"', "")
					self.device_uuid = self.device_uuid.replace('\n', "")
				elif self.device_tmp[1].startswith('UUID='):
					self.device_uuid = self.device_tmp[1].replace('"', "")
					self.device_uuid = self.device_uuid.replace('\n', "")
				elif self.device_tmp[2].startswith('UUID='):
					self.device_uuid = self.device_tmp[2].replace('"', "")
					self.device_uuid = self.device_uuid.replace('\n', "")
				elif self.device_tmp[3].startswith('UUID='):
					self.device_uuid = self.device_tmp[3].replace('"', "")
					self.device_uuid = self.device_uuid.replace('\n', "")
				system('mount ' + self.device_uuid)
				mountok = False
				f = open('/proc/mounts', 'r')
				for line in f.readlines():
					if line.find(self.device) != -1 and '/omb' not in line:
						mountok = True
				f.close()
				if not mountok:
					self.session.open(MessageBox, _("Mount current device failed!\nMaybe this device is not spelled out in the fstab?"), MessageBox.TYPE_ERROR, timeout=8)
			except:
				pass
		if self.mbox:
			self.mbox.close()
		self.updateList()

	def Unmount(self):
		if len(self['list'].list) < 1:
			return
		sel = self['list'].getCurrent()
		if sel:
			des = sel[1]
			des = des.replace('\n', '\t')
			parts = des.strip().split('\t')
			mountp = parts[1].replace(_("Mount: "), '')
			device = parts[2].replace(_("Device: "), '')
			print(mountp)
			if mountp == _("None"):
				return
			message = _('Really unmount ') + device + _(" from ") + mountp + " ?"
			self.session.openWithCallback(self.UnmountAnswer, MessageBox, message, MessageBox.TYPE_YESNO)

	def UnmountAnswer(self, answer):
		if answer:
			sel = self['list'].getCurrent()
			if sel:
				des = sel[1]
				des = des.replace('\n', '\t')
				parts = des.strip().split('\t')
				mountp = parts[1].replace(_("Mount: "), '')
				device = parts[2].replace(_("Device: "), '')
				moremount = sel[3]
				if mountp != _("None"):
					system('umount ' + mountp)
				if moremount == "":
					system('umount ' + device)
				try:
					mounts = open("/proc/mounts")
				except IOError:
					return
				mountcheck = mounts.readlines()
				mounts.close()
				for line in mountcheck:
					#if moremount == "":
					#	parts = line.strip().split(" ")
					#	if os.path.realpath(parts[0]).startswith(device):
					#		os.self.session.open(MessageBox, _("Can't unmount partiton, make sure it is not being used for swap or record/timeshift paths!"), MessageBox.TYPE_ERROR, timeout = 6, close_on_any_key = True)
					if mountp in line and device in line and '/omb' not in line:
						parts = line.strip().split(" ")
						if parts[1] == mountp:
							self.session.open(MessageBox, _("Can't unmount partiton, make sure it is not being used for swap or record/timeshift paths!"), MessageBox.TYPE_ERROR, timeout=5, close_on_any_key=True)
							break
				self.updateList()

	def saveMypoints(self):
		if len(self['list'].list) < 1:
			return
		sel = self['list'].getCurrent()
		if sel:
			des = sel[1]
			des = des.replace('\n', '\t')
			parts = des.strip().split('\t')
			device = parts[2].replace(_("Device: "), '')
			moremount = sel[3]
			adv_title = moremount != "" and _("Warning, this device is used for more than one mount point!\n") or ""
			message = adv_title + _("Really use and mount %s as HDD ?") % device
			self.session.openWithCallback(self.saveMypointAnswer, MessageBox, message, MessageBox.TYPE_YESNO)

	def saveMypointAnswer(self, answer):
		if answer:
			sel = self['list'].getCurrent()
			if sel:
				des = sel[1]
				des = des.replace('\n', '\t')
				parts = des.strip().split('\t')
				self.mountp = parts[1].replace(_("Mount: "), '')
				self.device = parts[2].replace(_("Device: "), '')
				if self.mountp.find('/media/hdd') < 0:
					pass
				else:
					self.session.open(MessageBox, _("This Device is already mounted as HDD."), MessageBox.TYPE_INFO, timeout=6, close_on_any_key=True)
					return
				system('[ -e /media/hdd/swapfile ] && swapoff /media/hdd/swapfile')
				#system('[ -e /etc/init.d/transmissiond ] && /etc/init.d/transmissiond stop')
				system('umount /media/hdd')
				try:
					f = open('/proc/mounts', 'r')
				except IOError:
					return
				for line in f.readlines():
					if '/media/hdd' in line:
						f.close()
						self.session.open(MessageBox, _("Cannot unmount from the previous device from /media/hdd.\nA record in progress, timeshift or some external tools (like samba, nfsd,transmission and etc) may cause this problem.\nPlease stop this actions/applications and try again!"), MessageBox.TYPE_ERROR)
						return
					else:
						pass
				f.close()
				if self.mountp.find('/media/hdd') < 0:
					if self.mountp != _("None"):
						system('umount ' + self.mountp)
					system('umount ' + self.device)
					self.Console.ePopen("/sbin/blkid | grep " + self.device, self.add_fstab, [self.device, self.mountp])

	def add_fstab(self, result=None, retval=None, extra_args=None):
		self.device = extra_args[0]
		self.mountp = extra_args[1]
		if len(result) == 0 or " UUID=" not in result:
			print("[MountManager] error get UUID for device %s" % self.device)
			return
		self.device_tmp = result.split(' ')
		if str(self.device_tmp) != "['']":
			if self.device_tmp[0].startswith('UUID='):
				self.device_uuid = self.device_tmp[0].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			elif self.device_tmp[1].startswith('UUID='):
				self.device_uuid = self.device_tmp[1].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			elif self.device_tmp[2].startswith('UUID='):
				self.device_uuid = self.device_tmp[2].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			elif self.device_tmp[3].startswith('UUID='):
				self.device_uuid = self.device_tmp[3].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			if not os.path.exists('/media/hdd'):
				os.mkdir('/media/hdd', 0o755)
			flashexpander = None
			if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Flashexpander/plugin.pyo") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Flashexpander/plugin.pyc"):
				try:
					f = open("/etc/fstab", 'r')
					for line in f.readlines():
						if line.find('/usr') > -1 and line.startswith(self.device_uuid):
							flashexpander = line
					f.close()
				except:
					pass
			open('/etc/fstab.tmp', 'w').writelines([l for l in open('/etc/fstab').readlines() if '/media/hdd' not in l])
			os.rename('/etc/fstab.tmp', '/etc/fstab')
			open('/etc/fstab.tmp', 'w').writelines([l for l in open('/etc/fstab').readlines() if self.device not in l])
			os.rename('/etc/fstab.tmp', '/etc/fstab')
			open('/etc/fstab.tmp', 'w').writelines([l for l in open('/etc/fstab').readlines() if self.device_uuid not in l])
			os.rename('/etc/fstab.tmp', '/etc/fstab')
			out = open('/etc/fstab', 'a')
			line = self.device_uuid + '\t/media/hdd\tauto\tdefaults\t0  2\n'
			if flashexpander is not None:
				line += flashexpander
			out.write(line)
			out.close()
			self.Console.ePopen('mount /media/hdd', self.updateList)

	def restBo(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 2)
		else:
			self.updateList()


class DeviceMountPanelConf(Screen, ConfigListScreen):
	skin = """
	<screen position="center,center" size="730,330" title="Setup Mounts">
		<ePixmap pixmap="skin_default/buttons/red.png" position="15,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="165,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="315,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="490,0" size="140,40" alphatest="on" />
		<widget name="key_red" position="15,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
		<widget name="key_green" position="165,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_yellow" position="315,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
		<widget name="key_blue" position="490,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
		<widget name="config" position="0,60" size="730,215" scrollbarMode="showOnDemand"/>
		<widget name="Linconn" position="30,305" size="680,25" font="Regular;18" halign="center" valign="center" backgroundColor="#9f1313"/>
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.list = []
		Screen.setTitle(self, _("Setup Mounts"))
		self['key_green'] = Label(_("TRIM"))
		self['key_red'] = Label(_("Label for device"))
		self['key_yellow'] = Label(_("Edit fstab"))
		self['key_blue'] = Label(_("Install / Info"))
		self['Linconn'] = Label(_("Wait please while scanning your box devices..."))
		self['myactions'] = ActionMap(['WizardActions'], {'back': self.close, 'ok': self.saveMypoints}, -2)
		self['colorActions'] = ActionMap(['ColorActions'], {'green': self.TrimOptions, 'red': self.editLabel, 'yellow': self.editFstab, 'blue': self.systemInfo}, -2)
		ConfigListScreen.__init__(self, self.list)
		self.checkMount = False
		self.Checktimer = eTimer()
		self.Checktimer.callback.append(self.check_cur_Umount)
		self.label_device = ""
		self.updateList2()

	def updateList2(self):
		self.list = []
		list2 = []
		self.Console = Console()
		self.Console.ePopen("sfdisk -l /dev/sd? | grep swap | awk '{print $(NF-9)}' >/tmp/devices.tmp")
		sleep(0.5)
		try:
			f = open('/tmp/devices.tmp', 'r')
			swapdevices = f.read()
			f.close()
		except:
			swapdevices = ''
		if os.path.exists('/tmp/devices.tmp'):
			os.remove('/tmp/devices.tmp')
		swapdevices = swapdevices.replace('\n', '')
		swapdevices = swapdevices.split('/')
		f = open('/proc/partitions', 'r')
		for line in f.readlines():
			parts = line.strip().split()
			if not parts:
				continue
			device = parts[3]
			mmc = False
			if MODEL_NAME in ('Zgemma', 'sfx6008', 'sf8008', 'sf5008', 'sf8008m', 'et13000', 'et11000', 'et1x000', 'duo4k', 'duo4kse', 'uno4k', 'uno4kse', 'ultimo4k', 'solo4k', 'zero4k', 'hd51', 'hd52', 'dm820', 'dm7080', 'sf4008', 'dm900', 'dm920', 'gbquad4k', 'gbue4k', 'lunix3-4k', 'lunix-4k', 'vs1500', 'h7', '8100s', 'e4hd', 'gbmv200', 'multibox', 'multiboxse', 'h9se', 'h11', 'h9combo', 'h9combose', 'h9twin', 'h9twinse', 'h10', 'v8plus', 'hd60', 'hd61', 'hd66se', 'pulse4k', 'pulse4kmini', 'dual') and search('mmcblk0p[1-9]', device):
				continue
			if MODEL_NAME in ('xc7439', 'osmio4k', 'osmio4kplus', 'osmini4k') and search('mmcblk1p[1-9]', device):
				continue
			if device and search('mmcblk[0-9]p[1-9]', device):
				mmc = True
			if not mmc and not search('sd[a-z][1-9]', device):
				continue
			if device in list2:
				continue
			if device in swapdevices:
				continue
			self.buildMy_rec(device)
			list2.append(device)
		f.close()
		self['config'].list = self.list
		self['config'].l.setList(self.list)
		self['Linconn'] = Label(_("Press OK...") + _("Save mount in fstab"))

	def buildMy_rec(self, device):
		global device2
		device2 = ''
		card = False
		try:
			if device.find('1') > 1:
				device2 = device.replace('1', '')
		except:
			device2 = ''
		try:
			if device.find('2') > 1:
				device2 = device.replace('2', '')
		except:
			device2 = ''
		try:
			if device.find('3') > 1:
				device2 = device.replace('3', '')
		except:
			device2 = ''
		try:
			if device.find('4') > 1:
				device2 = device.replace('4', '')
		except:
			device2 = ''
		try:
			if device.find('5') > 1:
				device2 = device.replace('5', '')
		except:
			device2 = ''
		try:
			if device.find('6') > 1:
				device2 = device.replace('6', '')
		except:
			device2 = ''
		try:
			if device.find('7') > 1:
				device2 = device.replace('7', '')
		except:
			device2 = ''
		try:
			if device.find('8') > 1:
				device2 = device.replace('8', '')
		except:
			device2 = ''
		try:
			if device.find('p1') > 1:
				device2 = device.replace('p1', '')
		except:
			device2 = ''
		try:
			if device.find('p2') > 1:
				device2 = device.replace('p2', '')
		except:
			device2 = ''
		try:
			if device.find('p3') > 1:
				device2 = device.replace('p3', '')
		except:
			device2 = ''
		try:
			if device.find('p4') > 1:
				device2 = device.replace('p4', '')
		except:
			device2 = ''
		try:
			if device.find('p5') > 1:
				device2 = device.replace('p5', '')
		except:
			device2 = ''
		try:
			if device.find('p6') > 1:
				device2 = device.replace('p6', '')
		except:
			device2 = ''
		try:
			if device.find('p7') > 1:
				device2 = device.replace('p7', '')
		except:
			device2 = ''
		try:
			if device.find('p8') > 1:
				device2 = device.replace('p8', '')
		except:
			device2 = ''
		try:
			devicetype = os.path.realpath('/sys/block/' + device2 + '/device')
		except:
			devicetype = ''
		d2 = device
		model = '-?-'
		name = "USB: "
		if 'sdhci' in devicetype or device2.startswith('mmcblk'):
			name = "MMC: "
			card = True
			try:
				model = open('/sys/block/' + device2 + '/device/name').read()
				model = str(model).replace('\n', '')
			except:
				pass
		else:
			try:
				model = open('/sys/block/' + device2 + '/device/model').read()
				model = str(model).replace('\n', '')
			except:
				pass
		des = ''
		try:
			if card:
				dev_name = 'mmcblk0'
			else:
				dev_name = device2
			data = open("/sys/block/%s/queue/rotational" % dev_name, "r").read().strip()
			rotational = int(data)
		except:
			rotational = True
		try:
			if card:
				dev_name = 'mmcblk0'
			else:
				dev_name = device2
			data = open("/sys/block/%s/removable" % dev_name, "r").read().strip()
			removable = int(data)
		except:
			removable = False
		if devicetype.find('/devices/pci') != -1 or devicetype.find('ahci') != -1 or devicetype.find('.sata/') != -1:
			name = _("HARD DISK: ")
			if not card and not removable and not rotational:
				name = "SSD: "
				mypixmap = '/usr/lib/enigma2/python/Plugins/SystemPlugins/MountManager/icons/dev_ssd.png'
		if name == "USB: " and not removable and rotational:
			mypixmap = '/usr/lib/enigma2/python/Plugins/SystemPlugins/MountManager/icons/dev_usb_drive.png'
		try:
			vendor = open('/sys/block/' + device2 + '/device/vendor').read()
		except:
			vendor = ""
		if vendor and model:
			name = name + vendor + " (" + model + ")"
		elif vendor:
			name = name + vendor
		elif model:
			name = name + model
		else:
			name = name +  "-?-"
		f = open('/proc/mounts', 'r')
		for line in f.readlines():
			if line.find(device) != -1 and '/omb' not in line:
				parts = line.strip().split()
				d1 = parts[1]
				dtype = parts[2]
				break
				continue
			else:
				d1 = _("None")
				dtype = _("unavailable")
		f.close()
		f = open('/proc/partitions', 'r')
		for line in f.readlines():
			if line.find(device) != -1:
				parts = line.strip().split()
				size = int(parts[2])
				if (((float(size) / 1024) / 1024) / 1024) > 1:
					des = "%s%s%s" % (_("Size: "), str(round((((float(size) / 1024) / 1024) / 1024), 2)), _("TB"))
				elif ((size / 1024) / 1024) > 1:
					des = "%s%s%s" % (_("Size: "), str(round(((float(size) / 1024) / 1024), 2)), _("GB"))
				else:
					des = "%s%s%s" % (_("Size: "), str(round((float(size) / 1024), 2)), _("MB"))
			else:
				try:
					size = open('/sys/block/' + device2 + '/' + device + '/size').read()
					size = str(size).replace('\n', '')
					size = int(size)
				except:
					size = 0
				if ((((float(size) / 2) / 1024) / 1024) / 1024) > 1:
					des = "%s%s%s" % (_("Size: "), str(round(((((float(size) / 2) / 1024) / 1024) / 1024), 2)), _("TB"))
				elif (((size / 2) / 1024) / 1024) > 1:
					des = "%s%s%s" % (_("Size: "), str(round((((float(size) / 2) / 1024) / 1024), 2)), _("GB"))
				else:
					des = "%s%s%s" % (_("Size: "), str(round(((float(size) / 2) / 1024), 2)), _("MB"))
		f.close()
		choices = [('/media/' + device, '/media/' + device), ('/media/hdd', '/media/hdd'), ('/media/hdd2', '/media/hdd2'), ('/media/hdd3', '/media/hdd3'), ('/media/usb_hdd', '/media/usb_hdd'), ('/media/usb', '/media/usb'), ('/media/usb2', '/media/usb2'), ('/media/usb3', '/media/usb3')]
		if 'MMC' in name:
			choices.append(('/media/mmc', '/media/mmc'))
			choices.append(('/media/mmc1', '/media/mmc1'))
			choices.append(('/media/mmc2', '/media/mmc2'))
		if not fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Flashexpander/plugin.pyo") or not fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Flashexpander/plugin.pyc"):
			if (removable and rotational) or (not removable and not rotational and card):
				choices.append(('/usr', '/usr'))
		item = NoSave(ConfigSelection(default='/media/' + device, choices=choices))
		if dtype == 'Linux':
			dtype = 'ext3'
		else:
			dtype = 'auto'
		item.value = d1.strip()
		text = name + ' ' + des + ' /dev/' + device
		ssd = 'SSD:' in name
		res = getConfigListEntry(text, item, device, dtype, ssd)
		if des != '' and self.list.append(res):
			pass

	def TrimOptions(self):
		self.label_device = ""
		if not os.path.exists('/sbin/tune2fs'):
			self.session.open(MessageBox, _("Please install tune2fs"), MessageBox.TYPE_INFO)
			return
		sel = self['config'].getCurrent()
		if sel and len(sel) > 3 and sel[4]:
			des = sel[2]
			if des and des != "":
				des = des.replace('\n', '\t')
				device = '/dev/' + des
				if os.path.exists(device):
					self.label_device = device
			mylist = [
			(_("Set discard mount option"), self.trimaction1),
			(_("Unset discard mount option"), self.trimaction2),
			(_("Show discard status"), self.trimaction3),
			]
			self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list=mylist,
			title=_("TRIM (if supported) working only for SSD device.\nRequires filesystem ext4 and flag discard."),
			)

	def trimaction1(self):
		from Screens.Console import Console as myConsole
		cmd = "/sbin/tune2fs -o discard %s && /sbin/tune2fs -l %s | grep 'Default mount options'" % (self.label_device, self.label_device)
		self.session.open(myConsole, _("Set discard mount option"), [cmd])

	def trimaction2(self):
		from Screens.Console import Console as myConsole
		cmd = "/sbin/tune2fs -o^discard %s && /sbin/tune2fs -l %s | grep 'Default mount options'" % (self.label_device, self.label_device)
		self.session.open(myConsole, _("Unset discard mount option"), [cmd])

	def trimaction3(self):
		from Screens.Console import Console as myConsole
		cmd = "/sbin/tune2fs -l %s | grep 'Default mount options'" % self.label_device
		self.session.open(myConsole, _("Show discard status"), [cmd])

	def editFstab(self):
		self.session.open(fstabViewer.fstabViewerScreen)

	def editLabel(self):
		self.label_device = ""
		sel = self['config'].getCurrent()
		if sel and len(sel) > 2:
			des = sel[2]
			if des and des != "":
				des = des.replace('\n', '\t')
				device = '/dev/' + des
				if os.path.exists(device):
					self.label_device = device
					if os.path.exists('/sbin/tune2fs'):
						self.openEditLabelDevice(device)
					else:
						self.session.open(MessageBox, _("Please install tune2fs"), MessageBox.TYPE_INFO)

	def openEditLabelDevice(self, device=''):
		if device:
			title_text = _("Please enter label for %s:") % device
			self.session.openWithCallback(self.renameEntryCallback, VirtualKeyBoard, title=title_text, text='')

	def renameEntryCallback(self, answer):
		if answer is not None:
			edit_fstab = False
			if answer != "":
				edit_fstab = True
			ret = system("/sbin/tune2fs %s -L '%s'" % (self.label_device, answer))
			if ret == 0:
				if edit_fstab:
					self.Console = Console()
					self.Console.ePopen("/sbin/blkid | grep " + self.label_device, self.delCurrentUUID, [self.label_device])
				message = _("Device changes need a system restart to take effects.\nRestart your Box now?")
				ybox = self.session.openWithCallback(self.restartBox, MessageBox, message, MessageBox.TYPE_YESNO)
				ybox.setTitle(_("Restart Box..."))
			else:
				self.label_device = ""
				self.close()

	def delCurrentUUID(self, result=None, retval=None, extra_args=None):
		self.device = extra_args[0]
		if result and self.device in result:
			pass
		else:
			return
		self.device_tmp = result.split(' ')
		if str(self.device_tmp) != "['']":
			if self.device_tmp[0].startswith('UUID='):
				self.device_uuid = self.device_tmp[0].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			elif self.device_tmp[1].startswith('UUID='):
				self.device_uuid = self.device_tmp[1].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			elif self.device_tmp[2].startswith('UUID='):
				self.device_uuid = self.device_tmp[2].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			elif self.device_tmp[3].startswith('UUID='):
				self.device_uuid = self.device_tmp[3].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			flashexpander = None
			if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Flashexpander/plugin.pyo") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Flashexpander/plugin.pyc"):
				try:
					f = open("/etc/fstab", 'r')
					for line in f.readlines():
						if line.find('/usr') > -1 and line.startswith(self.device_uuid):
							flashexpander = line
					f.close()
				except:
					pass
			open('/etc/fstab.tmp', 'w').writelines([l for l in open('/etc/fstab').readlines() if self.device not in l])
			os.rename('/etc/fstab.tmp', '/etc/fstab')
			open('/etc/fstab.tmp', 'w').writelines([l for l in open('/etc/fstab').readlines() if self.device_uuid not in l])
			os.rename('/etc/fstab.tmp', '/etc/fstab')
			if flashexpander is not None:
				out = open('/etc/fstab', 'a')
				line = flashexpander
				out.write(line)
				out.close()

	def systemInfo(self):
		mylist = [
		(_("mount"), self.action1),
		(_("df -h"), self.action2),
		(_("sfdisk -l"), self.action3),
		(_("blkid"), self.action4),
		(_("eject DVD"), self.action11),
		(_("install ext2 kernel module"), self.action5),
		(_("install ext3 kernel module"), self.action6),
		(_("install filesystem utilities (e2fsprogs)"), self.action7),
		(_("install filesystem utilities (e2fsprogs-tune2fs)"), self.action8),
		(_("install linux utilities (fdisk)"), self.action9),
		(_("install linux utilities (util-linux-blkid)"), self.action10),
		(_("install linux utilities (hdparm)"), self.action13),
		(_("install filesystem utilities (fuse-exfat)"), self.action14),
		(_("install filesystem utilities (ntfs-3g)"), self.action15),
		(_("install linux utilities (smartmontools)"), self.action16),
		(_("install linux utilities (parted)"), self.action17),
		]
		if fileExists('/usr/share/usb.ids') or fileExists('/usr/share/usb.ids.gz'):
			mylist.append((_("update usb.ids (www.linux-usb.org)"), self.action12))
		if not self.spinDown() and fileExists('/etc/init.d/umountfs'):
			mylist.append((_("Spin down HDD before shutdown box"), self.action18))
		if not fileExists('/etc/rcS.d/S99hdparm120.sh'):
			mylist.append((_("Add standby HDD via 10 min. (hdparm)"), self.action19))
		else:
			mylist.append((_("Remove standby HDD via 10 min. (hdparm)"), self.action20))
		self.session.openWithCallback(self.menuCallback, ChoiceBox, list=mylist, title=_("Select system info or install module:"))

	def action1(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****mount*****"), ["mount"])

	def action2(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****df -h*****"), ["df -h"])

	def action3(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****sfdisk -l*****"), ["sfdisk -l"])

	def action4(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****blkid*****"), ["blkid"])

	def action5(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****kernel-module-ext2*****"), ["opkg install kernel-module-ext2"])

	def action6(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****kernel-module-ext3*****"), ["opkg install kernel-module-ext3"])

	def action7(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****e2fsprogs*****"), ["opkg install e2fsprogs"])

	def action8(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****e2fsprogs-tune2fs*****"), ["opkg install e2fsprogs-tune2fs"])

	def action9(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****fdisk*****"), ["opkg install util-linux-fdisk"])

	def action10(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****util-linux-blkid*****"), ["opkg install util-linux-blkid"])

	def action11(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****eject DVD*****"), ["eject /dev/sr0"])

	def action12(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****usb.ids*****"), ["chmod 755 %s && %s" % (update_usb_ids, update_usb_ids)])

	def action13(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****hdparm*****"), ["opkg install hdparm"])

	def action14(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****fuse-exfat*****"), ["opkg install fuse-exfat && chmod 755 %s && %s" % (make_exfat, make_exfat)])

	def action15(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****ntfs-3g*****"), ["opkg install ntfs-3g"])

	def action16(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****smartmontools*****"), ["opkg install smartmontools"])

	def action17(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****parted*****"), ["opkg install parted"])

	def action18(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("*****Spin down HDD*****"), ["cp %s /etc/init.d/umountfs && chmod 755 /etc/init.d/umountfs && cat /etc/init.d/umountfs" % umountfs])

	def action19(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("Add standby HDD via 10 min. (hdparm)"), ["cp %s /etc/rcS.d/S99hdparm120.sh && chmod 755 /etc/rcS.d/S99hdparm120.sh && cat /etc/rcS.d/S99hdparm120.sh" % S99hdparm120])

	def action20(self):
		from Screens.Console import Console as myConsole
		self.session.open(myConsole, _("Remove standby HDD via 10 min. (hdparm)"), ["rm -rf /etc/rcS.d/S99hdparm120.sh && echo 'Done...\nNeed reboot box!'"])

	def spinDown(self):
		try:
			f = open('/etc/init.d/umountfs').readlines()
			for line in f:
				if _('sdparm') in line:
					return True
		except:
			pass
		return False

	def saveMypoints(self):
		if len(self['config'].list) < 1:
			return
		message = _("Really save in fstab mount by UUID:\n")
		val = []
		for x in self['config'].list:
			device = x[2]
			mountp = x[1].value
			if mountp not in val:
				val.append((mountp))
			else:
				self.session.open(MessageBox, _("Error!\nThe same mount point!"), MessageBox.TYPE_ERROR, timeout=5)
				return
			message += '/dev/' + device + _(" as ") + mountp + "\n"
		self.session.openWithCallback(self.saveMypointsAnswer, MessageBox, message, MessageBox.TYPE_YESNO)

	def saveMypointsAnswer(self, answer):
		if answer:
			self.Console = Console()
			system('[ -e /media/hdd/swapfile ] && swapoff /media/hdd/swapfile')
			#system('[ -e /etc/init.d/transmissiond ] && /etc/init.d/transmissiond stop')
			system('[ -e /media/usb/swapfile ] && swapoff /media/usb/swapfile')
			for x in self['config'].list:
				self.device = x[2]
				self.mountp = x[1].value
				self.type = x[3]
				self.Console.ePopen('umount -f /dev/%s 2>&1' % (self.device))
				self.Console.ePopen("/sbin/blkid | grep " + self.device, self.add_fstab, [self.device, self.mountp])
				self.Checktimer.stop()
				self.Checktimer.start(2500, True)

	def check_cur_Umount(self):
		self.checkMount = False
		file_mounts = '/proc/mounts'
		if fileExists(file_mounts):
			fd = open(file_mounts, 'r')
			lines_mount = fd.readlines()
			fd.close()
			for line in lines_mount:
				if '/omb' not in line:
					l = line.split(' ')
					if l[0][:7] == '/dev/sd' or l[0][:7].startswith('mmcblk'):
						self.checkMount = True
		self.select_action()

	def select_action(self):
		if self.checkMount:
			self.checkMount = False
			message = _("Devices changes need a system restart to take effects.\nRestart your Box now?")
			ybox = self.session.openWithCallback(self.restartBox, MessageBox, message, MessageBox.TYPE_YESNO)
			ybox.setTitle(_("Restart Box..."))
		else:
			mylist = [
			(_("Mount all device from the fstab"), self.AllMount),
			(_("Restart your box"), self.answerRestart),
			(_("Exit"), self.answerExit),
			]
			self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list=mylist,
			title=_("All device umount.Select action:"),
			)

	def answerRestart(self):
		self.restartBox(True)

	def answerExit(self):
		self.close()

	def menuCallback(self, ret=None):
		ret and ret[1]()

	def AllMount(self):
		system('mount -a')
		self.close()

	def add_fstab(self, result=None, retval=None, extra_args=None):
		self.device = extra_args[0]
		self.mountp = extra_args[1]
		if len(result) == 0 or " UUID=" not in result:
			print("[MountManager] error get UUID for device %s" % self.device)
			return
		self.device_tmp = result.split(' ')
		if str(self.device_tmp) != "['']":
			if self.device_tmp[0].startswith('UUID='):
				self.device_uuid = self.device_tmp[0].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			elif self.device_tmp[1].startswith('UUID='):
				self.device_uuid = self.device_tmp[1].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			elif self.device_tmp[2].startswith('UUID='):
				self.device_uuid = self.device_tmp[2].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			elif self.device_tmp[3].startswith('UUID='):
				self.device_uuid = self.device_tmp[3].replace('"', "")
				self.device_uuid = self.device_uuid.replace('\n', "")
			try:
				if self.device_tmp[0].startswith('TYPE='):
					self.device_type = self.device_tmp[0].replace('TYPE=', "")
					self.device_type = self.device_type.replace('"', "")
					self.device_type = self.device_type.replace('\n', "")
				elif self.device_tmp[1].startswith('TYPE='):
					self.device_type = self.device_tmp[1].replace('TYPE=', "")
					self.device_type = self.device_type.replace('"', "")
					self.device_type = self.device_type.replace('\n', "")
				elif self.device_tmp[2].startswith('TYPE='):
					self.device_type = self.device_tmp[2].replace('TYPE=', "")
					self.device_type = self.device_type.replace('"', "")
					self.device_type = self.device_type.replace('\n', "")
				elif self.device_tmp[3].startswith('TYPE='):
					self.device_type = self.device_tmp[3].replace('TYPE=', "")
					self.device_type = self.device_type.replace('"', "")
					self.device_type = self.device_type.replace('\n', "")
				elif self.device_tmp[4].startswith('TYPE='):
					self.device_type = self.device_tmp[4].replace('TYPE=', "")
					self.device_type = self.device_type.replace('"', "")
					self.device_type = self.device_type.replace('\n', "")
			except:
				self.device_type = 'auto'

			if self.device_type.startswith('ext'):
				self.device_type = 'auto'

			if not os.path.exists(self.mountp):
				os.mkdir(self.mountp, 0o755)
			flashexpander = None
			if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Flashexpander/plugin.pyo") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Flashexpander/plugin.pyc"):
				try:
					f = open("/etc/fstab", 'r')
					for line in f.readlines():
						if line.find('/usr') > -1 and line.startswith(self.device_uuid):
							flashexpander = line
					f.close()
				except:
					pass
			open('/etc/fstab.tmp', 'w').writelines([l for l in open('/etc/fstab').readlines() if self.mountp not in l])
			os.rename('/etc/fstab.tmp', '/etc/fstab')
			open('/etc/fstab.tmp', 'w').writelines([l for l in open('/etc/fstab').readlines() if self.device not in l])
			os.rename('/etc/fstab.tmp', '/etc/fstab')
			open('/etc/fstab.tmp', 'w').writelines([l for l in open('/etc/fstab').readlines() if self.device_uuid not in l])
			os.rename('/etc/fstab.tmp', '/etc/fstab')
			out = open('/etc/fstab', 'a')
			line = self.device_uuid + '\t' + self.mountp + '\t' + self.device_type + '\tdefaults\t0 2\n'
			if flashexpander is not None:
				line += flashexpander
			out.write(line)
			out.close()

	def restartBox(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 2)
		else:
			self.close()


class DevicesMountPanelSummary(SetupSummary):
	def __init__(self, session, parent):
		SetupSummary.__init__(self, session, parent=parent)
		self.skinName = ["DevicesMountPanelSummary", "SetupSummary"]

	def addWatcher(self):
		self.parent.onChangedEntry.append(self.selectionChanged)
		self.parent.selectionChanged()

	def removeWatcher(self):
		self.parent.onChangedEntry.remove(self.selectionChanged)

	def selectionChanged(self, name, desc):
		self["SetupEntry"].text = name
		self["SetupValue"].text = desc


def StartSetup(menuid, **kwargs):
	if menuid == "system":
		return [(_("Mount Manager"), OpenSetup, "mountpoints_setup", None)]
	else:
		return []


def OpenSetup(session, **kwargs):
	session.open(DevicesMountPanel)


def Plugins(**kwargs):
	return [PluginDescriptor(name="Mount Manager", description=_("Manage you devices mountpoints"), where=PluginDescriptor.WHERE_MENU, fnc=StartSetup)]
