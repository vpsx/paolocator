# For paolocator-b: Just broadcast location to server
WHOAMI = "PAOLO"
SEAKRIT = "REDACTED"
DEFOLT_LAT = 41.788272
DEFOLT_LONG = -87.595412

import time
import board
import busio
import adafruit_gps
import serial

import requests

SERVER_ADDR = 'http://whereispaolo.org'

url_log = SERVER_ADDR + '/log'
url_giveloc = SERVER_ADDR + '/givelocation'

# pi--therefore use pyserial library for uart access.
# I'm using built-in UART on Pi, so device name /dev/ttyS0
# That's probably "teletype serial zero" I guess?
uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=3000)

# Create a GPS module instance
gps = adafruit_gps.GPS(uart)

# Initialize the GPS module by changing what data it sends and at what rate.
# These are NMEA extensions for PMTK_314_SET_NMEA_OUTPUT and
# PMTK_220_SET_NMEA_UPDATERATE but you can send anything from here to adjust
# the GPS module behavior:
#   https://cdn-shop.adafruit.com/datasheets/PMTK_A11.pdf

# Turn on the basic GGA and RMC info (what you typically want)
gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
# Turn on just minimum info (RMC only, location):
#gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')

# Set update rate to once a second (1hz) which is what you typically want.
gps.send_command(b'PMTK220,1000')
# Or decrease to once every two seconds by doubling the millisecond value.
# Be sure to also increase your UART timeout above!
#gps.send_command(b'PMTK220,2000')
# You can also speed up the rate, but don't go too fast or else you can lose
# data during parsing.  This would be twice a second (2hz, 500ms delay):
#gps.send_command(b'PMTK220,500')

# Main loop runs forever printing the location, etc. every second.
last_gps_print = time.monotonic()
my_lat = DEFOLT_LAT
my_long = DEFOLT_LONG
while True:
    try:
        # Make sure to call gps.update() every loop iteration and at least twice
        # as fast as data comes from the GPS unit (usually every second).
        # This returns a bool that's true if it parsed new data (you can ignore it
        # though if you don't care and instead look at the has_fix property).
        gps.update()
        current = time.monotonic()
        # Every second print out current location details if there's a fix.
        if current - last_gps_print >= 5.0:
            last_gps_print = current
            if not gps.has_fix:
                # Try again if we don't have a fix yet.
                print('Waiting for fix...')
                r = requests.post(url_log, json={'msg':'Waiting for fix...'})
                continue
            # We have a fix! (gps.has_fix is true)
            print('=' * 40)  # Print a separator line.
            timestring = 'Fix at {}/{}/{} {:02}:{:02}:{:02}'.format(
                gps.timestamp_utc.tm_mon,   # Grab parts of the time from the
                gps.timestamp_utc.tm_mday,  # struct_time object that holds
                gps.timestamp_utc.tm_year,  # the fix time.  Note you might
                gps.timestamp_utc.tm_hour,  # not get all data like year, day,
                gps.timestamp_utc.tm_min,   # month!
                gps.timestamp_utc.tm_sec
            )
            print('Timestamp: {}'.format(timestring))
            print('Latitude: {0:.6f} degrees'.format(gps.latitude))
            print('Longitude: {0:.6f} degrees'.format(gps.longitude))
            gps_payload= {
                'Name': WHOAMI,
                'Timestamp': timestring,
                'Latitude': gps.latitude,
                'Longitude': gps.longitude,
            }
            r = requests.post(url_log, json=gps_payload)
            r = requests.post(url_giveloc, json=gps_payload)
            my_lat = gps.latitude
            my_long = gps.longitude

    except Exception as e:
        if e is not KeyboardInterrupt:
            # MUAHAHA!!!
            continue
