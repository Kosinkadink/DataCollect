import time,os,threading,platform,socket,select,sys
from datetime import datetime
from time import sleep
try:
	import serial
except:
	print("The serial module is required")
	raw_input("")
	quit()

version = 0.1
cliversion = '2.0test003'
ser = []
serList = []
serTrackFile = []
serTrackOnline = []
serTrackOnlineIndiv = []
serPrint = []
ardCount = 0

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) #directory from which this script is ran
if os.name == 'nt':
	__location__ = __location__.replace('\\','/')
saveLoc = os.path.join(__location__,'resources/temp_data')
scriptLoc = os.path.dirname(__file__)
if not os.path.exists(saveLoc): os.makedirs(saveLoc)

saveServ = "jedkos.com:9050"
serverBuffer = []
isOnline = False

def initialize():
	if not os.path.exists(__location__+'resources/networkpass'): 
		os.makedirs(__location__+'resources/networkpass') #contains network passwords

def boot():
	global version
	print("====================================")
	print("Arduino Temp Measure v%s" % version)
	print("by Jedrzej Kosinski")

def turnOff():
	print("====================================")

def helpMAIN():
	print("\n==Main Menu==")
	print("Main Menu Commands:")
	print("add + (number) + [opt name]: try to connect to serial on that port")
	print("autoadd + [opt name]: try to connect to the first available serial")
	print("view: display names of connected devices")
	print("available: display port numbers of available devices")
	print("rm + (name): try to remove connected device")
	print("(name or ALL) + (COMMAND): performs command on specified device")
	print("   COMMAND:")
	print("      file + (t/f): save input to file")
	print("      group + (t/f): save input to server as group")
	print("      indiv + (t/f): save input to server as individual")
	print("      print + (t/f): print input")
	print("online: returns if connected to group server")
	print("newserver + (server ip): change current saved server")
	print("connect + (server ip or 'server') + (chosen client name): join group data taking server")
	print("groupstart + (server ip or 'server') + (chosen group name): begin group data collection")
	print("disconnect: leave group data taking server")
	print("exit: close program")
	print("")

def temp_measure_main():
	global ser
	global serList
	global serTrackFile
	global serTrackOnline
	global serTrackOnlineIndiv
	global serPrint
	global ardCount
	global isOnline
	global saveServ
	initialize()
	boot()
	helpMAIN()

	commands_list = ['add',
					'autoadd',
					'view',
					'available', 'avail',
					'rm','remove',
					'newserver',
					'online',
					'connect','con',
					'disconnect','discon',
					'groupstart',
					'groupstop']

	while True:
		user_inp = raw_input("> ")
		user_inp = user_inp.split()

		if len(user_inp) == 0:
			print("Unknown command")
			continue

		if user_inp[0].lower() == 'add': ###########
			try:
				portN = user_inp[1]
				int(portN)
			except IndexError:
				print("Error: No port specified")
				continue
			except ValueError:
				print("Error: Port must be an integer")
				continue

			useDefName = False

			try:
				ardName = user_inp[2]
			except IndexError:
				useDefName = True
				ardName = 'ard%s' % str(ardCount)

			if ardName in serList:
				print("Error: Name already exists")
				continue

			if ardName in commands_list:
				print("Error: Name is already assigned to a command")
				continue


			success,connSer = connectToSerial(portN)
			if not success:
				print("Error: Could not connect to port")
				continue

			ser += [connSer]
			serList += [ardName]
			serTrackFile += [False]
			serTrackOnline += [False]
			serTrackOnlineIndiv += [False]
			serPrint += [False]
			if useDefName: ardCount += 1

			try:
				arduinoprocess = threading.Thread(target=arduinoThread,args=(connSer,ardName))
				arduinoprocess.daemon = True
				arduinoprocess.start()
			except:
				print("Error: issue starting arduino thread")
				continue

			print('Connected to %s on port %s' % (ardName,portN))
		
		elif user_inp[0].lower() == 'autoadd': ###########
			success,conSer,portN = try_serials()
			if not success:
				print('Error: No devices found')
				continue

			useDefName = False

			try:
				ardName = user_inp[1]
			except IndexError:
				useDefName = True
				ardName = 'ard%s' % str(ardCount)

			if ardName in serList:
				print("Error: Name already exists")
				continue

			if ardName in commands_list:
				print("Error: Name is already assigned to a command")
				continue

			ser += [conSer]
			serList += [ardName]
			serTrackFile += [False]
			serTrackOnline += [False]
			serTrackOnlineIndiv += [False]
			serPrint += [False]
			if useDefName: ardCount += 1

			try:
				arduinoprocess = threading.Thread(target=arduinoThread,args=(conSer,ardName))
				arduinoprocess.daemon = True
				arduinoprocess.start()
			except:
				print("Error: issue starting arduino thread")
				continue

			print('Found device; connected to %s on port %s' % (ardName,portN))
		
		elif user_inp[0].lower() == 'view': ###########
			print(str(serList))

		elif user_inp[0].lower() in ['available','avail']: ###########
			avPorts = availableDevices()
			avString = ''
			for av in avPorts:
				avString += av
				avString += ','
			if avString.endswith(','):
				avString = avString[:-1]

			if len(avString) == 0:
				print("No devices are available for connection")
			else:
				print("Devices available: %s" % avString)


		elif user_inp[0].lower() in ['rm','remove']: ############
			try:
				remArd = user_inp[1]
			except IndexError:
				print("Error: No device provided")
				continue
			try:
				nameIndex = serList.index(remArd)
			except ValueError:
				print("Error: No device found with name %s" % remArd)
				continue
			ser[nameIndex].close()
			del ser[nameIndex]
			del serList[nameIndex]
			del serTrackFile[nameIndex]
			del serTrackOnline[nameIndex]
			del serTrackOnlineIndiv[nameIndex]
			del serPrint[nameIndex]
			print("Device %s removed" % remArd)

		elif user_inp[0].lower() == 'newserver': ##############
			try:
				ip = user_inp[1]
			except IndexError:
				print("Error: No ip provided")
				continue
			try:
				address,port = ip.split(':')
			except IndexError:
				print("Error: Must provide address and port")
				continue
			saveServ = ip
			print("Server is now: %s" % ip)


		elif user_inp[0].lower() == 'online': #############
			if isOnline:
				print('Client is connected to a server')
			else:
				print("Client is NOT connected to a server")

		elif user_inp[0].lower() in ['connect','con']: ##############
			try:
				ip = user_inp[1]
			except IndexError:
				ip = saveServ

			if ip == 'server':
				ip = saveServ

			try:
				chosenName = user_inp[2]
			except IndexError:
				chosenName = '!!!NONE!!!'

			try:
				port = ip.split(':')[1]
				int(port)
			except IndexError:
				print('Error: No port provided')
				continue
			except ValueError:
				print('Error: Port must be an integer')
				continue

			success,connection = connectip(ip)
			if not success:
				continue

			command = 'tempgroup'

			connectprotocolclient(connection,chosenName,command)

		elif user_inp[0].lower() in ['disconnect','discon']: ############
			if isOnline:
				isOnline = False
				print('Leaving group server')
			else:
				print('No server to disconnect')

		elif user_inp[0].lower() == 'exit': ##############
			break

		elif user_inp[0].lower() == 'help': ##############
			helpMAIN()

		elif user_inp[0].lower() == 'all': ##################
			try:
				command = user_inp[1]
			except IndexError:
				print("Error: no command given")
				continue
			try:
				value = user_inp[2]
			except IndexError:
				value = None
			
			if len(serList) == 0:
				print("No devices connected")
				continue

			for ardName in serList:
				arduino_command_input(ardName,command,value)	

		elif user_inp[0] == 'groupstart': #############
			if not isOnline:
				print('Not currently connected to a server')
				continue

			try:
				ip = user_inp[1]
			except IndexError:
				ip = saveServ

			if ip == 'server':
				ip = saveServ

			try:
				port = ip.split(':')[1]
				int(port)
			except IndexError:
				print('Error: No port provided')
				continue
			except ValueError:
				print('Error: Port must be an integer')
				continue

			try:
				chosenGroupName = user_inp[2]
			except IndexError:
				chosenGroupName = '!!!NONE!!!'

			success,connection = connectip(ip)
			if not success:
				continue

			command = 'startdata'

			connectprotocolclient(connection,chosenGroupName,command)

		elif user_inp[0] == 'groupstop': #############

			if not isOnline:
				print('Not currently connected to a server')
				continue

			try:
				ip = user_inp[1]
			except IndexError:
				ip = saveServ

			if ip == 'server':
				ip = saveServ

			try:
				port = ip.split(':')[1]
				int(port)
			except IndexError:
				print('Error: No port provided')
				continue
			except ValueError:
				print('Error: Port must be an integer')
				continue

			success,connection = connectip(ip)
			if not success:
				continue

			command = 'stopdata'

			connectprotocolclient(connection,None,command)


		elif user_inp[0] in serList: ####################
			ardName = user_inp[0]
			ardIndex = serList.index(ardName)
			try:
				command = user_inp[1]
			except IndexError:
				print("Error: no command given")
				continue
			try:
				value = user_inp[2]
			except IndexError:
				value = None
			arduino_command_input(ardName,command,value)

		else:
			print("Unknown command")


	turnOff()

def arduino_command_input(ardName,command,value):
	global ser
	global serList
	global serTrackFile
	global serTrackOnline
	global serTrackOnlineIndiv
	global serPrint
	global ardCount

	ardIndex = serList.index(ardName)

	if command == 'file':
		commandVal = serTrackFile[ardIndex]
	elif command == 'group':
		commandVal = serTrackOnline[ardIndex]
	elif command == 'indiv':
		commandVal = serTrackOnlineIndiv[ardIndex]
	elif command == 'print':
		commandVal = serPrint[ardIndex]
	else:
		print("Error: invalid command given")
		return

	if value == None:
		print("Value of %s for %s is: %s" % (command,ardName,str(commandVal)))
		return

	if command in ['file','group','indiv','print']:
		if value.lower() == 't':
			if command == 'file':
				serTrackFile[ardIndex] = True
			elif command == 'group':
				serTrackOnline[ardIndex] = True
			elif command == 'indiv':
				serTrackOnlineIndiv[ardIndex] = True
			elif command == 'print':
				serPrint[ardIndex] = True
		elif value.lower() == 'f':
			if command == 'file':
				serTrackFile[ardIndex] = False
			elif command == 'group':
				serTrackOnline[ardIndex] = False
			elif command == 'indiv':
				serTrackOnlineIndiv[ardIndex] = False
			elif command == 'print':
				serPrint[ardIndex] = False
		else:
			print("Error: the command %s takes only t or f")
			return

def arduinoThread(serSerial,serName):
	global ser
	global serList
	global serTrackFile
	global serTrackOnline
	global serTrackOnlineIndiv
	global serPrint
	global isOnline

	ard_init(serSerial)

	while serName in serList:
		ardIndex = serList.index(serName)
		try:
			#serSerial.write('1')
			dataLen = 0
			data = ''
			while not data.endswith('\n'):
				data += serSerial.read(1)
				dataLen += 1

			dataFull = "%s,%s,%s" % (timestamp(),serName,data.strip())

			if serPrint[ardIndex] == True:
				printData(dataFull)
			if serTrackFile[ardIndex] == True:
				writeData(dataFull,serName)
			if serTrackOnline[ardIndex] == True:
				if isOnline:
					sendData(dataFull,serName,'group')
			if serTrackOnlineIndiv[ardIndex] == True:
				sendData(dataFull,serName,'indiv')			
		except TypeError:
			print('\nERROR on %s: serial closed' % serName)
			break
		except Exception,e:
			print('\nERROR on ' + serName + ': ' + str(e))
			break
	print("\n%s thread closing." % serName)
	if serName in serList:
		ser[ardIndex].close()
		del ser[ardIndex]
		del serList[ardIndex]
		del serTrackFile[ardIndex]
		del serTrackOnline[ardIndex]
		del serTrackOnlineIndiv[ardIndex]
		del serPrint[ardIndex]

def timestamp():
	now = datetime.now()
	timest = now.strftime("%Y%m%d%H%M%S.%f")
	timest = timest[:-3]
	return timest

def printData(data):
	print data

def sendData(data,serName,type):
	global saveServ
	global serverBuffer
	if type == 'group':
		serverBuffer += [data]
	elif type == 'indiv':
		indivData = "%s$$$%s" % (serName,data)
		success,s = connectip(saveServ)
		if not success:
			return False
		command = 'tempindiv'
		connectprotocolclient(s,indivData,command)

def writeData(data,serName):
	global saveLoc
	if os.path.exists(saveLoc + '/' + serName + '.csv'):
		addStart = False
	else:
		addStart = True

	with open(saveLoc + '/' + serName + '.csv','a') as ardFile:
		line = data
		if addStart == True:
			ardFile.write('time,name,data\n')
		ardFile.write(line + '\n')

def ard_init(serArd):
	connected = False
	while not connected:
		serin = serArd.read()
		connected = True

def try_serials():
	for n in range(0,21):
		success,ser = connectToSerial(str(n))
		if success:
			return (True,ser,n)
	return(False,None,None)

def connectToSerial(port):
	if os.name == 'nt': ##WINDOWS
		try:
			ser = serial.Serial('COM%s' % port,19200)
			return (True,ser)
		except:
			return (False,None)
	else: ##LINUX or MAC
		if platform.system() == 'Linux':
			try:
				ser = serial.Serial('/dev/ttyACM%s' % port,19200)
				return (True,ser)
			except:
				return (False,None)
		elif platform.system() != 'Windows':
			try:
				ser = serial.Serial('/dev/tty.usb%s' % port,19200)
				return (True,ser)
			except:
				return (False,None)
		else:
			print("Error: Operating system not recognized")
			return (False,None)


def availableDevices():
	avPorts = []
	for n in range(0,21):
		success,ser = connectToSerial(str(n))
		if success:
			ser.close()
			avPorts += [str(n)]
	return avPorts

######################################################
######################################################
####### ONLINE FUNCTIONALITY START ###################
######################################################
######################################################

def connectip(ip=saveServ):
	try:
		host = ip.split(':')[0]
		port = int(ip.split(':')[1])
	except IndexError:
		print('Error: Port must be an ineger')
		return (False,None)
	except ValueError:
		print('Error: Port must be an integer')
		return (False,None)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(2)
	try:
		s.connect((host, port))
	except:
		s.close
		print("Error: Could not connect to %s\n" % ip)
		return (False,None)
	#print "\nConnection successful to " + ip
	return (True,s)

def get_netPass():
	global scriptLoc
	if not os.path.exists(scriptLoc+'/resources/networkpass/default.txt'):
		with open(scriptLoc+'/resources/networkpass/default.txt', "a") as protlist: #file used for identifying what protocols are available
			pass
		return None
	else:
		with open(scriptLoc+'/resources/networkpass/default.txt', "r") as protlist: #file used for identifying what protocols are available
			netpassword = protlist.readline()
		if netpassword.strip() != '':
			return netpassword.strip()
		else:
			return None

def temp_online_client(s,onlineName):
	global serverBuffer
	global isOnline

	print '\nstarting temp client'

	socket_list = [s]

	while isOnline:
		sleep(.1)
		 
		# Get the list sockets which are readable
		ready_to_read,ready_to_write,in_error = select.select(socket_list, [], [], 0)

		for sock in ready_to_read:
			if sock == s:
				try:
					data = sock.recv(32)
				except:
					print 'Error: Server has closed connection'
					isOnline = False
					continue

				if data:
					if data == 'ready?':
						sock.sendall('ready!')
						sock.recv(2)
					elif data.startswith('x||'):
						sock.sendall('x||ok')
						print 'Error: Server signals to close connection'
						isOnline = False
					else:
						print(data)

				else:
					print '\nError: Disconnected from temp server, data = empty'
					isOnline = False

		if len(serverBuffer) > 0:
			data_send = serverBuffer[0][:129]
			s.sendall('d||' + data_send)
			s.recv(11)
			del serverBuffer[0]

	print('Closing online group thread...')

	try:
		s.sendall('/exit')
	except:
		print("sent leaving notice to server")


def sendIndivData(s,data):
	name,data = data.split('$$$')
	s.sendall(name)
	s.recv(2)
	s.sendall(data)
	s.recv(2)

def startGroupThread(s,data):
	global isOnline

	s.sendall(data)
	valid = s.recv(1)
	if valid != 'y':
		print("Error: client name already taken on server")

	else:

		try:
			arduinoprocess = threading.Thread(target=temp_online_client,args=(s,data))
			arduinoprocess.daemon = True
			arduinoprocess.start()
			isOnline = True
		except:
			print("Error: issue starting arduino thread")
			return

def startGroupData(s,data):
	s.sendall(data)
	s.recv(2)

def temp_recv_file(s): #receives files from master
	gene = s.recv(1024)
	s.send('ok')
	filename = gene.split(':')

	downloadslocation = scriptLoc + "/" + downloadslocation 

	has = s.recv(2)
	if has != 'ok':
		return '404'
	else:
		s.sendall('ok')
		file_cache = s.recv(16)
		file_cache = int(file_cache.strip())
		s.sendall('ok')
		size = s.recv(16)
		size = int(size.strip())
		recvd = 0
		print filename + ' download in progress...'
		if not os.path.exists(downloadslocation):
			os.makedirs(downloadslocation)
		q = open(os.path.join(downloadslocation, filename), 'wb')
		while size > recvd:
			sys.stdout.write(str((float(recvd)/size)*100)[:4]+ '%   ' + str(recvd) + '/' + str(size) + ' B\r')
			sys.stdout.flush()
			data = s.recv(1024)
			if not data: 
				break
			recvd += len(data)
			q.write(data)
		s.sendall('ok')
		q.close()
		sys.stdout.write('100.0%\n')
		print filename + ' download complete'
		return '111'

def distinguishCommand(s,data,command):
	if command == 'tempgroup':
		s.sendall(command)
		has = s.recv(2)
		if has != 'ok':
			print("Error: command not understood by server")
		else:
			startGroupThread(s,data)
	elif command == 'tempindiv':
		s.sendall(command)
		has = s.recv(2)
		if has != 'ok':
			print("Error: command not understood by server")
		else:
			sendIndivData(s,data)
	elif command == 'startdata':
		s.sendall(command)
		has = s.recv(2)
		if has != 'ok':
			print("Error: command not understood by server")
		else:
			startGroupData(s,data)
			print("Server signalled to START group data collection")
	elif command == 'stopdata':
		s.sendall(command)
		has = s.recv(2)
		if has != 'ok':
			print("Error: command not understood by server")
		else:
			print("Server signalled to STOP group data collection")
	else:
		s.sendall('badcommand')
		has = s.recv(2)
		print("Error: Command unknown on client")
				


def connectprotocolclient(s, data, command): #communicate via protocol to command seed
	global cliversion
	netPass = get_netPass()

	s.sendall('ok')
	hasPass = s.recv(2)
	if hasPass == 'yp':
		if self.netPass == None:
			s.sendall('n')
			s.close
			return 'requires password'
		else:
			s.sendall('y')
			s.recv(2)
			s.sendall(netPass)
			right = s.recv(1)
			if right != 'y':
				s.close
				return 'incorrect password'

	s.sendall('arduinotemp:temp_client:%s' % cliversion)
	compat = s.recv(1)

	if compat == 'y':
		s.sendall('ok')
		s.recv(2)
		#print 'success initiated'
		return distinguishCommand(s, data, command)

	else:
		s.sendall('ok')
		resp = s.recv(1024)
		s.close
		#print 'failure. closing connection...'
		return resp

	s.close
	return 'connection closed'


if __name__ == '__main__':
	temp_measure_main()
