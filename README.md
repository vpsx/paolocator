# paolocator
point at paolo

### Setup log

(This is just so I know... but obviously in theory just do `pipenv install` from lockfile)

```
$ pip install --user pipenv
$ export PATH=/home/pi/.local/bin:$PATH
$ export PIPENV_VENV_IN_PROJECT=1
$ pipenv install requests
$ pipenv run python main.py
```

Bleh, this landed me with python 2.7
Edit Pipfile to specify python 3. Next time try... something else...
```
$ pipenv --rm
$ pipenv --python 3
$ pipenv run python --version
$ pipenv install
$ pipenv run python main.py
```

```
pipenv install adafruit-circuitpython-gps
pipenv install adafruit_blinka
pipenv install pyserial
```

```
pipenv install adafruit-circuitpython-lsm303
```
_Not_ `pipenv install circuitpython-build-tools` followed by `pipenv run circuitpython-build-bundles blah`--this is ~insane and uncivilised~ actually not for Linux.

You must also `sudo raspi-config` - Interfacing Options - I2C - Enable.

### Incomplete list of useful links

github.com/adafruit/Adafruit_CircuitPython_GPS
circuitpython.readthedocs.io/projects/gps/en/latest/
learn.adafruit.com/circuitpython-on-raspberrypi-linux/uart-serial
learn.adafruit.com/adafruit-ultimate-gps/circuitpython-parsing


### Physical build log

Paolocator uses a Raspberry Pi Zero W with the Adafruit Ultimate GPS module.


#### Servo

CR servo, signal on pin 12, calibrated to 7.5 neutral.

#### GPS

This setup uses the Pi's built-in UART for GPS serial communication.

Wire up GPS module to Pi UART:
- GPS VIN to pi 3.3V or 5V
- GPS GND to pi GND
- GPS TX to pi RX
- GPS RX to pi TX

Enable UART via `sudo raspi config`; reboot.

See the CircuitPython section of Adafruit's Ultimate GPS tutorial for more details.

#### Compass (Accelerometer + Magnetometer)

This setup uses the LSM303, which uses I2C.

Wiring as expected: VIN to 3.3V or 5V; GND, SDA, SCL.

A note on MEMS magnetometers: You need to think conspiratorially about your compass, because legitimately everything will screw with your heading, including power banks. Do not set your breadboard on top of your power brick. Or your phone.



### Random stuff

configure network at `/etc/wpa_supplicant/wpa_supplicant.conf`

`ip neigh`!!


### Todo

investigate latency on paolocator-b: see fix timestamps while walking around. Compare local to GET
