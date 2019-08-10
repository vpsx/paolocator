# paolocator
point at paolo

### Setup log

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

### Incomplete list of useful links

github.com/adafruit/Adafruit_CircuitPython_GPS
circuitpython.readthedocs.io/projects/gps/en/latest/
learn.adafruit.com/circuitpython-on-raspberrypi-linux/uart-serial
learn.adafruit.com/adafruit-ultimate-gps/circuitpython-parsing


### Physical build log

Paolocator uses a Raspberry Pi Zero W with the Adafruit Ultimate GPS module.

#### GPS

This setup uses the Pi's built-in UART for GPS serial communication.

Wire up GPS module to Pi UART:
- GPS VIN to pi 3.3V or 5V
- GPS GND to pi GND
- GPS TX to pi RX
- GPS RX to pi TX

Enable UART via `sudo raspi config`; reboot.

See the CircuitPython section of Adafruit's Ultimate GPS tutorial for more details.
