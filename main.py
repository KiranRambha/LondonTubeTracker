import sys
import os
from pathlib import Path
libdir = str(Path(__file__).resolve().parent / 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd7in5_V2
from PIL import Image, ImageDraw, ImageFont
from manage_refresh import get_refresh_count, set_refresh_count
from tfl import get_arrivals_and_latest_location, get_arrivals_and_destination, fetch_bus_arrivals_concurrently
from datetime import datetime, timedelta

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
font_path = os.path.join(picdir, 'DejaVuSans-Bold.ttf')

DEBUG = False

# Initialize the E-Ink display (update to match your model)
epd = epd7in5_V2.EPD()

# 0 = black, 255 = white
background_color = 255
font_color = 0

kingsbury_station_id = '940GZZLUKBY'
kingsbury_platform_name = 'Southbound - Platform 2'
wembley_park_station_id = '940GZZLUWYP'
wembley_park_platform_name = 'Southbound - Platform 5'

bus_list = [
  {
    'direction': 'Wembley',
    'station_id': '490015769S',
    'lineId': ['79']
  },
  {
    'direction': 'Harrow',
    'station_id': '490000128B',
    'lineId': ['183', 'sl10']
  },
  {
    'direction': 'Hendon',
    'station_id': '490000128A',
    'lineId': ['183', 'sl10'],
  },
]

# Load fonts
font_large = ImageFont.truetype(font_path, 30)
font_medium = ImageFont.truetype(font_path, 24)
font_small = ImageFont.truetype(font_path, 18)

# Create an empty image
WIDTH, HEIGHT = 800, 480  # Resolution for 7.5" E-Ink display
count = get_refresh_count()

if DEBUG:
  count = 0

kingsburyLatestArrivals = ''
wembleyLatestArrivals = ''
buses_to_wembley = ''
buses_to_harrow = ''
buses_to_hendon = ''

def full_refresh_api_calls():
  kingsburyLatestArrivals = get_arrivals_and_latest_location(kingsbury_station_id, kingsbury_platform_name)
  wembleyLatestArrivals = get_arrivals_and_destination(wembley_park_station_id, wembley_park_platform_name)
  bus_arrivals = fetch_bus_arrivals_concurrently(bus_list)

  return {
    "kingsburyLatestArrivals": kingsburyLatestArrivals,
    "wembleyLatestArrivals": wembleyLatestArrivals,
    "buses_to_wembley": bus_arrivals.get('490015769S', {}),
    "buses_to_harrow": bus_arrivals.get('490000128B', {}),
    "buses_to_hendon": bus_arrivals.get('490000128A', {})
  }

def partial_refresh_api_call():
  kingsburyLatestArrivals = get_arrivals_and_latest_location(kingsbury_station_id, kingsbury_platform_name)

def generate_image():
  result = full_refresh_api_calls()
  kingsburyLatestArrivals = result['kingsburyLatestArrivals']
  wembleyLatestArrivals = result['wembleyLatestArrivals']
  buses_to_wembley = result['buses_to_wembley']
  buses_to_harrow = result['buses_to_harrow']
  buses_to_hendon = result['buses_to_hendon']

  # Get current date and time
  now = datetime.now()
  current_date = now.strftime("%A, %B %d")
  current_time = now.strftime("%H:%M")

  # Add 5 minutes to the current time
  time_plus_five_minutes = now + timedelta(minutes=5)
  current_time_plus_five = time_plus_five_minutes.strftime("%H:%M")

  image = Image.new("1", (WIDTH, HEIGHT), background_color)  # 1-bit monochrome image
  draw = ImageDraw.Draw(image)
  # Section: Weather & Pollution
  draw.text((10, 10), "London Underground & Bus", font=font_large, fill=font_color)
  draw.text((530, 20), f"{current_date}", font=font_small, fill=font_color)


  # Divider
  draw.line((0, 50, WIDTH, 50), fill=font_color, width=5)

  # Section: Jubilee Southbound Arrivals
  draw.text((10, 60), "Jubilee Southbound Arrivals - Kingsbury", font=font_medium, fill=font_color)

  draw.text((10, 95), "Stratford - " + str(kingsburyLatestArrivals['arrival_times']), font=font_small, fill=font_color)
  draw.text((10, 120), "Current Location - " + str(kingsburyLatestArrivals['current_location']), font=font_small, fill=font_color)

  # Divider
  draw.line((0, 145, WIDTH, 145), fill=font_color, width=1)

  # Section: Jubilee Southbound Arrivals
  draw.text((10, 155), "Metropolitan Southbound Arrivals - Wembley Park", font=font_medium, fill=font_color)

  draw.text((10, 190), str(wembleyLatestArrivals[0]['destination']) + " - " + str(wembleyLatestArrivals[0]['arrival_times']), font=font_small, fill=font_color)
  draw.text((10, 215), str(wembleyLatestArrivals[1]['destination']) + " - " + str(wembleyLatestArrivals[1]['arrival_times']), font=font_small, fill=font_color)
  if (len(wembleyLatestArrivals) > 2):
    draw.text((10, 240), str(wembleyLatestArrivals[2]['destination']) + " - " + str(wembleyLatestArrivals[2]['arrival_times']), font=font_small, fill=font_color)

  # Divider
  draw.line((0, 265, WIDTH, 265), fill=font_color, width=1)

  # Section: Bus Schedules
  draw.text((10, 275), "Bus Schedule", font=font_medium, fill=font_color)

  draw.text((10, 310), "79 to Wembley - " + buses_to_wembley.get('79', ''), font=font_small, fill=font_color)
  draw.text((10, 335), "183 to Harrow - " + buses_to_harrow.get('183', ''), font=font_small, fill=font_color)
  draw.text((10, 360), "SL10 to Harrow - " + buses_to_harrow.get('sl10', ''), font=font_small, fill=font_color)
  draw.text((10, 385), "183 to Hendon - " + buses_to_hendon.get('183', ''), font=font_small, fill=font_color)
  draw.text((10, 410), "SL10 to Hendon - " + buses_to_hendon.get('sl10', ''), font=font_small, fill=font_color)

  # Divider
  draw.line((0, 435, WIDTH, 435), fill=font_color, width=1)

  draw.text((10, 450), f"Last Update: {current_time}", font=font_small, fill=font_color)

  # Footer: Date and Time
  draw.text((590, 450), f"Next Update: {current_time_plus_five}", font=font_small, fill=font_color)
  return image

if count == 0:
  if DEBUG:
      # Save the image
      generate_image().save("output.png")
  else:
      print("Initializing Display")
      epd.init()
      print("Clear Display")
      epd.Clear()
      latest_image = generate_image()
      epd.display(epd.getbuffer(latest_image))
      epd.sleep()

      # Cache Image
      latest_image.save("output.png")
      count += 1
      set_refresh_count(count)
else:
  partial_refresh_api_call()
  epd.init_part()
  reuse_image = Image.open("output.png")
  reused_draw = ImageDraw.Draw(reuse_image)
  reused_draw.rectangle((5, 90, 600, 140), fill = background_color)
  reused_draw.text((10, 95), "Stratford - " + str(kingsburyLatestArrivals['arrival_times']), font=font_small, fill=font_color)
  reused_draw.text((10, 120), "Current Location - " + str(kingsburyLatestArrivals['current_location']), font=font_small, fill=font_color)
  epd.display_Partial(epd.getbuffer(reuse_image), 0, 0, WIDTH, HEIGHT)
  set_refresh_count(0)

print("Schedule displayed successfully!")
