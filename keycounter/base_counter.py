#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
import os
import threading
import requests
import time

from .storage import CountDataStorage

__version__ = '0.0.6'

KEY_COUNT = 0
# API_URL = 'http://127.0.0.1:5000/data'
API_URL = 'http://116.55.233.138:5000/data'


class ApiRequest(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        with open(os.path.expanduser('~') + '\\keycount.ini', 'r') as confile:
            self.user_info = {
                "username": confile.readline().strip(),
                "password": confile.readline().strip()
            }

    def run(self):
        global KEY_COUNT
        while True:
            self.send_data(KEY_COUNT)
            time.sleep(2)

    # send key count
    def send_data(self, key_count):
        self.user_info.update({'count': key_count})
        result = requests.post(API_URL, json=self.user_info)


class BaseKeyCounter(object):
    '''Base skeleton for a KeyCounter instance'''

    name = 'KeyCounter'
    version = __version__

    def __init__(self):
        '''
        Init the counter.
        - Load config
        - Setup UI
        - Start event loop
        '''
        self.key_count = 0
        self.daily_reset = False

        self.today = datetime.now().day
        self.setup_storage()

    def setup_storage(self):
        self.storage = CountDataStorage()

    def log(self, *args, **kwargs):
        '''Logging'''
        logging.debug(*args, **kwargs)

    def load_config(self):
        '''Load configuration from storage'''
        raise NotImplementedError(u'Should be implemented in subclass')

    def save_config(self):
        '''Save configuration to storage'''
        raise NotImplementedError(u'Should be implemented in subclass')

    def start(self):
        '''Start the event loop'''
        self.key_count = self.load_data(datetime.now())
        ApiRequest().start()

    def stop(self):
        '''Stop the event loop and save current count'''
        self.save_data(datetime.now(), self.key_count)
        self.storage.export()

    def do_daily_reset(self):
        '''Reset count and start a new day'''
        self.log('Perform daily reset')
        yesterday_count = self.key_count - 1
        yesterday = datetime.now() - timedelta(1)
        self.save_data(yesterday, yesterday_count)
        self.storage.export()
        self.key_count -= yesterday_count
        if self.key_count < 0:
            self.key_count = 0
        self.update_ui()

    def load_data(self, day):
        '''Load count data for specific day'''
        return self.storage.get(day)

    def save_data(self, day, count):
        '''Save count data for specific day'''
        self.storage.save(day, count)

    def check_daily_reset(self):
        '''Check whether it's time to do daily reset'''
        now = datetime.now()
        if now.day != self.today:
            self.do_daily_reset()
            self.today = now.day

    def update_count(self):
        '''Update count and reflect the change to UI'''
        global KEY_COUNT
        self.key_count += 1
        KEY_COUNT += 1
        self.update_ui()

    def update_ui(self):
        '''Update user interface'''
        raise NotImplementedError(u'Should be implemented in subclass')

    def handle_keyevent(self, _):
        '''
        Handle key event, properly change count and UI.
        This method should be properly registered to OS's KeyUp event.
        '''
        self.update_count()
        if self.daily_reset:
            self.check_daily_reset()
