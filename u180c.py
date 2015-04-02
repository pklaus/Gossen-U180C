#!/usr/bin/env python

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import logging
import argparse
from datetime import datetime as dt
import time
import sys

#Parameter               func.code  Register /IEEE   Unit
#                                Sign            Bytes
#
#V1   L-N voltage phase 1    03/04   0x0000 0x1000 2   mV
#V2   L-N voltage phase 2    03/04   0x0002 0x1002 2   mV
#V3   L-N voltage phase 3    03/04   0x0004 0x1004 2   mV
#V12  L-L voltage line 12    03/04   0x0006 0x1006 2   mV
#V23  L-L voltage line 23    03/04   0x0008 0x1008 2   mV
#V31  L-L voltage line 31    03/04   0x000A 0x100A 2   mV
#V∑   System voltage         03/04   0x000C 0x100C 2   mV
#A1   Phase 1 current        03/04 X 0x000E 0x100E 2   mA
#A2   Phase 2 current        03/04 X 0x0010 0x1010 2   mA
#A3   Phase 3 current        03/04 X 0x0012 0x1012 2   mA
#AN   Neutral current        03/04 X 0x0014 0x1014 2   mA
#A∑   System current         03/04 X 0x0016 0x1016 2   mA
#PF1  Phase 1 power factor   03/04 X 0x0018 0x1018 2    -
#PF2  Phase 2 power factor   03/04 X 0x0019 0x101A 2    -
#PF3  Phase 3 power factor   03/04 X 0x001A 0x101C 2    -
#PF∑  System power factor    03/04 X 0x001B 0x101E 2    -
#P1   Phase 1 active power   03/04 X 0x001C 0x1020 2   mW
#P2   Phase 2 active power   03/04 X 0x001F 0x1022 2   mW
#P3   Phase 3 active power   03/04 X 0x0022 0x1024 2   mW
#P∑   System active power    03/04 X 0x0025 0x1026 2   mW
#S1   Phase 1 apparent power 03/04 X 0x0028 0x1028 2  mVA
#S2   Phase 2 apparent power 03/04 X 0x002B 0x102A 2  mVA
#S3   Phase 3 apparent power 03/04 X 0x002E 0x102C 2  mVA
#S∑   System apparent power  03/04 X 0x0031 0x102E 2  mVA
#Q1   Phase 1 reactive power 03/04 X 0x0034 0x1030 2 mvar
#Q2   Phase 2 reactive power 03/04 X 0x0037 0x1032 2 mvar
#Q3   Phase 3 reactive power 03/04 X 0x003A 0x1034 2 mvar
#Q∑   System reactive power  03/04 X 0x003D 0x1036 2 mvar
#F    Frequency              03/04   0x0040 0x1038 2  mHz
#Phase sequence              03/04   0x0041 0x103A 2

RR = {
  'V1' :  ('L-N voltage phase 1',    False, 0x0000, 2, 0x1000, 2,   'mV'),
  'V2' :  ('L-N voltage phase 2',    False, 0x0002, 2, 0x1002, 2,   'mV'),
  'V3' :  ('L-N voltage phase 3',    False, 0x0004, 2, 0x1004, 2,   'mV'),
  'V12':  ('L-L voltage line 12',    False, 0x0006, 2, 0x1006, 2,   'mV'),
  'V23':  ('L-L voltage line 23',    False, 0x0008, 2, 0x1008, 2,   'mV'),
  'V31':  ('L-L voltage line 31',    False, 0x000A, 2, 0x100A, 2,   'mV'),
  'V∑' :  ('System voltage',         False, 0x000C, 2, 0x100C, 2,   'mV'),
  'A1' :  ('Phase 1 current',        True,  0x000E, 2, 0x100E, 2,   'mA'),
  'A2' :  ('Phase 2 current',        True,  0x0010, 2, 0x1010, 2,   'mA'),
  'A3' :  ('Phase 3 current',        True,  0x0012, 2, 0x1012, 2,   'mA'),
  'AN' :  ('Neutral current',        True,  0x0014, 2, 0x1014, 2,   'mA'),
  'A∑' :  ('System current',         True,  0x0016, 2, 0x1016, 2,   'mA'),
  'PF1':  ('Phase 1 power factor',   True,  0x0018, 1, 0x1018, 2,   None),
  'PF2':  ('Phase 2 power factor',   True,  0x0019, 1, 0x101A, 2,   None),
  'PF3':  ('Phase 3 power factor',   True,  0x001A, 1, 0x101C, 2,   None),
  'PF∑':  ('System power factor',    True,  0x001B, 1, 0x101E, 2,   None),
  'P1' :  ('Phase 1 active power',   True,  0x001C, 3, 0x1020, 2,   'mW'),
  'P2' :  ('Phase 2 active power',   True,  0x001F, 3, 0x1022, 2,   'mW'),
  'P3' :  ('Phase 3 active power',   True,  0x0022, 3, 0x1024, 2,   'mW'),
  'P∑' :  ('System active power',    True,  0x0025, 3, 0x1026, 2,   'mW'),
  'S1' :  ('Phase 1 apparent power', True,  0x0028, 3, 0x1028, 2,  'mVA'),
  'S2' :  ('Phase 2 apparent power', True,  0x002B, 3, 0x102A, 2,  'mVA'),
  'S3' :  ('Phase 3 apparent power', True,  0x002E, 3, 0x102C, 2,  'mVA'),
  'S∑' :  ('System apparent power',  True,  0x0031, 3, 0x102E, 2,  'mVA'),
  'Q1' :  ('Phase 1 reactive power', True,  0x0034, 3, 0x1030, 2, 'mvar'),
  'Q2' :  ('Phase 2 reactive power', True,  0x0037, 3, 0x1032, 2, 'mvar'),
  'Q3' :  ('Phase 3 reactive power', True,  0x003A, 3, 0x1034, 2, 'mvar'),
  'Q∑' :  ('System reactive power',  True,  0x003D, 3, 0x1036, 2, 'mvar'),
  'F'  :  ('Frequency',              False, 0x0040, 1, 0x1038, 2,  'mHz'),
  'Phase sequence': ('',             False, 0x0041, 1, 0x103A, 2,   None)
}

RR_ORDER = [
  'V1', 'V2', 'V3', 'V12', 'V23', 'V31', 'V∑', 'A1', 'A2', 'A3', 'AN', 'A∑',
  'PF1', 'PF2', 'PF3', 'PF∑', 'P1', 'P2', 'P3', 'P∑',
  'S1', 'S2', 'S3', 'S∑', 'Q1', 'Q2', 'Q3', 'Q∑', 'F', 'Phase sequence',
]

def convert_registers(reg_dict):
    ret_dict = dict()
    for reg_code in reg_dict:
        tpl = reg_dict[reg_code]
        register = {
          'code': reg_code,
          'descr': tpl[0],
          'sign': tpl[1],
          'reg_int_start_addr': tpl[2],
          'reg_int_num_words': tpl[3],
          'reg_ieee_start_addr': tpl[4],
          'reg_ieee_num_words': tpl[5],
          'unit': tpl[6],
        }
        ret_dict[reg_code] = register
    return ret_dict

RRD = convert_registers(RR)


class U180C(object):

    RR = RR
    RRD = RRD
    RR_ORDER = RR_ORDER

    def __init__(self, host, port=502):
        self.host = host
        self.port = port
        self.client = ModbusClient(host, port=502)
        self.client.connect()

    def read_all_at_once(self):
        num_words = sum([RRD[key]['reg_int_num_words'] for key in RRD])
        rr = self.client.read_input_registers(0x0000, num_words)
        assert(rr.function_code < 0x80)
        assert(len(rr.registers) == num_words)
        pos = 0
        for reg_code in U180C.RR_ORDER:
            reg = U180C.RRD[reg_code]
            val_words = rr.registers[pos:pos+reg['reg_int_num_words']]
            pos += reg['reg_int_num_words']
            if reg['sign']:
                sign = (val_words[0] & 0x8000) >> 15
                val_words[0] = val_words[0] & ~(0x8000)
            else:
                sign = 0
            if sign == 0: sign_factor = 1
            if sign == 1: sign_factor = -1
            if reg['reg_int_num_words'] == 1:
                value = val_words[0]
            if reg['reg_int_num_words'] == 2:
                value = (val_words[0] << 16) | val_words[1]
            if reg['reg_int_num_words'] == 3:
                value = (val_words[0] << 32) | (val_words[1] << 16) | val_words[2]
            value = sign_factor * value
            print("{code} {descr}:".format(**reg))
            if reg['unit']: print("{value} {unit}".format(value=value, unit=reg['unit']))
            else: print("{value}".format(value=value))


    def read_all(self):
        for reg_code in U180C.RR_ORDER:
            reg = U180C.RRD[reg_code]
            rr = self.client.read_input_registers(reg['reg_int_start_addr'], reg['reg_int_num_words'])
            assert(rr.function_code < 0x80)
            assert(len(rr.registers) == reg['reg_int_num_words'])
            val_words = rr.registers.copy()
            if reg['sign']:
                sign = (val_words[0] & 0x8000) >> 15
                val_words[0] = val_words[0] & ~(0x8000)
            else:
                sign = 0
            if sign == 0: sign_factor = 1
            if sign == 1: sign_factor = -1
            if reg['reg_int_num_words'] == 1:
                value = val_words[0]
            if reg['reg_int_num_words'] == 2:
                value = (val_words[0] << 16) | val_words[1]
            if reg['reg_int_num_words'] == 3:
                value = (val_words[0] << 32) | (val_words[1] << 16) | val_words[2]
            value = sign_factor * value
            print("{code} {descr}:".format(**reg))
            if reg['unit']: print("{value} {unit}".format(value=value, unit=reg['unit']))
            else: print("{value}".format(value=value))

    def close(self):
        self.client.close()

def main():
    parser = argparse.ArgumentParser(description='Talk to a Gossen U180C via Modbus TCP')
    parser.add_argument('host', help='The Modbus TCP host to connect to')
    parser.add_argument('--debug', help='Enable debugging output')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig()
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)

    u180c = U180C(args.host)

    try:
        while True:
            u180c.read_all_at_once()
            print(dt.now())
            sys.stdout.flush()
            time.sleep(0.2)
    except KeyboardInterrupt:
        print('[Ctrl]-[c] pressed. Exiting...')

    u180c.close()

if __name__ == "__main__":
    main()
