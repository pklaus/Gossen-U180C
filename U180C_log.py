#!/usr/bin/env python

import logging
import argparse
from datetime import datetime as dt
import time

from u180c import *

def main():
    parser = argparse.ArgumentParser(description='Talk to a Gossen U180C via Modbus TCP or HTTP')
    parser.add_argument('host', help="The U180C LAN Interface to connect to. State its IP address for MODBUS TCP or 'http://ip-or-host' for HTTP.")
    parser.add_argument('measures', metavar='MEASURE', help='Measures to be logged. List all possible with --list.', nargs='*', default='all')
    parser.add_argument('--debug', action='store_true', help='Enable debugging output')
    parser.add_argument('--filter', help="Filter output values. State 1,2,3 for phases or 'sys' for system.")
    parser.add_argument('--list', action='store_true', help="List all possible measures.")
    parser.add_argument('--style', choices=['csv', 'plain'], default='plain', help='The output style')
    parser.add_argument('--username', default='admin', help='The HTTP username (if needed)')
    parser.add_argument('--password', default='admin', help='The HTTP password (if needed)')
    parser.add_argument('--flush', action='store_true', help='Set this flag if you want the output to be flushed after each line.')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig()
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)

    try:
        u180c = U180CFactory(args.host)
    except U180CException as e:
        parser.error('Could not connect to host ' + args.host + '\n' + str(e))

    try:
        if type(u180c) is U180CWeb:
            if not u180c.authenticate(args.username, args.password):
                parser.error('Wrong username/password (Or, you need to logout the user in your Browser).')

        coils = u180c.read_coils()
        for coil_val in coils:
            coil = coil_val[0]
            value = coil_val[1]
            if value:
                sys.stderr.write("Warning: Coil {code} ({descr}) is ON!\n".format(**coil))

        #regs_values = u180c.counters_balance
        #for reg_value in regs_values:
        #    if args.filter:
        #        reg_def = reg_value[0]
        #        if reg_def['related_to'] == args.filter:
        #            U180C.print_register(*reg_value)
        #    else:
        #        U180C.print_register(*reg_value)
        #sys.stdout.flush()

        styles = {
          'plain' : {
            'leading_cols': {'Date&Time': {} },
            'sep' : ' '
          },
          'csv'   : {
            'leading_cols': {'SN': {'code': 'serial'}, 'Date' : {}, 'Time': {} },
            'sep' : ' '
          },
        }

        #flat_measure_list = RR_LIST
        measure_lists = [REAL_TIME_LIST, COUNTER_LIST_TOTAL, COUNTER_LIST_TARIFF1, COUNTER_LIST_TARIFF2, PARTIAL_COUNTER_LIST, BALANCE_LIST]
        flat_measure_list = []
        list(map(flat_measure_list.extend, measure_lists))
        if args.style == 'plain':
            sep = ' '
        elif args.style == 'csv':
            sep = ';'

        if args.list:
            print("Possible measures:")
            for measure in flat_measure_list:
                print(measure)
            sys.exit(0)

        measures = []
        if args.measures == 'all':
            measures = [RR[key] for key in flat_measure_list]
        else:
            measures = []
            for measure in args.measures:
                try:
                    measure = int(measure)
                except:
                    pass
                measure_found = False
                for key in RR_LIST:
                    reg_def = RR[key]
                    if measure in (reg_def['api_no'], reg_def['code'], reg_def['csv_code']):
                        measures.append(reg_def)
                        measure_found = True
                        break
                if not measure_found:
                    parser.error('Measure {} is unknown.'.format(measure))

        date_format = []
        headers = []
        if args.style == 'csv':
            headers = ["Date", "Time"] + [m['csv_code'] for m in measures]
            date_format = ['%d/%m/%Y', '%H:%M:%S']
        elif args.style == 'plain':
            headers = ["Date&Time"] + [m['code'] for m in measures]
            date_format = ['%Y-%m-%dT%H:%M:%S']
        print(sep.join(headers))
        try:
            while True:
                readings = []
                regs_values = u180c.all_measures
                for measure in measures:
                    for reg_value in regs_values:
                        reg_def = reg_value[0]
                        if measure == reg_def:
                            readings.append(reg_value)
                line = ""
                line += sep.join([dt.now().strftime(df) for df in date_format])
                line += sep
                line += sep.join(['{:.3f}'.format(val) if type(val) == float else str(val) for rd, val in readings])
                #for rd, val in readings:
                #    if type(val) == float:
                #        line += "{:.3f}".format(val)
                #    else:
                #        line += "{}".format(val)
                #    line += sep
                print(line)
                if args.flush: sys.stdout.flush()
                time.sleep(4.7)
        except KeyboardInterrupt:
            sys.stderr.write('[Ctrl]-[c] pressed. Exiting...\n')
        except U180CException as e:
            sys.stderr.write('A problem occured: {}\n'.format(e))

    finally:
        u180c.close()

if __name__ == "__main__":
    main()

