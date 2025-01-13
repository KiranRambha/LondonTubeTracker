import sys
import os
from pathlib import Path
libdir = str(Path(__file__).resolve().parent / 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)
    
from waveshare_epd import epd7in5_V2

# Initialize the E-Ink display (update to match your model)
epd = epd7in5_V2.EPD()

# Initialize display and clear it
def clear_display():
    print("Initializing Display")
    epd.init()
    print("Clear Display")
    epd.Clear()
    epd.sleep()  # Put the display to sleep to save power

# Call the clear_display function to clear the screen and consume less power
clear_display()

print("Display cleared successfully and power saved.")
