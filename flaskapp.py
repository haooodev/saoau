#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Simplest always online auto-update web application demo with flask.
Usage:
    1. Export an environment variable called AUTO_UPDATE_URL
    (like http://127.0.0.1:8000/update.tar.gz), which locates to a new version
    web app within a gzip compressed tarball.
    2. Copy this file elsewhere and make some changes, for instance add a new
    URL or change the index greeting world to 'Hello World'.
    3. Make this executable and run it via /some/path/to/flaskapp.py
    4. As it started, it will spawn 3 process, the parent, web, update. The
    parent just monitor its children and respawn them whenever as needed.
    Inspect it via:
        ``ps -ef | grep flaskapp``
    5. Archive the modified/updated version flaskapp.py like this:
        ``tar czf update.tar.gz flaskapp.py``
    6.Open another terminal and navigate to the created tarball and start a
    simple http server using python which will listen on localhost 8000:
        ``python3 -m http.server``  # for python3
        ``python2 -m SimpleHTTPServer ``  # for 
    7.As soon as you see file downloaded output on the simple server screen
    interupt it quickly or the just updated web app can reach the url and will
    think there is a new version again then download, start new version before
    kill itself.
'''

import os
import tarfile
import signal
import sys
import time
import subprocess

import urllib
if getattr(urllib, 'urlretrieve', None):
    native_urlretrieve = urllib.urlretrieve
else:
    from urllib.request import urlretrieve as native_urlretrieve

from flask import Flask

__version__ = (0, 0, 1)


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
APP_NAME = os.path.join(BASE_DIR, 'flaskapp.py')

UPDATE_TEMP_NAME = os.path.join(BASE_DIR, 'updat-temp.tar.gz')
UPDATE_URL = os.environ.get('AUTO_UPDATE_URL')
UPDATE_CHECK_INTERVAL = 5  # in seconds

app = Flask(__name__)


@app.route('/')
def index():
    return 'Hello World'

@app.route('/test/')
def cal(num):
    raise Exception()


def auto_update(url):
    pid = os.fork()
    if pid:
        return pid
    time.sleep(UPDATE_CHECK_INTERVAL)  # magically sleep
    temp_filename = os.path.join(BASE_DIR, UPDATE_TEMP_NAME)
    if os.path.exists(temp_filename) and os.path.isfile(temp_filename):
        os.remove(temp_filename)
    while 1:
        try:
            native_urlretrieve(url, temp_filename)
        except IOError as exc:
            time.sleep(UPDATE_CHECK_INTERVAL)
            continue

        os.remove(APP_NAME)
        new_version = tarfile.open(temp_filename, 'r:gz')
        new_version.extractall(BASE_DIR)
        subprocess.Popen('', executable=APP_NAME)
        sys.exit()


def web():
    pid = os.fork()
    if pid:
        return pid
    else:
        app.run('', port=9999)


def main():
    pid = os.fork()
    if pid:
        sys.exit()
    else:
        web_pid = None
        update_pid = None
        while True:
            if web_pid and update_pid:
                pid, status = os.wait()
                if pid == web_pid:
                    web_pid = None
                    
                if pid == update_pid:
                    if status == 0:
                        try:
                            os.kill(web_pid, signal.SIGKILL)
                        except OSError as exc:
                            pass
                        break
                    else:
                        update_pid = None
            else:
                if not web_pid:
                    web_pid = web()
                if not update_pid:
                    update_pid = auto_update(UPDATE_URL)


if __name__ == '__main__':
    main()
