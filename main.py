import json
import math
import time

import asyncio
import websockets

import adafruit_gps
import adafruit_lsm303_accel
import adafruit_lsm303dlh_mag
import board
import busio
import RPi.GPIO as GPIO
import serial

# #########################################################################

# Configuration

TESTMODE = False
# Test P values near Porta Nuova
TEST_P_LAT = 45.0623136
TEST_P_LNG = 7.6795449
# Test Z values near Poste Italiane
TEST_Z_LAT = 45.049769
TEST_Z_LNG = 7.675253

# PAOLOSERVER ADDRESS
PAOLOSERVER_WSADDR = "ws://whereispaolo.org:8080"

# Duty cycle values - these should lean lower
SERVO_NEUTRAL = 7.4       #7.5
SERVO_CLOCKWISE = 6.8     #7.2
SERVO_ANTICLOCKWISE = 7.8 #7.8
# yes
SERVO_MOVE_TIME = 0.16

# Tolerate X degrees' difference between fwd azimuth and heading
TOLERANCE = 7.0

# Cadence in seconds;
# Too short, and the WS stream backs up while gobbler waits for other fns
# Too long, and other fns must wait for gobbler, stalling the pointer
# A better solution is needed--probably involves low-level event loop control
METRONOME = 0.5

# #########################################################################

# Set up accelerometer and magnetometer
i2c = busio.I2C(board.SCL, board.SDA)
accel = adafruit_lsm303_accel.LSM303_Accel(i2c)
mag = adafruit_lsm303dlh_mag.LSM303DLH_Mag(i2c)

# Set up GPS
# This is supposed to run on RasPi--therefore use pyserial library for uart access
# I'm using built-in UART on RasPi, so device name /dev/ttyS0 (teletype serial 0)
uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=3000)
gps = adafruit_gps.GPS(uart)
# From Adafruit:
#   Initialize the GPS module by changing what data it sends and at what rate.
#   These are NMEA extensions for PMTK_314_SET_NMEA_OUTPUT and
#   PMTK_220_SET_NMEA_UPDATERATE but you can send anything from here to adjust
#   the GPS module behavior:
#     https://cdn-shop.adafruit.com/datasheets/PMTK_A11.pdf
#   Turn on the basic GGA and RMC info
gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
#   Set update rate to once a second (1hz)
gps.send_command(b'PMTK220,1000')


# Set up continuous servo
GPIO.setmode(GPIO.BCM)
pwm_pin = 12
GPIO.setup(pwm_pin, GPIO.OUT)
pwm = GPIO.PWM(pwm_pin, 50) #Channel, frequency
pwm.start(SERVO_NEUTRAL)


# Global values
FWD_AZMT = 0
#GOBBLE_SEMAPHORE = 1 #Not using this


async def conductor():
    # Using connect() as context manager ensures the socket gets closed afterwards
    async with websockets.connect(PAOLOSERVER_WSADDR) as websocket:
        try:
            while True:
                await asyncio.gather(
                          find_where_to_point(websocket),
                          get_the_pointer_there(),
                          gobbler(websocket),
                      )
        except KeyboardInterrupt:
            print("Keyboard interrupt")
            pwm.stop()
            GPIO.cleanup()
            print("GPIO cleanup done")

async def find_where_to_point(websocket):
    """
    - Read own GPS
    - Go read the websocket and get P's location
    - Calculate forward azimuth
    """
    global FWD_AZMT

    # Where am I?
    gps.update()
    if gps.has_fix:
        my_lat = gps.latitude
        my_lng = gps.longitude
    else:
        print("GPS waiting for fix... Cannot obtain forward azimuth.")
        if not TESTMODE:
            return

    # Print GPS info
    #timestring = 'Fix at {}/{}/{} {:02}:{:02}:{:02}'.format(
    #    gps.timestamp_utc.tm_mon,   # Grab parts of the time from the
    #    gps.timestamp_utc.tm_mday,  # struct_time object that holds
    #    gps.timestamp_utc.tm_year,  # the fix time.  Note you might
    #    gps.timestamp_utc.tm_hour,  # not get all data like year, day,
    #    gps.timestamp_utc.tm_min,   # month!
    #    gps.timestamp_utc.tm_sec
    #)
    #print('Timestamp: {}'.format(timestring))
    #print('Latitude: {0:.6f} degrees'.format(gps.latitude))
    #print('Longitude: {0:.6f} degrees'.format(gps.longitude))

    if TESTMODE:
        print("TEST MODE ON: Faking Z location")
        my_lat = TEST_Z_LAT
        my_lng = TEST_Z_LNG

    # Where is Paolo?
    try:
        msg = await asyncio.wait_for(websocket.recv(), timeout=1)
        locdata = json.loads(msg)
        p_lat = locdata["coords"]["latitude"]
        p_lng = locdata["coords"]["longitude"]
        p_time = locdata["timestamp"]
        print(f"Received from Pserver:")
        print(f"    LAT {p_lat}")
        print(f"    LNG {p_lng}")
        print(f"    TIME {p_time}")
    except asyncio.TimeoutError:
        print("Timed out waiting for info on P location... Cannot obtain fwd azimuth.")
        if not TESTMODE:
            return
    except Exception as e:
        print(f"Error fetching P location: {e}")
        if not TESTMODE:
           return

    if TESTMODE:
        print("TEST MODE ON: Faking P location")
        p_lat = TEST_P_LAT
        p_lng = TEST_P_LNG

    # Forward azimuth
    # https://www.movable-type.co.uk/scripts/latlong.html
    fr_lat_r = math.radians(p_lat)
    fr_long_r = math.radians(p_lng)
    my_lat_r = math.radians(my_lat)
    my_long_r = math.radians(my_lng)
    fwd_azimuth = math.degrees(math.atan2(
        math.sin(fr_long_r - my_long_r) * math.cos(fr_lat_r),
        math.cos(my_lat_r) * math.sin(fr_lat_r)
        - math.sin(my_lat_r) * math.cos(fr_lat_r)
        * math.cos(fr_long_r-my_long_r)
    ))
    fwd_azimuth = 360 + fwd_azimuth if fwd_azimuth < 0 else fwd_azimuth
    print("Forward azimuth: {0:.6f} degrees".format(fwd_azimuth))

    FWD_AZMT = fwd_azimuth


async def get_the_pointer_there():
    """
    - Figure out where we are currently pointing (read acc/mag)
    - Calculate diff with forward azimuth
    - Turn the pointer
    """
    if not FWD_AZMT:
        print(f"Not moving ptr: No fwd azimuth avbl (or it is precisely zero yay!).")
        return

    acc_x, acc_y, acc_z = accel.acceleration # m/s^2
    mag_x, mag_y, mag_z = mag.magnetic # micro-Teslas
    #print('Acceleration (m/s^2): ({0:10.3f}, {1:10.3f}, {2:10.3f})'.format(acc_x, acc_y, acc_z))
    #print('Magnetometer (mcr-T): ({0:10.3f}, {1:10.3f}, {2:10.3f})'.format(mag_x, mag_y, mag_z))
    acc_norm = math.sqrt(acc_x * acc_x + acc_y * acc_y + acc_z * acc_z)
    pitch = math.asin(acc_x/acc_norm)
    roll =  math.asin(acc_y/acc_norm)
    #print('Pitch  : {}'.format(math.degrees(pitch)))
    #print('Roll   : {}'.format(math.degrees(roll)))
    # Could normalize mag vals as above but ehhh
    # Tilt-compensated magnetic sensor measurements
    tilt_mag_x = mag_x * math.cos(pitch) - mag_z * math.sin(pitch)
    tilt_mag_y = mag_y * math.cos(roll) - mag_z * math.sin(roll)
    #print('Tilt-comp mag       : ({0:10.3f}, {1:10.3f})'.format(tilt_mag_x, tilt_mag_y))
    heading = math.degrees(math.atan2(tilt_mag_y, tilt_mag_x))
    heading = 360 + heading if heading < 0 else heading
    print('Heading: {}'.format(heading))

    # Difference
    diff = FWD_AZMT - heading
    diff = diff % 360
    diff = diff - 360 if diff > 180 else diff
    print("Diff: {0:.6f} degrees".format(diff))

    # Move the pointer
    if diff < 0 - TOLERANCE:
        print("Go anti-clockwise!")
        pwm.ChangeDutyCycle(SERVO_ANTICLOCKWISE)
        await asyncio.sleep(SERVO_MOVE_TIME)
        pwm.ChangeDutyCycle(SERVO_NEUTRAL)
    elif diff > 0 + TOLERANCE:
        print("Go clockwise!")
        pwm.ChangeDutyCycle(SERVO_CLOCKWISE)
        await asyncio.sleep(SERVO_MOVE_TIME)
        pwm.ChangeDutyCycle(SERVO_NEUTRAL)
    else:
        print("You're in range... FOLLOW THAT ARROWWWWWWW")
        pwm.ChangeDutyCycle(SERVO_NEUTRAL)
        await asyncio.sleep(SERVO_MOVE_TIME)


async def gobbler(websocket):
    """ Gobble up the Paolo-GPS websocket stream (so we can keep up) """
    #print("Gobbler: " + str(time.monotonic()))
    stop = time.monotonic() + METRONOME
    while time.monotonic() < stop:
        try:
            await asyncio.wait_for(websocket.recv(), timeout=0.01)
        except:
            pass

asyncio.run(conductor())
