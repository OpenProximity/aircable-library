"""
    Base class for both sppClient and sppServer, rfcomm clients/servers
    wrappers.

    Copyright 2008 Wireless Cables Inc. <www.aircable.net>
    Copyright 2008 Naranjo, Manuel Francisco <manuel@aircable.net>

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import socket, time

import dbus

from re import compile
from errors import *
from select import select

try:
    from net.aircable.utils import getLogger
    logger = getLogger(__name__)
except:
    import logging
    logger = logging.getLogger('sppAIRcable')

    console = logging.StreamHandler()
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)
    logger.setLevel(logging.DEBUG)


class sppBase:
	'''
	    Base class for rfcomm wrappers regardless of it\'s master or slave
	    behaviour.
	'''
        socket  = None;
        channel = None;
	service = None;
	device  = None;
	
	bus 	  = dbus.SystemBus();
	__pattern = compile(r'.*\n');
	
	new_bluez_api = True;
	
	def getDefaultDeviceAddress(self):
	    obj     = self.bus.get_object( 'org.bluez', '/' )
	    manager = dbus.Interface( obj, 'org.bluez.Manager' )
	    obj     = self.bus.get_object( 'org.bluez', 
						    manager.DefaultAdapter() )
	    adapter = dbus.Interface( obj, 'org.bluez.Adapter' )
	    address = adapter.GetProperties()['Address']
	    return address
	    
	def getAdapterObjectPath(self):
            bluez_path   = self.bus.get_object( 'org.bluez', '/' )
            manager = dbus.Interface( bluez_path, 'org.bluez.Manager' )

            return self.bus.get_object( 'org.bluez',
                            manager.FindAdapter(self.device)
                        )

	def __init__(self, socket):
	    '''
		    You use this constructor when you all ready have a socket
	        
		arguments:
		    socket descriptor
	    '''
	    self.__socket = socket;

	def __init__( self,
			channel = -1, 
			service = 'spp',
			device  = None  ):
	    '''
		More general constructor. You will use this one when you want
		sppClient to make the conneciton.
	    
		arguments:
		    channel: Channel to be used for establishing the connection.
		    service: Service to use when you want sppClient to do service
			     Discovery.
		    device:  Bluetooth Address of the local device you want to 
			     use for making the connection, None for default.
	    '''

	    self.channel = int(channel);
	    self.service = service;
	    
	    if not device:
		device = self.getDefaultDeviceAddress()
	    
	    self.device  = device;
	    
	    self.iface = dbus.Interface( 
		    self.getAdapterObjectPath(),
		    'org.bluez.Adapter')
            
	    logger.info("sppBase.__init__");
	    logger.info("Channel: %s" % channel );
	    logger.info("Service: %s" % service );
	    logger.info("Device: %s"  % device  );

	def checkConnected(self, message =''):
		if self.socket == None:
		    raise SPPNotConnectedException, message
		    
	def disconnect(self, force=False):
	    if not force:
		self.checkConnected("Can't close if it's opened");
	    logger.info("Closing socket");
	    self.socket.shutdown(socket.SHUT_RDWR);
	    self.socket.close()
	    self.socket = None

	def send(self, text):
	    '''
		Send something to the port.
	    
		Arguments: what to send
	    '''
	    self.checkConnected('Can\'t send if not connected');
	    
	    logger.debug(">> %s" % text)
		
	    ret = self.socket.sendall(text, socket.MSG_WAITALL);
	    
	    if ret and int(ret) != text.length():
		raise SPPException, "Failed to send all data"
	
	def sendLine(self, text):
	    """
		Send a line instead of only text, this will add \n
	    """
	    self.send("%s\n\r" % text)

	def read(self, bytes=10, log=True, timeout=None):
	    '''
		Read binary data from the port.
	    
		Arguments:
		    bytes: Amount of bytes to read
	    '''
	    self.checkConnected('Can\'t read if not connected');
	    
	    ret = None
	    
	    if timeout is None:
		timeout = self.socket.gettimeout()
	    
	    if timeout is not None:
		start = time.time()
	    
	    while [ 1 ]:
		sel = select( (self.socket,), (), (), 0)
		if len(sel[0]) > 0:
		    ret = self.socket.recv(bytes);
		    break
		if timeout is not None and time.time() - start > timeout:
		    raise SPPException("timeout reached on read")
		time.sleep(0.1)
	    
	    if( log ):
		logger.debug("<< %s" % ret)
	    
	    return ret

	def readLine(self):
	    '''
		Reads until \n is detected
	    '''
	    out = buffer("");
		
	    while ( 1 ):
		out += self.read(bytes=1, log=False);

		if self.__pattern.match(out):
			out = out.replace('\n', '');
			logger.debug("<< %s" % out )
			return out
	
	def readBuffer(self, honnor_eol=False,timeout=1, log=False):
	    '''
		Reads all the data inside the buffer
	    '''
	    out = buffer("");
#	    timeout__ = self.socket.gettimeout()
#	    self.socket.settimeout(timeout)
	    start = time.time()
	    try:
		while ( 1 ):
		    out += self.read(bytes=1, log=False, timeout=timeout)
		    if honnor_eol and self.__pattern.match(out):
			break;
		    if time.time() - start > timeout:
			break;
	    except SPPException, err:
		if log:
		    logger.exception(err)
	    
	    
	    return str(out).replace('\n', '')
#	    self.socket.settimeout(timeout__)
#	    return 
			
	#shell functions wrappers
	def shellGrabFile(self, file):
		out = "";
		self.sendLine("s%s" % file)
		
		while [ 1 ]:
			try:
				line = self.readLine()
			except socket.error:
				logger.info("Connection lost connection")
				break;

			logger.debug("line=%s" % line)
		
			if (line != None and line.find("DONE") >- 1):
				logger.debug("EOF")
				break;
			elif line.startswith(">") or len(line)>1 or line.find("GO")==-1:
				out += line
				out += "\n"
			#self.sendLine("GO")
		
		out=out.replace('>','')
		logger.debug("Got:\n%s" % out);
		return out
    
	def shellAskLine(self, number):
		'''Function wrapper for a shell operation'''
		logger.debug('shellAskLine %s' % number)
		#self.makeShellReady()
		self.sendLine("p%04i" % number)
		while [ 1 ]:
			line = self.readLine()
			if line.find("error")==-1:
				return line.replace('>', '').strip()
			else:
			    return ""

	def shellSetLine(self, number, content):
		'''Function wrapper for a shell operation'''
		self.__sendCommand("S%04i%s" % (number, content))
    
	def __sendCommand(self, command):
		logger.debug('__sendCommand %s' % command)
		#self.makeShellReady()
		self.sendLine(command)
		while [ 1 ]:
			line=self.readLine()
			if line.find('error')==-1:
				return line
    
	def shellExit(self):
		'''Function wrapper for a shell operation'''
		self.__sendCommand('e')

	def shellUpdate(self):
		'''Function wrapper for a shell operation'''
		self.__sendCommand('u')
    
	def shellPushIntoHistory(self, argument):
		'''Function wrapper for a shell operation'''
		self.__sendCommand("c%s" % argument)
	
	def shellDeleteFile(self, file):
		self.__sendCommand("d%s" % file)

	# stupid function that will try to sync both shells
	def makeShellReady(self):
		logger.debug("MakeShellReady()")
		line=""
		timeout=self.socket.gettimeout()
		self.socket.settimeout(1)

		while [ 1 ]:
			logger.debug('reading')
			try:
				line += self.read(200)
			except socket.error: # wait until socket timesout
				logger.debug('Shell cleaned')
				self.socket.settimeout(timeout)
				return line
				
	def endConnection(self, exit=True):
		self.shellPushIntoHistory(time.time())
		
		time.sleep(2)
		if exit:
			logger.info("Sending exit")
			self.shellExit()

