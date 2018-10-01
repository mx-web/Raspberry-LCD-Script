import lcddriver

lcd = lcddriver.lcd()

first = raw_input('First Line LCD Text:\n')
second = raw_input('Second Line LCD Text:\n')
third = "Hello World";

lcd.lcd_display_string(first, 1)
lcd.lcd_display_string(second, 2)
lcd.lcd_display_string(third, 3)
