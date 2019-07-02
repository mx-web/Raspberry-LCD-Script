

class LCDscreen:

	identity = ""
	linemem = []
	charowner=[]
	widget = {}
	backlight="on"
	
	def __init__(self, name):
		self.identity = name
		#print ("Screen \""+name+"\" created")
		w, h = 20, 4;
		self.charowner = [['' for x in range(w)] for y in range(h)] 
		self.linemem = [[' ' for x in range(w)] for y in range(h)] 
		
	def listen(self,lcd):
		#print ("Listening screen \""+self.identity+"\"")
		lcd.lcd_clear()
		
		displaystr = ""
		for y in range (0,4,1):
			for x in range (0,20,1):
				displaystr += self.linemem[y][x]
			lcd.lcd_display_string(displaystr, y+1)
			displaystr = ""
		lcd.lcd_backlight(self.backlight)
	
	def set(self,lcd,dataarray): #return msg to client
		global c
		
		if dataarray[2] =="-heartbeat":
			return "huh? \"heartbeat\" is not implemented"
		
		elif dataarray[2] =="-backlight":
			lcd.lcd_backlight(dataarray[3])
			self.backlight = dataarray[3]
			return "success"
		else:
			"huh? Unknown command"
	
	def addwidget(self,lcd,dataarray): #return msg to client
		if dataarray[2] in self.widget:
			return "huh? Widget \""+dataarray[2]+"\" already created"
		elif dataarray[3]!="string":
			return "huh? This server only support \"string\" type for widget"
		else:
			self.widget[dataarray[2]] = [0,0,""] #y,x,string
			return "success"
	
	def setwidget(self,lcd,dataarray): #return msg to client
		name = dataarray[2]
		if name not in self.widget:
			return "huh? Widget \""+dataarray[2]+"\" not defined"
		
		oldy=self.widget[name][0]		
		data_string=dataarray[5]
		xpos=int(dataarray[3])-1
		ypos=int(dataarray[4])-1
		self.widget[name][0]=ypos #y
		self.widget[name][1]=xpos #x
		self.widget[name][2]=data_string #string
		
		#first clear out all char belongs to widget on line oldy:
		for x in range (0,20,1):
			#print("oldy=",oldy,", x=",x)
			if self.charowner[oldy][x]==name:
				self.linemem[oldy][x]=' '
				self.charowner[oldy][x]=''
		
		#write char on line y
		x=xpos
		for s in range(0,len(data_string),1):
			if x >19:
				break
			#print("ypos=",ypos,", x=",x)
			self.charowner[ypos][x]=name
			self.linemem[ypos][x]=data_string[s]
			x += 1

		displaystr = ""
		for x in range (0,20,1):
			displaystr += self.linemem[ypos][x]
		lcd.lcd_display_string(displaystr, ypos+1)
		
		if ypos!=oldy:
			displaystr = ""
			for x in range (0,20,1):
				displaystr += self.linemem[oldy][x]
			lcd.lcd_display_string(displaystr, oldy+1)
		return "success"