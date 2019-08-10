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
