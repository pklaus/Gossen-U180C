#!/usr/bin/env python

import logging
import argparse
from datetime import datetime as dt
import time

from u180c import *

def main():
    parser = argparse.ArgumentParser(description='Download / clear the logfile of a Gossen U180C via HTTP')
    parser.add_argument('host', help="The U180C LAN Interface to connect to like 'http://ip-or-host'.")
    parser.add_argument('--username', default='admin', help='The HTTP username (if needed)')
    parser.add_argument('--password', default='admin', help='The HTTP password (if needed)')
    parser.add_argument('--download', action='store_true', help='Download the logfile.')
    parser.add_argument('--clear', action='store_true', help='Clear the logfile.')
    parser.add_argument('--enable', action='store_true', help='Enable logging.')
    parser.add_argument('--disable', action='store_true', help='Disable logging.')
    args = parser.parse_args()

    try:
        u180c = U180CWeb(args.host)
    except U180CException as e:
        parser.error('Could not connect to host ' + args.host + '\n' + str(e))

    try:
        if not u180c.authenticate(args.username, args.password):
            parser.error('Wrong username/password (Or, you need to logout the user in your Browser).')

        if args.download:
            first_yield = True
            for status in u180c.download_csv():
                if first_yield:
                    first_yield = False
                    print('Saving CSV file as {}'.format(status))
                    status = 0
                print('  {:4.1f} MiB downloaded'.format(status/1024.**2), end='\r')
        if args.clear:
            print('Clearing log now.')
            # Checking / ensuring authentication once more
            u180c.authenticate(args.username, args.password)
            u180c.clear_csv()
        if args.enable:
            print('Enabling logging.')
            u180c.enable_logging()
        if args.disable:
            print('Disabling logging.')
            u180c.disable_logging()
    finally:
        u180c.close()

if __name__ == "__main__":
    main()

