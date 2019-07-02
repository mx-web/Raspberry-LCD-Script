#This program sinmulates LCDd behaviour and use LCDproc protocal
#Python version must be 3.3 or above
#Install python3-smbus for support of the driver


import lcddriver,LCDscreen, time, socket, sys, pprint, signal, csv, configparser, getopt
from time import localtime, strftime
from io import StringIO


#--------------------- Main program below ---------------
if sys.version_info[0] < 3:
    raise Exception("You must use Python 3.3 or above to run this program")

if sys.version_info[1] < 3:
    raise Exception("You must use Python 3.3 or above to run this program")

# obtain arguments
inifile='LCDd.ini'
opts, args = getopt.getopt(sys.argv[1:],"c:")
for opt, arg in opts:
	if opt == '-c':
		inifile = arg

#obtain config from config file
config = configparser.ConfigParser()
config.read(inifile)

if "DEFAULT" not in config:
	print ("Error reading config. All elements must be under [DEFAULT]")
	exit (1)

if "port" not in config["DEFAULT"] or "i2c_address" not in config["DEFAULT"]:
	print ("Error reading config. Port/i2c_address must be defined under [DEFAULT]")
	exit (1)

port =int(config["DEFAULT"]["port"])	

if "host" not in config["DEFAULT"]:
	host=""
else:
	host = config["DEFAULT"]["host"]

#initiate value
status = {}
screen = {}
c = False


#functions
def welcome_screen():
#welcome_screen has to ba called whenever before the s.accept is made for resetting value
	global status, c
	
	lcd.lcd_display_string("LCDd in Python V1.0", 1)
	lcd.lcd_display_string("IP:"+ host + ":" + str(port), 2)
	lcd.lcd_display_string(strftime("%Y-%m-%d %H:%M:%S", localtime()), 4)
	status.clear();
	screen.clear();
	signal.alarm(0)
	status['lastcomm'] = 0
	status['datastream'] = ""
	status['datastack'] = []
	status['Handshaken'] = False
	status['sentping'] = False
	status['listening_screen'] = 0
	status['listening_screen_name'] = ""
	status['listening_screen_since'] = 0
	status['empty_data'] = 0
	c = False

def read_connection(c):
	global status
	
	try:
		status['datastream'] += c.recv(1024).strip().decode('utf-8')+"\n"
	except socket.timeout:
		welcome_screen()
		lcd.lcd_display_string("Accepting connection", 3)
		return False
	except BlockingIOError:
		return False
	signal.alarm(10)
	status['sentping'] = False
	arrived_datastack = status['datastream'].split('\n')
	for line in arrived_datastack:
		status['datastack'].append(line)
	status['datastream']=status['datastack'].pop()
	#pprint.pprint(status['datastack'])
	return True

def write_connection(c,string):

	try:
		string += "\n"
		c.send(string.encode())
	except:
		welcome_screen()
		lcd.lcd_display_string("Accepting connection", 3)

def InterruptHandler(signalrecv, frame):
	global s, c
	signalrecvstr=""
	if signalrecv==signal.SIGINT:
		signalrecvstr="SIGINT"
	elif signalrecv==signal.SIGTERM:
		signalrecvstr="SIGTERM"
	else:
		signalrecvstr=format(signalrecv)
	print("Interrupt (ID: "+signalrecvstr+") has been caught. Cleaning up...")
	lcd.lcd_clear()
	lcd.lcd_display_string("  "+signalrecvstr+" Received -", 2)
	lcd.lcd_display_string("     Good bye      -", 3)
	if c is not False:
		c.close()
		print ("Connection closed")
	s.close
	exit(0)
	
def sigalrmHandler(signalrecv, frame):
	global s, c, status
	if status['sentping'] == False:
		status['sentping'] = True
		print ("Sent ping to client")
		write_connection(c,"ping")
		signal.alarm(5)
	else:
		c.close()
		c = False
		print ("Connection to client closed due to no response")
		welcome_screen()
		lcd.lcd_display_string("Accepting connection", 3)

#Signal handlier
signal.signal(signal.SIGINT, InterruptHandler)
signal.signal(signal.SIGTERM, InterruptHandler)
signal.signal(signal.SIGALRM, sigalrmHandler)

#initiate LCD
lcd = lcddriver.lcd(config)
lcd.lcd_backlight("on")
Backlightstatus = "on";
welcome_screen()
lcd.lcd_display_string("Initalizing", 3)
timenow = strftime("%Y-%m-%d %H:%M:%S", localtime())


#initiate socket for server accepting connection
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Prevent socket in a TIME_WAIT state after program closed
try:
	s.bind((host, port))
except socket.error as msg:
	print ("Error when binding socket:"+str(msg))
	lcd.lcd_display_string("Binding failed at", 3)
	exit (1)
s.listen(5)
s.setblocking(0)


lcd.lcd_display_string("Accepting connection", 3)

while 1:
	time.sleep(0.25)
	try:
		if c is False:
			try:
				c,addr = s.accept() #blocking accept
				lcd.lcd_display_string("Connection received@", 3)
				status['lastcomm'] = localtime()
				c.settimeout(5)
			except BlockingIOError:
				if timenow != strftime("%Y.%m.%d %H:%M:%S", localtime()):		
					timenow = strftime("%Y.%m.%d %H:%M:%S", localtime())
					lcd.lcd_display_string(timenow, 4)
				continue
			except:
				welcome_screen()
				lcd.lcd_display_string("Accepting connection", 3)
		else:
				
			read_connection(c)
			
			if status['Handshaken'] is False:
				
				if status['datastack'].pop(0).find("hello")!=0:
					c.send("huh? Handshake sequence incorrect\n".encode())
					c.close()
					welcome_screen()
					lcd.lcd_display_string("Accepting connection", 3)
				else: #Handshake completed
					status['Handshaken'] = True
					lcd.lcd_display_string("Connection established", 3)
					lcd.lcd_display_string("                    ", 4)
					write_connection(c,"connect LCDproc 0")
					c.setblocking(0)
			else:
				
				#screen issue (change screen for every 5 seconds)
				if time.time()-status['listening_screen_since'] >5 and len(screen)> 1:
					no_of_screen=len(screen);
					sceen_to_listen=status['listening_screen']+1
					if sceen_to_listen >= len(screen):
						sceen_to_listen=0
					i=0
					#pprint.pprint(screen)
					for screen_name, target_screen in screen.items():
						if i != sceen_to_listen:
							i+=1
							continue
						write_connection(c,"listen " + screen_name)
						write_connection(c,"ignore " + status['listening_screen_name'])
						target_screen.listen(lcd)
						status['listening_screen_name']=screen_name
						status['listening_screen_since']=time.time()
						status['listening_screen']=sceen_to_listen
						break
					
					
				#process all data in data stack
				while len(status['datastack']) > 0:
					data=status['datastack'].pop(0)
					#pprint.pprint(data)
					reader = list(csv.reader(StringIO(data), delimiter=' '))
					if len(reader)==0: #empty data
						status['empty_data']+=1
						if status['empty_data'] > 10:
							write_connection(c,"huh? Too much empty data. Closing connection")
							c.close()
							welcome_screen()
							lcd.lcd_display_string("Accepting connection", 3)
						continue
					dataarray=reader[0]
					if dataarray[0]== "screen_add": #
						#print ("Received screen_add command")
						if dataarray[1] in screen:
							write_connection(c,"huh? Screen \""+dataarray[1]+"\" already created")
						else:
							screen[dataarray[1]]=LCDscreen.LCDscreen(dataarray[1])
							if len(screen) == 1:
								screen[dataarray[1]].listen(lcd)
								write_connection(c,"listen " + dataarray[1])
								status['listening_screen'] = 0
								status['listening_screen_name']=dataarray[1]
								status['listening_screen_since']=time.time()
					elif dataarray[0]== "widget_add":
						#print ("Received widget_add command")
						if dataarray[1] not in screen:
							write_connection(c,"huh? Screen \""+dataarray[1]+"\" not defined")
						else:
							write_connection(c,screen[dataarray[1]].addwidget(lcd,dataarray))
					elif dataarray[0]== "screen_set":
						#print ("Received screen_set command")
						if dataarray[1] in screen:
							write_connection(c,screen[dataarray[1]].set(lcd,dataarray))
						else:
							write_connection(c,"huh? Screen \""+dataarray[1]+"\" not defined")
					elif dataarray[0]== "widget_set":
						#print ("Received widget_set command")
						if dataarray[1] not in screen:
							write_connection(c,"huh? Screen \""+dataarray[1]+"\" not defined")
						else:
							write_connection(c,screen[dataarray[1]].setwidget(lcd,dataarray))	
					elif dataarray[0]== "pong":
						print ("Received pong")
					else:
						print ("Unknown command received:", data)
						write_connection(c,"huh? Unknown command")
	except ConnectionResetError:
		print ("Caught ConnectionResetError Exception in main loop")
		welcome_screen()
		lcd.lcd_display_string("Accepting connection", 3)
	except IOError as e:
		print ("Caught IOError Exception in main loop")
		print (e)
		write_connection(c,"huh? I/O Error within server. Closing connection")
		c.close()
		time.sleep(5)
		welcome_screen()
		lcd.lcd_display_string("Accepting connection", 3)
		