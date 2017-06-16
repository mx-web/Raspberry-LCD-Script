import lcddriver

lcd = lcddriver.lcd()

first = raw_input('First Line LCD Text:\n')
second = raw_input('Second Line LCD Text:\n')


lcd.lcd_display_string(first, 1)
lcd.lcd_display_string(second, 2)
