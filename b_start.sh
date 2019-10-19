#!/bin/sh
# This is started by systemd paolocator.service and run as root

cd /home/pi/paolocator

# These two need to be run the first time but not thereafter
# ...so if you update the Pipfile... uncomment, run, recomment...
# derp.
# One day maybe I will know why, but it has to do with namespaces
# ...probably
#/usr/bin/pip install pipenv
#/home/pi/.local/bin/pipenv install

# Actual thing that you want
/home/pi/.local/bin/pipenv run python /home/pi/paolocator/b_only_gps.py

# For when you are troubleshooting outside
#/home/pi/.local/bin/pipenv run python /home/pi/paolocator/nwtest.py
