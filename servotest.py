# Use this noodle to sanity check PWM generally
# Stick the signal pin on pin_pwm (so 12)
# $ python3 servotest.py
# Probably you will comment out the first block

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
pin_pwm = 12
GPIO.setup(pin_pwm, GPIO.OUT)
pwm = GPIO.PWM(pin_pwm, 50) # channel, frequency

# Your CR servo is FS90R
# 1/50=0.02s=20ms
# STOP = 1.5ms pulse = dc7.5
# FULL SPD FWD = 2ms pulse = dc10
# FULL SPD BCK = 1ms pulse = dc5

print("Starting up with dc 6.0")
pwm.start(6.0)
time.sleep(1)
print("OK")

# Probably comment this out
try:
    dc = 0.0
    while True:
        while dc < 10.0:
            dc += 0.5
            print(dc)
            pwm.ChangeDutyCycle(dc)
            time.sleep(1.0)
        while dc > 5.0:
            dc -= 0.5
            print(dc)
            pwm.ChangeDutyCycle(dc)
            time.sleep(1.0)
except KeyboardInterrupt:
    pass
    #pwm.stop()
    #GPIO.cleanup()

# Mainly use this
try:
    while True:
        d = float(input('duty cycle 5 to 10: '))
        pwm.ChangeDutyCycle(d)
except KeyboardInterrupt:
    pwm.stop()
    GPIO.cleanup()
