WHOAMI = "LAOPO"
SEAKRIT = "REDACTED"
FRIEND = "PAOLO" #"tadpoles"
DEFOLT_LAT = 41.796235
DEFOLT_LONG = -87.581281

# With many thanks to Adafruit_CircuitPython_GPS and its examples folder
# Also to "Chris H" off whose magnetometer tilt-compensation code my own is based:
# learn.adafruit.com/lsm303-accelerometer-slash-compass-breakout/calibration
# #chris-hs-calibration-6-4

import time
import math
import board
import busio
import adafruit_gps
import adafruit_lsm303
import serial
import RPi.GPIO as GPIO

import requests

#SERVER_ADDR = 'http://whatever-ip-here:5000'
SERVER_ADDR = 'http://whereispaolo.org'

url_log = SERVER_ADDR + '/log'
url_giveloc = SERVER_ADDR + '/givelocation'
url_getloc = SERVER_ADDR + '/getlocation'

GPIO.setmode(GPIO.BCM)
cr_servo_pwm_pin = 12
GPIO.setup(cr_servo_pwm_pin, GPIO.OUT)
cr_servo_pwm = GPIO.PWM(cr_servo_pwm_pin, 50) # channel, frequency
#cr_servo_pwm.start(7.5) # calibrate to servo neutral

# Yay accelerometer and magnetometer!
i2c = busio.I2C(board.SCL, board.SDA)
accelmag = adafruit_lsm303.LSM303(i2c)

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
last_acm_print = time.monotonic()
friend_lat = None
friend_long = None
my_lat = DEFOLT_LAT
my_long = DEFOLT_LONG
heading = 0
while True:
    try:
        # Make sure to call gps.update() every loop iteration and at least twice
        # as fast as data comes from the GPS unit (usually every second).
        # This returns a bool that's true if it parsed new data (you can ignore it
        # though if you don't care and instead look at the has_fix property).
        gps.update()
        current = time.monotonic()
        # Every second print out current accel/mag readings.
        if current - last_acm_print >= 1.0:
            last_acm_print = current
            acc_x, acc_y, acc_z = accelmag.acceleration
            mag_x, mag_y, mag_z = accelmag.magnetic

            #print('Acceleration (m/s^2): ({0:10.3f}, {1:10.3f}, {2:10.3f})'.format(acc_x, acc_y, acc_z))
            #print('Magnetometer (gauss): ({0:10.3f}, {1:10.3f}, {2:10.3f})'.format(mag_x, mag_y, mag_z))

            acc_norm = math.sqrt(acc_x * acc_x + acc_y * acc_y + acc_z * acc_z)
            pitch = math.asin(acc_x/acc_norm)
            roll =  math.asin(acc_y/acc_norm)
            #print('Pitch  : {}'.format(math.degrees(pitch)))
            #print('Roll   : {}'.format(math.degrees(roll)))

            # Could normalize mag vals as above but ehhh

            # Tilt compensated magnetic sensor measurements
            tilt_mag_x = mag_x * math.cos(pitch) - mag_z * math.sin(pitch)
            tilt_mag_y = mag_y * math.cos(roll) - mag_z * math.sin(roll)
            #print('Tilt-comp mag       : ({0:10.3f}, {1:10.3f})'.format(tilt_mag_x, tilt_mag_y))

            heading = math.degrees(math.atan2(tilt_mag_y, tilt_mag_x))
            heading = 360 + heading if heading < 0 else heading
            print('Heading: {}'.format(heading))
            #print('')
        # Every second print out current location details if there's a fix.
        if current - last_gps_print >= 3.0:
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

        fr = requests.get(url_getloc+'?name={}'.format(FRIEND))
        try:
            friend_lat = fr.json()['latitude']
            friend_long = fr.json()['longitude']
        except Exception as e: # shh
            print(e)
            continue # ???

        # https://www.movable-type.co.uk/scripts/latlong.html
        fr_lat_r = math.radians(friend_lat)
        fr_long_r = math.radians(friend_long)
        my_lat_r = math.radians(my_lat)
        my_long_r = math.radians(my_long)
        fwd_azimuth = math.degrees(math.atan2(
            math.sin(fr_long_r - my_long_r) * math.cos(fr_lat_r),
            math.cos(my_lat_r) * math.sin(fr_lat_r)
            - math.sin(my_lat_r) * math.cos(fr_lat_r)
            * math.cos(fr_long_r-my_long_r)
        ))
        fwd_azimuth = 360 + fwd_azimuth if fwd_azimuth < 0 else fwd_azimuth

        print("Forward azimuth: {0:.6f} degrees".format(fwd_azimuth))
        azi_payload = {'Fwd Azimuth': fwd_azimuth}
        r = requests.post(url_log, json=azi_payload)

        diff = fwd_azimuth - heading
        diff = diff % 360
        diff = diff - 360 if diff > 180 else diff
        print("Diff: {0:.6f} degrees".format(diff))
        # Tolerate X degrees error
        tolerate = 5.0
        if diff < 0 - tolerate:
            # Turn arrow counter-clockwise... slowly
            cr_servo_pwm.start(7.7)
        elif diff > 0 + tolerate:
            # Turn arrow clockwise... slowly
            cr_servo_pwm.start(7.3)

        #time.sleep(1)
        #cr_servo_pwm.stop()
        #time.sleep(1)
        print('\n')
    except Exception as e:
        if e is not KeyboardInterrupt:
            # MUAHAHA!!!
            continue
