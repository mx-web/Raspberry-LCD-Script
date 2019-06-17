#!/usr/bin/python
import sys
sys.path.append("./lib")

import i2c_lib, pprint
from time import *

# LCD Address
#ADDRESS = 0x20

# commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20 # 0b00100000
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08 #0b00001000
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

LCD_LINE1ADDR = 0x80 #dec 128 (addr=0-19)
LCD_LINE2ADDR = 0xC0 #dec 192 (addr=64-83)
LCD_LINE3ADDR = 0x94 #dec 148 (addr=20-39)
LCD_LINE4ADDR = 0xD4 #dec 212 (addr=84-103)

En = 0b00000100 # Enable bit
Rw = 0b00000010 # Read/Write bit
Rs = 0b00000001 # Register select bit

class lcd:

	backlight_status = LCD_BACKLIGHT
	linemem = ["","","",""]

	#initializes objects and lcd
	def __init__(self,config):
		ADDRESS=int(config["DEFAULT"]["i2c_address"],16)
		self.lcd_device = i2c_lib.i2c_device(ADDRESS)
		self.lcd_write(0x03)
		self.lcd_write(0x03)
		self.lcd_write(0x03)
		self.lcd_write(0x02)

		self.lcd_write(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
		self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
		self.lcd_write(LCD_CLEARDISPLAY)
		self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
		sleep(0.2)

	# clocks EN to latch command
	def lcd_strobe(self, data):
		self.lcd_device.write_cmd(data | En | self.backlight_status)
		sleep(.0005)
		self.lcd_device.write_cmd(((data & ~En) | self.backlight_status))
		sleep(.0001)

	def lcd_write_four_bits(self, data):
		self.lcd_device.write_cmd(data | self.backlight_status)
		self.lcd_strobe(data)

	# write a command to lcd
	def lcd_write(self, cmd, mode=0):
		self.lcd_write_four_bits(mode | (cmd & 0xF0))
		self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))
		
	#turn on/off the lcd backlight
	def lcd_backlight(self, state):
		if state in ("on","On","ON"):
			self.lcd_device.write_cmd(LCD_BACKLIGHT)
			self.backlight_status = LCD_BACKLIGHT
		elif state in ("off","Off","OFF"):
			self.lcd_device.write_cmd(LCD_NOBACKLIGHT)
			self.backlight_status = LCD_NOBACKLIGHT
		else:
			print("Unknown State!")

	# put string function
	def lcd_display_string(self, string, line):
		if line == 1:
			cursorpos=LCD_LINE1ADDR
			old_str = self.linemem[0]
			self.linemem[0] = string
		if line == 2:
			cursorpos=LCD_LINE2ADDR
			old_str = self.linemem[1]
			self.linemem[1] = string
		if line == 3:
			cursorpos=LCD_LINE3ADDR
			old_str = self.linemem[2]
			self.linemem[2] = string
		if line == 4:
			cursorpos=LCD_LINE4ADDR
			old_str = self.linemem[3]
			self.linemem[3] = string
		
		old_cursorpos = 0x00
		
		#updateneeded=False
		for i in range(0,20,1):
			#phrase old string
			if(len(old_str)>i):
				old_char=old_str[i]
			else: 
				old_char = " "
			#phrase new string
			if(len(string)>i):
				char=string[i]
			else:
				char = " "
			
			if old_char != char: #Update needed
				#updateneeded=True
				if cursorpos-old_cursorpos == 1:
					self.lcd_write(ord(char), Rs)
				else:
					self.lcd_write(cursorpos)
					self.lcd_write(ord(char), Rs)
				old_cursorpos = cursorpos
			cursorpos += 1
		
		#if updateneeded==True:
		#	print ("Updated Message:", string)
		
	# clear lcd and set to home
	def lcd_clear(self):
		self.lcd_write(LCD_CLEARDISPLAY)
		self.lcd_write(LCD_RETURNHOME)
		self.linemem = ["","","",""]
