import time
import math
import board
import busio
import adafruit_lsm303_accel
import adafruit_lsm303dlh_mag

# Yay accelerometer and magnetometer!
i2c = busio.I2C(board.SCL, board.SDA)
accel = adafruit_lsm303_accel.LSM303_Accel(i2c)
mag = adafruit_lsm303dlh_mag.LSM303DLH_Mag(i2c)


last_acm_print = time.monotonic()
heading = 0
while True:
    current = time.monotonic()
    # Every second print out current accel/mag readings.
    if current - last_acm_print >= 1.0:
        last_acm_print = current
        acc_x, acc_y, acc_z = accel.acceleration   # m/s^2
        mag_x, mag_y, mag_z = mag.magnetic         # micro-Teslas

        #print('Acceleration (m/s^2): ({0:10.3f}, {1:10.3f}, {2:10.3f})'.format(acc_x, acc_y, acc_z))
        #print('Magnetometer (mcr-T): ({0:10.3f}, {1:10.3f}, {2:10.3f})'.format(mag_x, mag_y, mag_z))

        acc_norm = math.sqrt(acc_x * acc_x + acc_y * acc_y + acc_z * acc_z)
        pitch = math.asin(acc_x/acc_norm)
        roll =  math.asin(acc_y/acc_norm)
        print('Pitch  : {}'.format(math.degrees(pitch)))
        print('Roll   : {}'.format(math.degrees(roll)))

        # Tilt compensated magnetic sensor measurements
        tilt_mag_x = mag_x * math.cos(pitch) - mag_z * math.sin(pitch)
        tilt_mag_y = mag_y * math.cos(roll) - mag_z * math.sin(roll)
        print('Tilt-comp mag       : ({0:10.3f}, {1:10.3f})'.format(tilt_mag_x, tilt_mag_y))

        heading = math.degrees(math.atan2(tilt_mag_y, tilt_mag_x))
        heading = 360 + heading if heading < 0 else heading
        print('Heading: {}'.format(heading))

        vanillaheading = math.degrees(math.atan2(mag_y, mag_x))
        vanillaheading = 360 + vanillaheading if vanillaheading < 0 else vanillaheading
        print('Vanilla Heading: {}'.format(vanillaheading))
        print('\n')
