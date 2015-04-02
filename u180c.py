#!/usr/bin/env python

import pymodbus.client.sync
import pymodbus.exceptions
import logging
import argparse
from datetime import datetime as dt
import time
import sys
import struct

# Readable Registers

RR_RAW = {

  # REAL-TIME VALUES
  'V1' :  ('L-N voltage phase 1',        1, False, 0x00, 2, 1000., 0x1000, 2,   'V'),
  'V2' :  ('L-N voltage phase 2',        2, False, 0x02, 2, 1000., 0x1002, 2,   'V'),
  'V3' :  ('L-N voltage phase 3',        3, False, 0x04, 2, 1000., 0x1004, 2,   'V'),
  'V12':  ('L-L voltage line 12',    [1,2], False, 0x06, 2, 1000., 0x1006, 2,   'V'),
  'V23':  ('L-L voltage line 23',    [2,3], False, 0x08, 2, 1000., 0x1008, 2,   'V'),
  'V31':  ('L-L voltage line 31',    [3,1], False, 0x0A, 2, 1000., 0x100A, 2,   'V'),
  'V∑' :  ('System voltage',         'sys', False, 0x0C, 2, 1000., 0x100C, 2,   'V'),
  'A1' :  ('Phase 1 current',            1, True,  0x0E, 2, 1000., 0x100E, 2,   'A'),
  'A2' :  ('Phase 2 current',            2, True,  0x10, 2, 1000., 0x1010, 2,   'A'),
  'A3' :  ('Phase 3 current',            3, True,  0x12, 2, 1000., 0x1012, 2,   'A'),
  'AN' :  ('Neutral current',        'sys', True,  0x14, 2, 1000., 0x1014, 2,   'A'),
  'A∑' :  ('System current',         'sys', True,  0x16, 2, 1000., 0x1016, 2,   'A'),
  'PF1':  ('Phase 1 power factor',       1, True,  0x18, 1, 1000., 0x1018, 2,  None),
  'PF2':  ('Phase 2 power factor',       2, True,  0x19, 1, 1000., 0x101A, 2,  None),
  'PF3':  ('Phase 3 power factor',       3, True,  0x1A, 1, 1000., 0x101C, 2,  None),
  'PF∑':  ('System power factor',    'sys', True,  0x1B, 1, 1000., 0x101E, 2,  None),
  'P1' :  ('Phase 1 active power',       1, True,  0x1C, 3, 1000., 0x1020, 2,   'W'),
  'P2' :  ('Phase 2 active power',       2, True,  0x1F, 3, 1000., 0x1022, 2,   'W'),
  'P3' :  ('Phase 3 active power',       3, True,  0x22, 3, 1000., 0x1024, 2,   'W'),
  'P∑' :  ('System active power',    'sys', True,  0x25, 3, 1000., 0x1026, 2,   'W'),
  'S1' :  ('Phase 1 apparent power',     1, True,  0x28, 3, 1000., 0x1028, 2,  'VA'),
  'S2' :  ('Phase 2 apparent power',     2, True,  0x2B, 3, 1000., 0x102A, 2,  'VA'),
  'S3' :  ('Phase 3 apparent power',     3, True,  0x2E, 3, 1000., 0x102C, 2,  'VA'),
  'S∑' :  ('System apparent power',  'sys', True,  0x31, 3, 1000., 0x102E, 2,  'VA'),
  'Q1' :  ('Phase 1 reactive power',     1, True,  0x34, 3, 1000., 0x1030, 2, 'var'),
  'Q2' :  ('Phase 2 reactive power',     2, True,  0x37, 3, 1000., 0x1032, 2, 'var'),
  'Q3' :  ('Phase 3 reactive power',     3, True,  0x3A, 3, 1000., 0x1034, 2, 'var'),
  'Q∑' :  ('System reactive power',  'sys', True,  0x3D, 3, 1000., 0x1036, 2, 'var'),
  'F'  :  ('Frequency',              'sys', False, 0x40, 1, 1000., 0x1038, 2,  'Hz'),
  'Phase sequence': ('',             'sys', False, 0x41, 1,     1, 0x103A, 2,  None),

  # COUNTER VALUES
  '+kWh1'     : ('Phase 1 imported active energy',               1, False, 0x100, 3, 10., 0x1100, 2,   'Wh'),
  '+kWh2'     : ('Phase 2 imported active energy',               2, False, 0x103, 3, 10., 0x1102, 2,   'Wh'),
  '+kWh3'     : ('Phase 3 imported active energy',               3, False, 0x106, 3, 10., 0x1104, 2,   'Wh'),
  '+kWh∑'     : ('System imported active energy',            'sys', False, 0x109, 3, 10., 0x1106, 2,   'Wh'),
  '-kWh1'     : ('Phase 1 exported active energy',               1, False, 0x10c, 3, 10., 0x1108, 2,   'Wh'),
  '-kWh2'     : ('Phase 2 exported active energy',               2, False, 0x10f, 3, 10., 0x110a, 2,   'Wh'),
  '-kWh3'     : ('Phase 3 exported active energy',               3, False, 0x112, 3, 10., 0x110c, 2,   'Wh'),
  '-kWh∑'     : ('System exported active energy',            'sys', False, 0x115, 3, 10., 0x110e, 2,   'Wh'),
  '+kVAh1-L'  : ('Phase 1 imported lagging apparent energy',     1, False, 0x118, 3, 10., 0x1110, 2,  'VAh'),
  '+kVAh2-L'  : ('Phase 2 imported lagging apparent energy',     2, False, 0x11b, 3, 10., 0x1112, 2,  'VAh'),
  '+kVAh3-L'  : ('Phase 3 imported lagging apparent energy',     3, False, 0x11e, 3, 10., 0x1114, 2,  'VAh'),
  '+kVAh∑-L'  : ('System imported lagging apparent energy',  'sys', False, 0x121, 3, 10., 0x1116, 2,  'VAh'),
  '-kVAh1-L'  : ('Phase 1 exported lagging apparent energy',     1, False, 0x124, 3, 10., 0x1118, 2,  'VAh'),
  '-kVAh2-L'  : ('Phase 2 exported lagging apparent energy',     2, False, 0x127, 3, 10., 0x111a, 2,  'VAh'),
  '-kVAh3-L'  : ('Phase 3 exported lagging apparent energy',     3, False, 0x12a, 3, 10., 0x111c, 2,  'VAh'),
  '-kVAh∑-L'  : ('System exported lagging apparent energy',  'sys', False, 0x12d, 3, 10., 0x111e, 2,  'VAh'),
  '+kVAh1-C'  : ('Phase 1 imported leading apparent energy',     1, False, 0x130, 3, 10., 0x1120, 2,  'VAh'),
  '+kVAh2-C'  : ('Phase 2 imported leading apparent energy',     2, False, 0x133, 3, 10., 0x1122, 2,  'VAh'),
  '+kVAh3-C'  : ('Phase 3 imported leading apparent energy',     3, False, 0x136, 3, 10., 0x1124, 2,  'VAh'),
  '+kVAh∑-C'  : ('System imported leading apparent energy',  'sys', False, 0x139, 3, 10., 0x1126, 2,  'VAh'),
  '-kVAh1-C'  : ('Phase 1 exported leading apparent energy',     1, False, 0x13c, 3, 10., 0x1128, 2,  'VAh'),
  '-kVAh2-C'  : ('Phase 2 exported leading apparent energy',     2, False, 0x13f, 3, 10., 0x112a, 2,  'VAh'),
  '-kVAh3-C'  : ('Phase 3 exported leading apparent energy',     3, False, 0x142, 3, 10., 0x112c, 2,  'VAh'),
  '-kVAh∑-C'  : ('System exported leading apparent energy',  'sys', False, 0x145, 3, 10., 0x112e, 2,  'VAh'),
  '+kvarh1-L' : ('Phase 1 imported lagging reactive energy',     1, False, 0x148, 3, 10., 0x1130, 2, 'varh'),
  '+kvarh2-L' : ('Phase 2 imported lagging reactive energy',     2, False, 0x14b, 3, 10., 0x1132, 2, 'varh'),
  '+kvarh3-L' : ('Phase 3 imported lagging reactive energy',     3, False, 0x14e, 3, 10., 0x1134, 2, 'varh'),
  '+kvarh∑-L' : ('System imported lagging reactive energy',  'sys', False, 0x151, 3, 10., 0x1136, 2, 'varh'),
  '-kvarh1-L' : ('Phase 1 exported lagging reactive energy',     1, False, 0x154, 3, 10., 0x1138, 2, 'varh'),
  '-kvarh2-L' : ('Phase 2 exported lagging reactive energy',     2, False, 0x157, 3, 10., 0x113a, 2, 'varh'),
  '-kvarh3-L' : ('Phase 3 exported lagging reactive energy',     3, False, 0x15a, 3, 10., 0x113c, 2, 'varh'),
  '-kvarh∑-L' : ('System exported lagging reactive energy',  'sys', False, 0x15d, 3, 10., 0x113e, 2, 'varh'),
  '+kvarh1-C' : ('Phase 1 imported leading reactive energy',     1, False, 0x160, 3, 10., 0x1140, 2, 'varh'),
  '+kvarh2-C' : ('Phase 2 imported leading reactive energy',     2, False, 0x163, 3, 10., 0x1142, 2, 'varh'),
  '+kvarh3-C' : ('Phase 3 imported leading reactive energy',     3, False, 0x166, 3, 10., 0x1144, 2, 'varh'),
  '+kvarh∑-C' : ('System imported leading reactive energy',  'sys', False, 0x169, 3, 10., 0x1146, 2, 'varh'),
  '-kvarh1-C' : ('Phase 1 exported leading reactive energy',     1, False, 0x16c, 3, 10., 0x1148, 2, 'varh'),
  '-kvarh2-C' : ('Phase 2 exported leading reactive energy',     2, False, 0x16f, 3, 10., 0x114a, 2, 'varh'),
  '-kvarh3-C' : ('Phase 3 exported leading reactive energy',     3, False, 0x172, 3, 10., 0x114c, 2, 'varh'),
  '-kvarh∑-C' : ('System exported leading reactive energy',  'sys', False, 0x175, 3, 10., 0x114e, 2, 'varh'),

  # TARIFF 1: Counter Address + 0x0100
  # TARIFF 2: Counter Address + 0x0200

  # PARTIAL_COUNTER_VALUES
  '+kWh∑ PAR'     : ('System imported active energy',           'sys', False, 0x0400, 3, 10., 0x1400, 2,   'Wh'),
  '-kWh∑ PAR'     : ('System exported active energy',           'sys', False, 0x0403, 3, 10., 0x1402, 2,   'Wh'),
  '+kVAh∑-L PAR'  : ('System imported lagging apparent energy', 'sys', False, 0x0406, 3, 10., 0x1404, 2,  'VAh'),
  '-kVAh∑-L PAR'  : ('System exported lagging apparent energy', 'sys', False, 0x0409, 3, 10., 0x1406, 2,  'VAh'),
  '+kVAh∑-C PAR'  : ('System imported leading apparent energy', 'sys', False, 0x040C, 3, 10., 0x1408, 2,  'VAh'),
  '-kVAh∑-C PAR'  : ('System exported leading apparent energy', 'sys', False, 0x040F, 3, 10., 0x140A, 2,  'VAh'),
  '+kvarh∑-L PAR' : ('System imported lagging reactive energy', 'sys', False, 0x0412, 3, 10., 0x140C, 2, 'varh'),
  '-kvarh∑-L PAR' : ('System exported lagging reactive energy', 'sys', False, 0x0415, 3, 10., 0x140E, 2, 'varh'),
  '+kvarh∑-C PAR' : ('System imported leading reactive energy', 'sys', False, 0x0418, 3, 10., 0x1410, 2, 'varh'),
  '-kvarh∑-C PAR' : ('System exported leading reactive energy', 'sys', False, 0x041B, 3, 10., 0x1412, 2, 'varh'),

  # BALANCE_VALUES
  'kWh∑'     : ('System active energy',           'sys', True, 0x041E, 3, 10., 0x1414, 2,   'Wh'),
  'kVAh∑-L'  : ('System lagging apparent energy', 'sys', True, 0x0421, 3, 10., 0x1416, 2,  'VAh'),
  'kVAh∑-C'  : ('System leading apparent energy', 'sys', True, 0x0424, 3, 10., 0x1418, 2,  'VAh'),
  'kvarh∑-L' : ('System lagging reactive energy', 'sys', True, 0x0427, 3, 10., 0x141A, 2, 'varh'),
  'kvarh∑-C' : ('System leading reactive energy', 'sys', True, 0x042A, 3, 10., 0x141C, 2, 'varh'),
}

REAL_TIME_LIST = [
  'V1', 'V2', 'V3', 'V12', 'V23', 'V31', 'V∑', 'A1', 'A2', 'A3', 'AN', 'A∑',
  'PF1', 'PF2', 'PF3', 'PF∑', 'P1', 'P2', 'P3', 'P∑',
  'S1', 'S2', 'S3', 'S∑', 'Q1', 'Q2', 'Q3', 'Q∑', 'F', 'Phase sequence',
]
COUNTER_LIST = [
  '+kWh1',     '+kWh2',     '+kWh3',     '+kWh∑',     '-kWh1',     '-kWh2',     '-kWh3',     '-kWh∑',
  '+kVAh1-L',  '+kVAh2-L',  '+kVAh3-L',  '+kVAh∑-L',  '-kVAh1-L',  '-kVAh2-L',  '-kVAh3-L',  '-kVAh∑-L',
  '+kVAh1-C',  '+kVAh2-C',  '+kVAh3-C',  '+kVAh∑-C',  '-kVAh1-C',  '-kVAh2-C',  '-kVAh3-C',  '-kVAh∑-C',
  '+kvarh1-L', '+kvarh2-L', '+kvarh3-L', '+kvarh∑-L', '-kvarh1-L', '-kvarh2-L', '-kvarh3-L', '-kvarh∑-L',
  '+kvarh1-C', '+kvarh2-C', '+kvarh3-C', '+kvarh∑-C', '-kvarh1-C', '-kvarh2-C', '-kvarh3-C', '-kvarh∑-C'
]

PARTIAL_COUNTER_LIST = [
  '+kWh∑ PAR',     '-kWh∑ PAR',
  '+kVAh∑-L PAR',  '-kVAh∑-L PAR',  '+kVAh∑-C PAR',  '-kVAh∑-C PAR', 
  '+kvarh∑-L PAR', '-kvarh∑-L PAR', '+kvarh∑-C PAR', '-kvarh∑-C PAR'
]

BALANCE_LIST = ['kWh∑', 'kVAh∑-L', 'kVAh∑-C', 'kvarh∑-L', 'kvarh∑-C']

COUNTER_COMMUNICATION_DATA_RAW = {
  'serial'     : ('Energy counter serial number',                       0x0500, 5, ),
  'model'      : ('Energy counter model',                               0x0505, 1, ),
  'type'       : ('Energy counter type',                                0x0506, 1, ),
  'firmware'   : ('Energy counter firmware release',                    0x0507, 1, ),
  'hardware'   : ('Energy counter hardware version',                    0x0508, 1, ),
# '6'          : ('Reserved',                                           0x0509, 2, ),
  'tariff'     : ('Tariff in use',                                      0x050B, 1, ),
  'pri_sec'   : ('Primary/secondary value',                            0x050C, 1, ),
  'error'      : ('Energy counter error code',                          0x050D, 1, ),
# Ratio between the primary and secondary value of the current transformer:
# 'ct'         : ('CT value (only for counter 6A 3phase model)',        0x050E, 1, ),
# '11'         : ('Reserved',                                           0x050F, 2, ),
  'fsa'        : ('Current full scale value (A)',                       0x0511, 1, ),
  'wiring'     : ('Wiring mode',                                        0x0512, 1, ),
# '14'         : ('MODBUS address (not available for MODBUS TCP)',      0x0513, 1, ),
# '15'         : ('MODBUS mode (not available for MODBUS TCP)',         0x0514, 1, ),
# '16'         : ('Communication speed (not available for MODBUS TCP)', 0x0515, 1, ),
# '17'         : ('Reserved',                                           0x0516, 2, ),
  'partial'  : ('Partial counters status',                            0x0517, 1, ),
  'm_serial'   : ('Module serial number',                               0x0518, 5, ),
  'svr'        : ('Signed value representation',                        0x051D, 1, ),
# '21'         : ('Reserved',                                           0x051E, 1, ),
  'm_firmware' : ('Module firmware release',                            0x051F, 1, ),
  'm_hardware' : ('Module hardware version',                            0x0520, 1, ),
# '24'         : ('Reserved',                                           0x0521, 2, ),
# '25'         : ('Register set type',                                  0x0523, 1, ),
}

COUNTER_COMMUNICATION_DATA_LIST = [
  'serial', 'model', 'type', 'firmware', 'hardware', 'tariff', 'pri_sec', 'error',
  'fsa', 'wiring', 'partial', 'm_serial', 'svr', 'm_firmware', 'm_hardware',
]

COILS_RAW = {
  # Byte 1 - voltage out of range
  'UV3' : ('Under Min Level Phase 3 Voltage',),
  'UV2' : ('Under Min Level Phase 2 Voltage',),
  'UV1' : ('Under Min Level Phase 1 Voltage',),
  'UV∑' : ('Under Min Level System Voltage',),
  'OV3' : ('Over Max Level Phase 3 Voltage',),
  'OV2' : ('Over Max Level Phase 2 Voltage',),
  'OV1' : ('Over Max Level Phase 1 Voltage',),
  'OV∑' : ('Over Max Level System Voltage',),
  
  #Byte 2 - line voltage out of range
  'COM'  : ('communication in progress',),
  'RES'  : ('reserved bit to 0',),
  'UV31' : ('Under Min Level Line 31 Voltage',),
  'UV23' : ('Under Min Level Line 23 Voltage',),
  'UV12' : ('Under Min Level Line 12 Voltage',),
  'OV31' : ('Over Max Level Line 31 Voltage',),
  'OV23' : ('Over Max Level Line 23 Voltage',),
  'OV12' : ('Over Max Level Line 12 Voltage',),
  
  # Byte 3/4 - current out of range
  'RES' : ('reserved bit to 0',),
  'RES' : ('reserved bit to 0',),
  'RES' : ('reserved bit to 0',),
  'RES' : ('reserved bit to 0',),
  'RES' : ('reserved bit to 0',),
  'RES' : ('reserved bit to 0',), 
  'UIN' : ('Under Min Level Phase Neutral Current',),
  'UI3' : ('Under Min Level Phase 3 Current',),

  'UI2' : ('Under Min Level Phase 2 Current',),
  'UI1' : ('Under Min Level Phase 1 Current',),
  'UI∑' : ('Under Min Level System Current',),
  'OIN' : ('Over Max Level Neutral Current',),
  'OI3' : ('Over Max Level Phase 3 Current',),
  'OI2' : ('Over Max Level Phase 2 Current',),
  'OI1' : ('Over Max Level Phase 1 Current',),
  'OI∑' : ('Over Max Level System Current',),
  
  # Byte 5 - frequency out of range
  'RES' : ('reserved bit to 0',),
  'RES' : ('reserved bit to 0',),
  'RES' : ('reserved bit to 0',),
  'RES' : ('reserved bit to 0',),
  'RES' : ('reserved bit to 0',),
  'RES' : ('reserved bit to 0',),
  'RES' : ('reserved bit to 0',),
  'F'   : ('Frequency Out Of Range',),
}

COILS_LIST = [
  'OV∑', 'OV1', 'OV2', 'OV3', 'UV∑', 'UV1', 'UV2', 'UV3',
  'OV12', 'OV23', 'OV31', 'UV12', 'UV23', 'UV31', 'RES', 'COM',
  'UI3', 'UIN', 'RES', 'RES', 'RES', 'RES', 'RES', 'RES',
  'OI∑', 'OI1', 'OI2', 'OI3', 'OIN', 'UI∑', 'UI1', 'UI2',
  'F', 'RES', 'RES', 'RES', 'RES', 'RES', 'RES', 'RES',
]

def convert_registers(reg_dict):
    ret_dict = dict()
    for reg_code in reg_dict:
        tpl = reg_dict[reg_code] # tuple
        register = dict()
        if len(tpl) == 9:
            register = {
              'code': reg_code,
              'descr': tpl[0],
              'related_to': tpl[1],
              'sign': tpl[2],
              'reg_int_start_addr': tpl[3],
              'reg_int_num_words': tpl[4],
              'reg_int_divisor': tpl[5],
              'reg_ieee_start_addr': tpl[6],
              'reg_ieee_num_words': tpl[7],
              'unit': tpl[8],
            }
        if len(tpl) == 3:
            register = {
              'code': reg_code,
              'descr': tpl[0],
              'reg_int_start_addr': tpl[1],
              'reg_int_num_words': tpl[2],
            }
        if len(tpl) == 1:
            register = {
              'code': reg_code,
              'descr': tpl[0],
            }
        ret_dict[reg_code] = register
    return ret_dict

RR = convert_registers(RR_RAW)
COUNTER_COMMUNICATION_DATA = convert_registers(COUNTER_COMMUNICATION_DATA_RAW)
COILS = convert_registers(COILS_RAW)

class U180C(object):

    def __init__(self, host, port=502):
        self.host = host
        self.port = port
        self.client = pymodbus.client.sync.ModbusTcpClient(host, port=502)
        self.client.connect()

    def read_cc(self):
        ccd = COUNTER_COMMUNICATION_DATA
        ret_list = []
        for code in COUNTER_COMMUNICATION_DATA_LIST:
            rd = ccd[code] # register definition
            rr = self.client.read_input_registers(rd['reg_int_start_addr'], rd['reg_int_num_words'])
            assert rr.function_code < 0x80, 'Error: returned function code is ' + hex(rr.function_code)
            if code == 'serial':
                value = ''.join([''.join((chr(val>>8),chr(val&0xff))) for val in rr.registers])
            elif code == 'model':
                model_map = {0x03: '6A 3phases/4wires', 0x06: '6A 3phases/3wires',
                             0x08: '80A 3phases/4wires', 0x0A: '80A 3phases/3wires',
                             0x0C: '80A 1phase/2wires'}
                assert rr.registers[0] in model_map
                value = model_map[rr.registers[0]]
            elif code == 'type':
                type_map = {0x00: 'with RESET function, NO MID',
                             0x01: 'NO MID',
                             0x02: 'MID' }
                assert rr.registers[0] in type_map
                value = type_map[rr.registers[0]]
            elif code in ['firmware', 'm_firmware']:
                fw_str = str(rr.registers[0])
                value = fw_str[:-2] + '.' + fw_str[-2:]
            elif code in ['hardware', 'm_hardware']:
                fw_str = str(rr.registers[0])
                value = fw_str[:-2] + '.' + fw_str[-2:]
            elif code == 'tariff':
                tariff_map = {0x1: 'tariff 1', 0x2: 'tariff 2'}
                value = tariff_map[rr.registers[0]]
            elif code == 'pri_sec':
                val_map = {0x0: 'primary', 0x1: 'secondary'}
                value = val_map[rr.registers[0]]
            elif code == 'error':
                val_map = {0x0: 'none', 0x1: 'phase sequence error'}
                value = val_map[rr.registers[0]]
            elif code == 'fsa':
                val_map = {0x0: '1A', 0x1: '5A', 0x2: '80A'}
                value = val_map[rr.registers[0]]
            elif code == 'wiring':
                val_map = {0x1: '3phases/4-wires', 0x2: '3phases/3-wires', 0x3: '1-phase'}
                value = val_map[rr.registers[0]]
            elif code == 'partial':
                bits = rr.registers[0]
                partial_counter_map = [
                  '+kWh∑ PAR',
                  '-kWh∑ PAR',
                  '+kVAh∑-L PAR',
                  '-kVAh∑-L PAR',
                  '+kVAh∑-C PAR',
                  '-kVAh∑-C PAR',
                  '+kvarh∑-L PAR',
                  '-kvarh∑-L PAR',
                  '+kvarh∑-C PAR',
                  '-kvarh∑-C PAR',
                ]
                value = []
                for partial_counter in partial_counter_map:
                    value.append({partial_counter: bits & 0x1})
                    bits = bits >> 1
            elif code == 'm_serial':
                value = ''.join([''.join((chr(val>>8),chr(val&0xff))) for val in rr.registers])
            #elif code == 'svr':
            #    val_map = {0x0: 'sign bit', 0x1: '2’s complement'}
            #    value = val_map[rr.registers[0]]
            else:
                value = rr.registers
            ret_list.append( (rd, value) )
        return ret_list

    def read_all_real_time(self):
        return self.read_ieee_registers(REAL_TIME_LIST)

    def read_all_counter(self):
        return self.read_ieee_registers(COUNTER_LIST)

    def read_all_balance(self):
        return self.read_ieee_registers(BALANCE_LIST)

    def read_coherent_block(self, register_list):
        num_words = sum([RR[key]['reg_int_num_words'] for key in register_list])
        rr = self.client.read_input_registers(RR[register_list[0]]['reg_int_start_addr'], num_words)
        assert rr.function_code < 0x80
        assert len(rr.registers) == num_words
        ret_list = []
        pos = 0
        for reg_code in RR_RT_ORDER:
            reg = RR[reg_code]
            value = U180C.calculate_value_int_reg(reg, rr.registers[pos:pos+reg['reg_int_num_words']])
            pos += reg['reg_int_num_words']
            ret_list.append((reg, value))
        return ret_list

    def read_ieee_registers(self, register_list):
        min_address = min([RR[code]['reg_ieee_start_addr'] for code in register_list])
        max_address = max([RR[code]['reg_ieee_start_addr']+RR[code]['reg_ieee_num_words'] for code in register_list])
        num_words = max_address - min_address + 1
        assert num_words <= 0xFF # manual says max 256 bytes, but might be 256 words = 512 bytes
        rr = self.client.read_input_registers(min_address, num_words)
        assert rr.function_code < 0x80
        assert len(rr.registers) == num_words
        ret_list = []
        for code in register_list:
            rd = RR[code] # register definition
            rel_addr = rd['reg_ieee_start_addr'] - min_address
            words = rr.registers[rel_addr:rel_addr+rd['reg_ieee_num_words']]
            ieee_bytes = bytes([words[0]>>8, words[0]&0xFF, words[1]>>8, words[1]&0xFF])
            value = struct.unpack('>f', ieee_bytes)[0]
            ret_list.append((rd, value))
        return ret_list

    def read_int_registers(self, register_list):
        min_address = min([RR[code]['reg_int_start_addr'] for code in register_list])
        max_address = max([RR[code]['reg_int_start_addr']+RR[code]['reg_int_num_words'] for code in register_list])
        num_words = max_address - min_address + 1
        assert num_words <= 0xFF # manual says max 256 bytes, but might be 256 words = 512 bytes
        rr = self.client.read_input_registers(min_address, num_words)
        assert rr.function_code < 0x80
        assert len(rr.registers) == num_words
        ret_list = []
        for code in register_list:
            rd = RR[code] # register definition
            rel_addr = rd['reg_int_start_addr'] - min_address
            value = U180C.calculate_value_int_reg(rd, rr.registers[rel_addr:rel_addr+rd['reg_int_num_words']])
            ret_list.append((rd, value))
        return ret_list

    def calculate_value_int_reg(register_definition, register_values):
        rd = register_definition
        rv = register_values.copy()
        if rd['sign']:
            sign = (rv[0] & 0x8000) >> 15
            rv[0] = rv[0] & ~(0x8000)
        else:
            sign = 0
        if sign == 0: sign_factor = 1
        if sign == 1: sign_factor = -1
        if rd['reg_int_num_words'] == 1:
            value = rv[0]
        if rd['reg_int_num_words'] == 2:
            value = (rv[0] << 16) | rv[1]
        if rd['reg_int_num_words'] == 3:
            value = (rv[0] << 32) | (rv[1] << 16) | rv[2]
        value = sign_factor * value
        value /= rd['reg_int_divisor']
        return value

    def read_coils(self):
        coil_addr = 0x00
        num_coils = len(COILS_LIST)
        rr = self.client.read_coils(coil_addr, num_coils)
        assert rr.function_code < 0x80
        assert len(rr.bits) == num_coils
        self.coils = []
        pos = 0
        for key in COILS_LIST:
            self.coils.append((COILS[key], rr.bits[pos]))
            pos += 1
        self.coils = [coil for coil in self.coils if coil[0]['code'] != 'RES']
        return self.coils

    def read_register(self, code):
        reg = RR[code]
        rr = self.client.read_input_registers(reg['reg_int_start_addr'], reg['reg_int_num_words'])
        assert rr.function_code < 0x80
        assert len(rr.registers) == reg['reg_int_num_words']
        value = calculate_value_int_reg(reg, rr.registers)
        return (reg, value)

    def print_register(register_definition, value=None):
        rd = register_definition
        if value is not None:
            if type(value) == float:
                value = "{:.3f}".format(value)
            print("{code} ({descr}):".format(**rd))
            if 'unit' in rd and rd['unit']: print("{value} {unit}".format(value=value, unit=rd['unit']))
            else: print("{value}".format(value=value))
        else:
            print("{code} ({descr}) - unit: {unit}".format(**rd))

    def close(self):
        self.client.close()

def main():
    parser = argparse.ArgumentParser(description='Talk to a Gossen U180C via Modbus TCP')
    parser.add_argument('host', help='The Modbus TCP host to connect to')
    parser.add_argument('--debug', help='Enable debugging output')
    parser.add_argument('--filter', help="Filter output values. State 1,2,3 for phases or 'sys' for system.")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig()
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)

    try:
        u180c = U180C(args.host)
        cc = u180c.read_cc()
        for conf_val in cc:
            U180C.print_register(*conf_val)
    except pymodbus.exceptions.ConnectionException:
        parser.error('Could not connect to host ' + args.host)

    coils = u180c.read_coils()
    for coil_val in coils:
        coil = coil_val[0]
        value = coil_val[1]
        if value:
            print("Warning: Coil {code} ({descr}) is ON!".format(**coil))

    try:
        while True:
            regs_values = u180c.read_all_real_time()
            for reg_value in regs_values:
                if args.filter:
                    reg_def = reg_value[0]
                    if reg_def['related_to'] == args.filter:
                        U180C.print_register(*reg_value)
                else:
                    U180C.print_register(*reg_value)
            regs_values = u180c.read_all_counter()
            for reg_value in regs_values:
                if args.filter:
                    reg_def = reg_value[0]
                    if reg_def['related_to'] == args.filter:
                        U180C.print_register(*reg_value)
                else:
                    U180C.print_register(*reg_value)
            regs_values = u180c.read_all_balance()
            for reg_value in regs_values:
                if args.filter:
                    reg_def = reg_value[0]
                    if reg_def['related_to'] == args.filter:
                        U180C.print_register(*reg_value)
                else:
                    U180C.print_register(*reg_value)
            print(dt.now())
            sys.stdout.flush()
            time.sleep(5)
    except KeyboardInterrupt:
        sys.stderr.write('[Ctrl]-[c] pressed. Exiting...\n')

    import pdb; pdb.set_trace()

    u180c.close()

if __name__ == "__main__":
    main()
