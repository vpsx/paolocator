#!/bin/sh
#omegad this is called a shebang
cd /home/pi/paolocator
echo "Whoa it worked" >> worked.txt
echo $(whoami) >> worked.txt
# That's root.
#su - pi -c "echo $(whoami) >> worked.txt"
#su - pi -c "/home/pi/.local/bin/pipenv run python /home/pi/paolocator/main.py"
echo $(whoami) >> worked.txt
#/usr/bin/pip install pipenv
# vvv Need this to run the first time but let's see if thereafter
#/home/pi/.local/bin/pipenv install
/home/pi/.local/bin/pipenv run python /home/pi/paolocator/main.py
#/home/pi/.local/bin/pipenv run python /home/pi/paolocator/nwtest.py
#/home/pi/.local/bin/pipenv run echo "Trala" > worked.txt
#/home/pi/.local/bin/pipenv run python main.py
# BLAAAAAAAAAAAAAAAAAARHG
