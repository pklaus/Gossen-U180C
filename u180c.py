#!/usr/bin/env python

import logging
import argparse
from datetime import datetime as dt
import time
import sys
import struct


# XML element name in
# http://192.168.178.253/tmp/0_readings.xml?1428492576635
# sn       AB1OB00413
# paracnt  167
# datet    8/4/2015 13:29:32
# param0   232.495
# ...
# param165 01
# param166 00

# Readable Registers
RR_RAW = {
  'mapping' : {
    'key': 'code',
    0    : 'api_no',
    1    : 'csv_code',
    2    : 'descr',
    3    : 'descr2',
    4    : 'related_to',
    5    : 'sign',
    6    : 'reg_int_start_addr',
    7    : 'reg_int_num_words',
    8    : 'reg_int_divisor',
    9    : 'reg_ieee_start_addr',
    10   : 'reg_ieee_num_words',
    11   : 'unit'
  },
  # REAL-TIME VALUES
  'V1'  :  ( 0, 'V1N',      'Phase 1 Voltage',        'L-N voltage phase 1',        1, False, 0x00, 2, 1000., 0x1000, 2,   'V'),
  'V2'  :  ( 1, 'V2N',      'Phase 2 Voltage',        'L-N voltage phase 2',        2, False, 0x02, 2, 1000., 0x1002, 2,   'V'),
  'V3'  :  ( 2, 'V3N',      'Phase 3 Voltage',        'L-N voltage phase 3',        3, False, 0x04, 2, 1000., 0x1004, 2,   'V'),
  'V12' :  ( 3, 'V12',      'Line 12 Voltage',        'L-L voltage line 12',    [1,2], False, 0x06, 2, 1000., 0x1006, 2,   'V'),
  'V23' :  ( 4, 'V23',      'Line 23 Voltage',        'L-L voltage line 23',    [2,3], False, 0x08, 2, 1000., 0x1008, 2,   'V'),
  'V31' :  ( 5, 'V31',      'Line 31 Voltage',        'L-L voltage line 31',    [3,1], False, 0x0A, 2, 1000., 0x100A, 2,   'V'),
  'V∑'  :  ( 6, 'VSYS',     'System Voltage',         'System voltage',         'sys', False, 0x0C, 2, 1000., 0x100C, 2,   'V'),
  'A1'  :  ( 7, 'A1',       'Phase 1 Current',        'Phase 1 current',            1, True,  0x0E, 2, 1000., 0x100E, 2,   'A'),
  'A2'  :  ( 8, 'A2',       'Phase 2 Current',        'Phase 2 current',            2, True,  0x10, 2, 1000., 0x1010, 2,   'A'),
  'A3'  :  ( 9, 'A3',       'Phase 3 Current',        'Phase 3 current',            3, True,  0x12, 2, 1000., 0x1012, 2,   'A'),
  'AN'  :  (10, 'AN',       'Neutral Current',        'Neutral current',        'sys', True,  0x14, 2, 1000., 0x1014, 2,   'A'),
  'A∑'  :  (11, 'ASYS',     'System Current',         'System current',         'sys', True,  0x16, 2, 1000., 0x1016, 2,   'A'),
  'PF1' :  (12, 'PF1',      'Phase 1 Power Factor',   'Phase 1 power factor',       1, True,  0x18, 1, 1000., 0x1018, 2,  None),
  'PF2' :  (13, 'PF2',      'Phase 2 Power Factor',   'Phase 2 power factor',       2, True,  0x19, 1, 1000., 0x101A, 2,  None),
  'PF3' :  (14, 'PF3',      'Phase 3 Power Factor',   'Phase 3 power factor',       3, True,  0x1A, 1, 1000., 0x101C, 2,  None),
  'PF∑' :  (15, 'PFSYS',    'System Power Factor',    'System power factor',    'sys', True,  0x1B, 1, 1000., 0x101E, 2,  None),
  'P1'  :  (16, 'P1',       'Phase 1 Active Power',   'Phase 1 active power',       1, True,  0x1C, 3, 1000., 0x1020, 2,   'W'),
  'P2'  :  (17, 'P2',       'Phase 2 Active Power',   'Phase 2 active power',       2, True,  0x1F, 3, 1000., 0x1022, 2,   'W'),
  'P3'  :  (18, 'P3',       'Phase 3 Active Power',   'Phase 3 active power',       3, True,  0x22, 3, 1000., 0x1024, 2,   'W'),
  'P∑'  :  (19, 'PSYS',     'System Active Power',    'System active power',    'sys', True,  0x25, 3, 1000., 0x1026, 2,   'W'),
  'S1'  :  (20, 'S1',       'Phase 1 Apparent Power', 'Phase 1 apparent power',     1, True,  0x28, 3, 1000., 0x1028, 2,  'VA'),
  'S2'  :  (21, 'S2',       'Phase 2 Apparent Power', 'Phase 2 apparent power',     2, True,  0x2B, 3, 1000., 0x102A, 2,  'VA'),
  'S3'  :  (22, 'S3',       'Phase 3 Apparent Power', 'Phase 3 apparent power',     3, True,  0x2E, 3, 1000., 0x102C, 2,  'VA'),
  'S∑'  :  (23, 'SSYS',     'System Apparent Power',  'System apparent power',  'sys', True,  0x31, 3, 1000., 0x102E, 2,  'VA'),
  'Q1'  :  (24, 'Q1',       'Phase 1 Reactive Power', 'Phase 1 reactive power',     1, True,  0x34, 3, 1000., 0x1030, 2, 'var'),
  'Q2'  :  (25, 'Q2',       'Phase 2 Reactive Power', 'Phase 2 reactive power',     2, True,  0x37, 3, 1000., 0x1032, 2, 'var'),
  'Q3'  :  (26, 'Q3',       'Phase 3 Reactive Power', 'Phase 3 reactive power',     3, True,  0x3A, 3, 1000., 0x1034, 2, 'var'),
  'Q∑'  :  (27, 'QSYS',     'System Reactive Power',  'System reactive power',  'sys', True,  0x3D, 3, 1000., 0x1036, 2, 'var'),
  'F'   :  (28, 'F',        'Frequency',              'Frequency',              'sys', False, 0x40, 1, 1000., 0x1038, 2,  'Hz'),
  'ps'  :  (29, 'PHASE_SEQ','Phase Order',            'Phase sequence',         'sys', False, 0x41, 1,     1, 0x103A, 2,  None),
  # COUNTER VALUES
  '+kWh1'        : ( 30, 'kWh1_imp',         'Phase 1 Imported Active Energy, Total',                 'Phase 1 imported active energy',               1, False, 0x100, 3, 10., 0x1100, 2,   'Wh'),
  '+kWh2'        : ( 31, 'kWh2_imp',         'Phase 2 Imported Active Energy, Total',                 'Phase 2 imported active energy',               2, False, 0x103, 3, 10., 0x1102, 2,   'Wh'),  
  '+kWh3'        : ( 32, 'kWh3_imp',         'Phase 3 Imported Active Energy, Total',                 'Phase 3 imported active energy',               3, False, 0x106, 3, 10., 0x1104, 2,   'Wh'),  
  '+kWh∑'        : ( 33, 'kWhSYS_imp',       'System Imported Active Energy, Total',                  'System imported active energy',            'sys', False, 0x109, 3, 10., 0x1106, 2,   'Wh'),  
  '-kWh1'        : ( 34, 'kWh1_exp',         'Phase 1 Exported Active Energy, Total',                 'Phase 1 exported active energy',               1, False, 0x10c, 3, 10., 0x1108, 2,   'Wh'),  
  '-kWh2'        : ( 35, 'kWh2_exp',         'Phase 2 Exported Active Energy, Total',                 'Phase 2 exported active energy',               2, False, 0x10f, 3, 10., 0x110a, 2,   'Wh'),  
  '-kWh3'        : ( 36, 'kWh3_exp',         'Phase 3 Exported Active Energy, Total',                 'Phase 3 exported active energy',               3, False, 0x112, 3, 10., 0x110c, 2,   'Wh'),  
  '-kWh∑'        : ( 37, 'kWh SYS_exp',      'System Exported Active Energy, Total',                  'System exported active energy',            'sys', False, 0x115, 3, 10., 0x110e, 2,   'Wh'),  
  '+kVAh1-L'     : ( 38, 'kVAh1_L_imp',      'Phase 1 Imported Inductive Apparent Energy, Total',     'Phase 1 imported lagging apparent energy',     1, False, 0x118, 3, 10., 0x1110, 2,  'VAh'),  
  '+kVAh2-L'     : ( 39, 'kVAh2_L_imp',      'Phase 2 Imported Inductive Apparent Energy, Total',     'Phase 2 imported lagging apparent energy',     2, False, 0x11b, 3, 10., 0x1112, 2,  'VAh'),  
  '+kVAh3-L'     : ( 40, 'kVAh3_L_imp',      'Phase 3 Imported Inductive Apparent Energy, Total',     'Phase 3 imported lagging apparent energy',     3, False, 0x11e, 3, 10., 0x1114, 2,  'VAh'),  
  '+kVAh∑-L'     : ( 41, 'kVAhSYS_L_imp',    'System Imported Inductive Apparent Energy, Total',      'System imported lagging apparent energy',  'sys', False, 0x121, 3, 10., 0x1116, 2,  'VAh'),  
  '-kVAh1-L'     : ( 42, 'kVAh1_L_exp',      'Phase 1 Exported Inductive Apparent Energy, Total',     'Phase 1 exported lagging apparent energy',     1, False, 0x124, 3, 10., 0x1118, 2,  'VAh'),  
  '-kVAh2-L'     : ( 43, 'kVAh2_L_exp',      'Phase 2 Exported Inductive Apparent Energy, Total',     'Phase 2 exported lagging apparent energy',     2, False, 0x127, 3, 10., 0x111a, 2,  'VAh'),  
  '-kVAh3-L'     : ( 44, 'kVAh3_L_exp',      'Phase 3 Exported Inductive Apparent Energy, Total',     'Phase 3 exported lagging apparent energy',     3, False, 0x12a, 3, 10., 0x111c, 2,  'VAh'),  
  '-kVAh∑-L'     : ( 45, 'kVAhSYS_L_exp',    'System Exported Inductive Apparent Energy, Total',      'System exported lagging apparent energy',  'sys', False, 0x12d, 3, 10., 0x111e, 2,  'VAh'),  
  '+kVAh1-C'     : ( 46, 'kVAh1_C_imp',      'Phase 1 Imported Capacitive Apparent Energy, Total',    'Phase 1 imported leading apparent energy',     1, False, 0x130, 3, 10., 0x1120, 2,  'VAh'),  
  '+kVAh2-C'     : ( 47, 'kVAh2_C_imp',      'Phase 2 Imported Capacitive Apparent Energy, Total',    'Phase 2 imported leading apparent energy',     2, False, 0x133, 3, 10., 0x1122, 2,  'VAh'),  
  '+kVAh3-C'     : ( 48, 'kVAh3_C_imp',      'Phase 3 Imported Capacitive Apparent Energy, Total',    'Phase 3 imported leading apparent energy',     3, False, 0x136, 3, 10., 0x1124, 2,  'VAh'),  
  '+kVAh∑-C'     : ( 49, 'kVAhSYS_C_imp',    'System Imported Capacitive Apparent Energy, Total',     'System imported leading apparent energy',  'sys', False, 0x139, 3, 10., 0x1126, 2,  'VAh'),  
  '-kVAh1-C'     : ( 50, 'kVAh1_C_exp',      'Phase 1 Exported Capacitive Apparent Energy, Total',    'Phase 1 exported leading apparent energy',     1, False, 0x13c, 3, 10., 0x1128, 2,  'VAh'),  
  '-kVAh2-C'     : ( 51, 'kVAh2_C_exp',      'Phase 2 Exported Capacitive Apparent Energy, Total',    'Phase 2 exported leading apparent energy',     2, False, 0x13f, 3, 10., 0x112a, 2,  'VAh'),  
  '-kVAh3-C'     : ( 52, 'kVAh3_C_exp',      'Phase 3 Exported Capacitive Apparent Energy, Total',    'Phase 3 exported leading apparent energy',     3, False, 0x142, 3, 10., 0x112c, 2,  'VAh'),  
  '-kVAh∑-C'     : ( 53, 'kVAhSYS_C_exp',    'System Exported Capacitive Apparent Energy, Total',     'System exported leading apparent energy',  'sys', False, 0x145, 3, 10., 0x112e, 2,  'VAh'),  
  '+kvarh1-L'    : ( 54, 'kvarh1_L_imp',     'Phase 1 Imported Inductive Reactive Energy, Total',     'Phase 1 imported lagging reactive energy',     1, False, 0x148, 3, 10., 0x1130, 2, 'varh'),  
  '+kvarh2-L'    : ( 55, 'kvarh2_L_imp',     'Phase 2 Imported Inductive Reactive Energy, Total',     'Phase 2 imported lagging reactive energy',     2, False, 0x14b, 3, 10., 0x1132, 2, 'varh'),  
  '+kvarh3-L'    : ( 56, 'kvarh3_L_imp',     'Phase 3 Imported Inductive Reactive Energy, Total',     'Phase 3 imported lagging reactive energy',     3, False, 0x14e, 3, 10., 0x1134, 2, 'varh'),  
  '+kvarh∑-L'    : ( 57, 'kvarhSYS_L_imp',   'System Imported Inductive Reactive Energy, Total',      'System imported lagging reactive energy',  'sys', False, 0x151, 3, 10., 0x1136, 2, 'varh'),  
  '-kvarh1-L'    : ( 58, 'kvarh1_L_exp',     'Phase 1 Exported Inductive Reactive Energy, Total',     'Phase 1 exported lagging reactive energy',     1, False, 0x154, 3, 10., 0x1138, 2, 'varh'),  
  '-kvarh2-L'    : ( 59, 'kvarh2_L_exp',     'Phase 2 Exported Inductive Reactive Energy, Total',     'Phase 2 exported lagging reactive energy',     2, False, 0x157, 3, 10., 0x113a, 2, 'varh'),  
  '-kvarh3-L'    : ( 60, 'kvarh3_L_exp',     'Phase 3 Exported Inductive Reactive Energy, Total',     'Phase 3 exported lagging reactive energy',     3, False, 0x15a, 3, 10., 0x113c, 2, 'varh'),  
  '-kvarh∑-L'    : ( 61, 'kvarhSYS_L_exp',   'System Exported Inductive Reactive Energy, Total',      'System exported lagging reactive energy',  'sys', False, 0x15d, 3, 10., 0x113e, 2, 'varh'),  
  '+kvarh1-C'    : ( 62, 'kvarh1_C_imp',     'Phase 1 Imported Capacitive Reactive Energy, Total',    'Phase 1 imported leading reactive energy',     1, False, 0x160, 3, 10., 0x1140, 2, 'varh'),  
  '+kvarh2-C'    : ( 63, 'kvarh2_C_imp',     'Phase 2 Imported Capacitive Reactive Energy, Total',    'Phase 2 imported leading reactive energy',     2, False, 0x163, 3, 10., 0x1142, 2, 'varh'),  
  '+kvarh3-C'    : ( 64, 'kvarh3_C_imp',     'Phase 3 Imported Capacitive Reactive Energy, Total',    'Phase 3 imported leading reactive energy',     3, False, 0x166, 3, 10., 0x1144, 2, 'varh'),  
  '+kvarh∑-C'    : ( 65, 'kvarhSYS_C_imp',   'System Imported Capacitive Reactive Energy, Total',     'System imported leading reactive energy',  'sys', False, 0x169, 3, 10., 0x1146, 2, 'varh'),  
  '-kvarh1-C'    : ( 66, 'kvarh1_C_exp',     'Phase 1 Exported Capacitive Reactive Energy, Total',    'Phase 1 exported leading reactive energy',     1, False, 0x16c, 3, 10., 0x1148, 2, 'varh'),  
  '-kvarh2-C'    : ( 67, 'kvarh2_C_exp',     'Phase 2 Exported Capacitive Reactive Energy, Total',    'Phase 2 exported leading reactive energy',     2, False, 0x16f, 3, 10., 0x114a, 2, 'varh'),  
  '-kvarh3-C'    : ( 68, 'kvarh3_C_exp',     'Phase 3 Exported Capacitive Reactive Energy, Total',    'Phase 3 exported leading reactive energy',     3, False, 0x172, 3, 10., 0x114c, 2, 'varh'),  
  '-kvarh∑-C'    : ( 69, 'kvarhSYS_C_exp',   'System Exported Capacitive Reactive Energy, Total',     'System exported leading reactive energy',  'sys', False, 0x175, 3, 10., 0x114e, 2, 'varh'),  
  # TARIFF 1: Counter Address + 0x0100
  '+kWh1_t1'     : ( 70, 'kWh1_T1_imp',      'Phase 1 Imported Active Energy, Tariff 1',              'Phase 1 imported active energy',               1, False, 0x100, 3, 10., 0x1200, 2,   'Wh'),
  '+kWh2_t1'     : ( 71, 'kWh2_T1_imp',      'Phase 2 Imported Active Energy, Tariff 1',              'Phase 2 imported active energy',               2, False, 0x103, 3, 10., 0x1202, 2,   'Wh'),  
  '+kWh3_t1'     : ( 72, 'kWh3_T1_imp',      'Phase 3 Imported Active Energy, Tariff 1',              'Phase 3 imported active energy',               3, False, 0x106, 3, 10., 0x1204, 2,   'Wh'),  
  '+kWh∑_t1'     : ( 73, 'kWhSYS_T1_imp',    'System Imported Active Energy, Tariff 1',               'System imported active energy',            'sys', False, 0x109, 3, 10., 0x1206, 2,   'Wh'),  
  '-kWh1_t1'     : ( 74, 'kWh1_T1_exp',      'Phase 1 Exported Active Energy, Tariff 1',              'Phase 1 exported active energy',               1, False, 0x10c, 3, 10., 0x1208, 2,   'Wh'),  
  '-kWh2_t1'     : ( 75, 'kWh2_T1_exp',      'Phase 2 Exported Active Energy, Tariff 1',              'Phase 2 exported active energy',               2, False, 0x10f, 3, 10., 0x120a, 2,   'Wh'),  
  '-kWh3_t1'     : ( 76, 'kWh3_T1_exp',      'Phase 3 Exported Active Energy, Tariff 1',              'Phase 3 exported active energy',               3, False, 0x112, 3, 10., 0x120c, 2,   'Wh'),  
  '-kWh∑_t1'     : ( 77, 'kWhSYS_T1_exp',    'System Exported Active Energy, Tariff 1',               'System exported active energy',            'sys', False, 0x115, 3, 10., 0x120e, 2,   'Wh'),  
  '+kVAh1-L_t1'  : ( 78, 'kVAh1_L_T1_imp',   'Phase 1 Imported Inductive Apparent Energy, Tariff 1',  'Phase 1 imported lagging apparent energy',     1, False, 0x118, 3, 10., 0x1210, 2,  'VAh'),  
  '+kVAh2-L_t1'  : ( 79, 'kVAh2_L_T1_imp',   'Phase 2 Imported Inductive Apparent Energy, Tariff 1',  'Phase 2 imported lagging apparent energy',     2, False, 0x11b, 3, 10., 0x1212, 2,  'VAh'),  
  '+kVAh3-L_t1'  : ( 80, 'kVAh3_L_T1_imp',   'Phase 3 Imported Inductive Apparent Energy, Tariff 1',  'Phase 3 imported lagging apparent energy',     3, False, 0x11e, 3, 10., 0x1214, 2,  'VAh'),  
  '+kVAh∑-L_t1'  : ( 81, 'kVAhSYS_L_T1_imp', 'System Imported Inductive Apparent Energy, Tariff 1',   'System imported lagging apparent energy',  'sys', False, 0x121, 3, 10., 0x1216, 2,  'VAh'),  
  '-kVAh1-L_t1'  : ( 82, 'kVAh1_L_T1_exp',   'Phase 1 Exported Inductive Apparent Energy, Tariff 1',  'Phase 1 exported lagging apparent energy',     1, False, 0x124, 3, 10., 0x1218, 2,  'VAh'),  
  '-kVAh2-L_t1'  : ( 83, 'kVAh2_L_T1_exp',   'Phase 2 Exported Inductive Apparent Energy, Tariff 1',  'Phase 2 exported lagging apparent energy',     2, False, 0x127, 3, 10., 0x121a, 2,  'VAh'),  
  '-kVAh3-L_t1'  : ( 84, 'kVAh3_L_T1_exp',   'Phase 3 Exported Inductive Apparent Energy, Tariff 1',  'Phase 3 exported lagging apparent energy',     3, False, 0x12a, 3, 10., 0x121c, 2,  'VAh'),  
  '-kVAh∑-L_t1'  : ( 85, 'kVAhSYS_L_T1_exp', 'System Exported Inductive Apparent Energy, Tariff 1',   'System exported lagging apparent energy',  'sys', False, 0x12d, 3, 10., 0x121e, 2,  'VAh'),  
  '+kVAh1-C_t1'  : ( 86, 'kVAh1_C_T1_imp',   'Phase 1 Imported Capacitive Apparent Energy, Tariff 1', 'Phase 1 imported leading apparent energy',     1, False, 0x130, 3, 10., 0x1220, 2,  'VAh'),  
  '+kVAh2-C_t1'  : ( 87, 'kVAh2_C_T1_imp',   'Phase 2 Imported Capacitive Apparent Energy, Tariff 1', 'Phase 2 imported leading apparent energy',     2, False, 0x133, 3, 10., 0x1222, 2,  'VAh'),  
  '+kVAh3-C_t1'  : ( 88, 'kVAh3_C_T1_imp',   'Phase 3 Imported Capacitive Apparent Energy, Tariff 1', 'Phase 3 imported leading apparent energy',     3, False, 0x136, 3, 10., 0x1224, 2,  'VAh'),  
  '+kVAh∑-C_t1'  : ( 89, 'kVAhSYS_C_T1_imp', 'System Imported Capacitive Apparent Energy, Tariff 1',  'System imported leading apparent energy',  'sys', False, 0x139, 3, 10., 0x1226, 2,  'VAh'),  
  '-kVAh1-C_t1'  : ( 90, 'kVAh1_C_T1_exp',   'Phase 1 Exported Capacitive Apparent Energy, Tariff 1', 'Phase 1 exported leading apparent energy',     1, False, 0x13c, 3, 10., 0x1228, 2,  'VAh'),  
  '-kVAh2-C_t1'  : ( 91, 'kVAh2_C_T1_exp',   'Phase 2 Exported Capacitive Apparent Energy, Tariff 1', 'Phase 2 exported leading apparent energy',     2, False, 0x13f, 3, 10., 0x122a, 2,  'VAh'),  
  '-kVAh3-C_t1'  : ( 92, 'kVAh3_C_T1_exp',   'Phase 3 Exported Capacitive Apparent Energy, Tariff 1', 'Phase 3 exported leading apparent energy',     3, False, 0x142, 3, 10., 0x122c, 2,  'VAh'),  
  '-kVAh∑-C_t1'  : ( 93, 'kVAhSYS_C_T1_exp', 'System Exported Capacitive Apparent Energy, Tariff 1',  'System exported leading apparent energy',  'sys', False, 0x145, 3, 10., 0x122e, 2,  'VAh'),  
  '+kvarh1-L_t1' : ( 94, 'kvarh1_L_T1_imp',  'Phase 1 Imported Inductive Reactive Energy, Tariff 1',  'Phase 1 imported lagging reactive energy',     1, False, 0x148, 3, 10., 0x1230, 2, 'varh'),  
  '+kvarh2-L_t1' : ( 95, 'kvarh2_L_T1_imp',  'Phase 2 Imported Inductive Reactive Energy, Tariff 1',  'Phase 2 imported lagging reactive energy',     2, False, 0x14b, 3, 10., 0x1232, 2, 'varh'),  
  '+kvarh3-L_t1' : ( 96, 'kvarh3_L_T1_imp',  'Phase 3 Imported Inductive Reactive Energy, Tariff 1',  'Phase 3 imported lagging reactive energy',     3, False, 0x14e, 3, 10., 0x1234, 2, 'varh'),  
  '+kvarh∑-L_t1' : ( 97, 'kvarhSYS_L_T1_imp','System Imported Inductive Reactive Energy, Tariff 1',   'System imported lagging reactive energy',  'sys', False, 0x151, 3, 10., 0x1236, 2, 'varh'),  
  '-kvarh1-L_t1' : ( 98, 'kvarh1_L_T1_exp',  'Phase 1 Exported Inductive Reactive Energy, Tariff 1',  'Phase 1 exported lagging reactive energy',     1, False, 0x154, 3, 10., 0x1238, 2, 'varh'),  
  '-kvarh2-L_t1' : ( 99, 'kvarh2_L_T1_exp',  'Phase 2 Exported Inductive Reactive Energy, Tariff 1',  'Phase 2 exported lagging reactive energy',     2, False, 0x157, 3, 10., 0x123a, 2, 'varh'),  
  '-kvarh3-L_t1' : (100, 'kvarh3_L_T1_exp',  'Phase 3 Exported Inductive Reactive Energy, Tariff 1',  'Phase 3 exported lagging reactive energy',     3, False, 0x15a, 3, 10., 0x123c, 2, 'varh'),  
  '-kvarh∑-L_t1' : (101, 'kvarhSYS_L_T1_exp','System Exported Inductive Reactive Energy, Tariff 1',   'System exported lagging reactive energy',  'sys', False, 0x15d, 3, 10., 0x123e, 2, 'varh'),  
  '+kvarh1-C_t1' : (102, 'kvarh1_C_T1_imp',  'Phase 1 Imported Capacitive Reactive Energy, Tariff 1', 'Phase 1 imported leading reactive energy',     1, False, 0x160, 3, 10., 0x1240, 2, 'varh'),  
  '+kvarh2-C_t1' : (103, 'kvarh2_C_T1_imp',  'Phase 2 Imported Capacitive Reactive Energy, Tariff 1', 'Phase 2 imported leading reactive energy',     2, False, 0x163, 3, 10., 0x1242, 2, 'varh'),  
  '+kvarh3-C_t1' : (104, 'kvarh3_C_T1_imp',  'Phase 3 Imported Capacitive Reactive Energy, Tariff 1', 'Phase 3 imported leading reactive energy',     3, False, 0x166, 3, 10., 0x1244, 2, 'varh'),  
  '+kvarh∑-C_t1' : (105, 'kvarhSYS_C_T1_imp','System Imported Capacitive Reactive Energy, Tariff 1',  'System imported leading reactive energy',  'sys', False, 0x169, 3, 10., 0x1246, 2, 'varh'),  
  '-kvarh1-C_t1' : (106, 'kvarh1_C_T1_exp',  'Phase 1 Exported Capacitive Reactive Energy, Tariff 1', 'Phase 1 exported leading reactive energy',     1, False, 0x16c, 3, 10., 0x1248, 2, 'varh'),  
  '-kvarh2-C_t1' : (107, 'kvarh2_C_T1_exp',  'Phase 2 Exported Capacitive Reactive Energy, Tariff 1', 'Phase 2 exported leading reactive energy',     2, False, 0x16f, 3, 10., 0x124a, 2, 'varh'),  
  '-kvarh3-C_t1' : (108, 'kvarh3_C_T1_exp',  'Phase 3 Exported Capacitive Reactive Energy, Tariff 1', 'Phase 3 exported leading reactive energy',     3, False, 0x172, 3, 10., 0x124c, 2, 'varh'),  
  '-kvarh∑-C_t1' : (109, 'kvarhSYS_C_T1_exp','System Exported Capacitive Reactive Energy, Tariff 1',  'System exported leading reactive energy',  'sys', False, 0x175, 3, 10., 0x124e, 2, 'varh'),  
  # TARIFF 2: Counter Address + 0x0200
  '+kWh1_t2'     : (110, 'kWh1_T2_imp',      'Phase 1 Imported Active Energy, Tariff 2',              'Phase 1 imported active energy',               1, False, 0x100, 3, 10., 0x1300, 2,   'Wh'),
  '+kWh2_t2'     : (111, 'kWh2_T2_imp',      'Phase 2 Imported Active Energy, Tariff 2',              'Phase 2 imported active energy',               2, False, 0x103, 3, 10., 0x1302, 2,   'Wh'),  
  '+kWh3_t2'     : (112, 'kWh3_T2_imp',      'Phase 3 Imported Active Energy, Tariff 2',              'Phase 3 imported active energy',               3, False, 0x106, 3, 10., 0x1304, 2,   'Wh'),  
  '+kWh∑_t2'     : (113, 'kWhSYS_T2_imp',    'System Imported Active Energy, Tariff 2',               'System imported active energy',            'sys', False, 0x109, 3, 10., 0x1306, 2,   'Wh'),  
  '-kWh1_t2'     : (114, 'kWh1_T2_exp',      'Phase 1 Exported Active Energy, Tariff 2',              'Phase 1 exported active energy',               1, False, 0x10c, 3, 10., 0x1308, 2,   'Wh'),  
  '-kWh2_t2'     : (115, 'kWh2_T2_exp',      'Phase 2 Exported Active Energy, Tariff 2',              'Phase 2 exported active energy',               2, False, 0x10f, 3, 10., 0x130a, 2,   'Wh'),  
  '-kWh3_t2'     : (116, 'kWh3_T2_exp',      'Phase 3 Exported Active Energy, Tariff 2',              'Phase 3 exported active energy',               3, False, 0x112, 3, 10., 0x130c, 2,   'Wh'),  
  '-kWh∑_t2'     : (117, 'kWhSYS_T2_exp',    'System Exported Active Energy, Tariff 2',               'System exported active energy',            'sys', False, 0x115, 3, 10., 0x130e, 2,   'Wh'),  
  '+kVAh1-L_t2'  : (118, 'kVAh1_L_T2_imp',   'Phase 1 Imported Inductive Apparent Energy, Tariff 2',  'Phase 1 imported lagging apparent energy',     1, False, 0x118, 3, 10., 0x1310, 2,  'VAh'),  
  '+kVAh2-L_t2'  : (119, 'kVAh2_L_T2_imp',   'Phase 2 Imported Inductive Apparent Energy, Tariff 2',  'Phase 2 imported lagging apparent energy',     2, False, 0x11b, 3, 10., 0x1312, 2,  'VAh'),  
  '+kVAh3-L_t2'  : (120, 'kVAh3_L_T2_imp',   'Phase 3 Imported Inductive Apparent Energy, Tariff 2',  'Phase 3 imported lagging apparent energy',     3, False, 0x11e, 3, 10., 0x1314, 2,  'VAh'),  
  '+kVAh∑-L_t2'  : (121, 'kVAhSYS_L_T2_imp', 'System Imported Inductive Apparent Energy, Tariff 2',   'System imported lagging apparent energy',  'sys', False, 0x121, 3, 10., 0x1316, 2,  'VAh'),  
  '-kVAh1-L_t2'  : (122, 'kVAh1_L_T2_exp',   'Phase 1 Exported Inductive Apparent Energy, Tariff 2',  'Phase 1 exported lagging apparent energy',     1, False, 0x124, 3, 10., 0x1318, 2,  'VAh'),  
  '-kVAh2-L_t2'  : (123, 'kVAh2_L_T2_exp',   'Phase 2 Exported Inductive Apparent Energy, Tariff 2',  'Phase 2 exported lagging apparent energy',     2, False, 0x127, 3, 10., 0x131a, 2,  'VAh'),  
  '-kVAh3-L_t2'  : (124, 'kVAh3_L_T2_exp',   'Phase 3 Exported Inductive Apparent Energy, Tariff 2',  'Phase 3 exported lagging apparent energy',     3, False, 0x12a, 3, 10., 0x131c, 2,  'VAh'),  
  '-kVAh∑-L_t2'  : (125, 'kVAhSYS_L_T2_exp', 'System Exported Inductive Apparent Energy, Tariff 2',   'System exported lagging apparent energy',  'sys', False, 0x12d, 3, 10., 0x131e, 2,  'VAh'),  
  '+kVAh1-C_t2'  : (126, 'kVAh1_C_T2_imp',   'Phase 1 Imported Capacitive Apparent Energy, Tariff 2', 'Phase 1 imported leading apparent energy',     1, False, 0x130, 3, 10., 0x1320, 2,  'VAh'),  
  '+kVAh2-C_t2'  : (127, 'kVAh2_C_T2_imp',   'Phase 2 Imported Capacitive Apparent Energy, Tariff 2', 'Phase 2 imported leading apparent energy',     2, False, 0x133, 3, 10., 0x1322, 2,  'VAh'),  
  '+kVAh3-C_t2'  : (128, 'kVAh3_C_T2_imp',   'Phase 3 Imported Capacitive Apparent Energy, Tariff 2', 'Phase 3 imported leading apparent energy',     3, False, 0x136, 3, 10., 0x1324, 2,  'VAh'),  
  '+kVAh∑-C_t2'  : (129, 'kVAhSYS_C_T2_imp', 'System Imported Capacitive Apparent Energy, Tariff 2',  'System imported leading apparent energy',  'sys', False, 0x139, 3, 10., 0x1326, 2,  'VAh'),  
  '-kVAh1-C_t2'  : (130, 'kVAh1_C_T2_exp',   'Phase 1 Exported Capacitive Apparent Energy, Tariff 2', 'Phase 1 exported leading apparent energy',     1, False, 0x13c, 3, 10., 0x1328, 2,  'VAh'),  
  '-kVAh2-C_t2'  : (131, 'kVAh2_C_T2_exp',   'Phase 2 Exported Capacitive Apparent Energy, Tariff 2', 'Phase 2 exported leading apparent energy',     2, False, 0x13f, 3, 10., 0x132a, 2,  'VAh'),  
  '-kVAh3-C_t2'  : (132, 'kVAh3_C_T2_exp',   'Phase 3 Exported Capacitive Apparent Energy, Tariff 2', 'Phase 3 exported leading apparent energy',     3, False, 0x142, 3, 10., 0x132c, 2,  'VAh'),  
  '-kVAh∑-C_t2'  : (133, 'kVAhSYS_C_T2_exp', 'System Exported Capacitive Apparent Energy, Tariff 2',  'System exported leading apparent energy',  'sys', False, 0x145, 3, 10., 0x132e, 2,  'VAh'),  
  '+kvarh1-L_t2' : (134, 'kvarh1_L_T2_imp',  'Phase 1 Imported Inductive Reactive Energy, Tariff 2',  'Phase 1 imported lagging reactive energy',     1, False, 0x148, 3, 10., 0x1330, 2, 'varh'),  
  '+kvarh2-L_t2' : (135, 'kvarh2_L_T2_imp',  'Phase 2 Imported Inductive Reactive Energy, Tariff 2',  'Phase 2 imported lagging reactive energy',     2, False, 0x14b, 3, 10., 0x1332, 2, 'varh'),  
  '+kvarh3-L_t2' : (136, 'kvarh3_L_T2_imp',  'Phase 3 Imported Inductive Reactive Energy, Tariff 2',  'Phase 3 imported lagging reactive energy',     3, False, 0x14e, 3, 10., 0x1334, 2, 'varh'),  
  '+kvarh∑-L_t2' : (137, 'kvarhSYS_L_T2_imp','System Imported Inductive Reactive Energy, Tariff 2',   'System imported lagging reactive energy',  'sys', False, 0x151, 3, 10., 0x1336, 2, 'varh'),  
  '-kvarh1-L_t2' : (138, 'kvarh1_L_T2_exp',  'Phase 1 Exported Inductive Reactive Energy, Tariff 2',  'Phase 1 exported lagging reactive energy',     1, False, 0x154, 3, 10., 0x1338, 2, 'varh'),  
  '-kvarh2-L_t2' : (139, 'kvarh2_L_T2_exp',  'Phase 2 Exported Inductive Reactive Energy, Tariff 2',  'Phase 2 exported lagging reactive energy',     2, False, 0x157, 3, 10., 0x133a, 2, 'varh'),  
  '-kvarh3-L_t2' : (140, 'kvarh3_L_T2_exp',  'Phase 3 Exported Inductive Reactive Energy, Tariff 2',  'Phase 3 exported lagging reactive energy',     3, False, 0x15a, 3, 10., 0x133c, 2, 'varh'),  
  '-kvarh∑-L_t2' : (141, 'kvarhSYS_L_T2_exp','System Exported Inductive Reactive Energy, Tariff 2',   'System exported lagging reactive energy',  'sys', False, 0x15d, 3, 10., 0x133e, 2, 'varh'),  
  '+kvarh1-C_t2' : (142, 'kvarh1_C_T2_imp',  'Phase 1 Imported Capacitive Reactive Energy, Tariff 2', 'Phase 1 imported leading reactive energy',     1, False, 0x160, 3, 10., 0x1340, 2, 'varh'),  
  '+kvarh2-C_t2' : (143, 'kvarh2_C_T2_imp',  'Phase 2 Imported Capacitive Reactive Energy, Tariff 2', 'Phase 2 imported leading reactive energy',     2, False, 0x163, 3, 10., 0x1342, 2, 'varh'),  
  '+kvarh3-C_t2' : (144, 'kvarh3_C_T2_imp',  'Phase 3 Imported Capacitive Reactive Energy, Tariff 2', 'Phase 3 imported leading reactive energy',     3, False, 0x166, 3, 10., 0x1344, 2, 'varh'),  
  '+kvarh∑-C_t2' : (145, 'kvarhSYS_C_T2_imp','System Imported Capacitive Reactive Energy, Tariff 2',  'System imported leading reactive energy',  'sys', False, 0x169, 3, 10., 0x1346, 2, 'varh'),  
  '-kvarh1-C_t2' : (146, 'kvarh1_C_T2_exp',  'Phase 1 Exported Capacitive Reactive Energy, Tariff 2', 'Phase 1 exported leading reactive energy',     1, False, 0x16c, 3, 10., 0x1348, 2, 'varh'),  
  '-kvarh2-C_t2' : (147, 'kvarh2_C_T2_exp',  'Phase 2 Exported Capacitive Reactive Energy, Tariff 2', 'Phase 2 exported leading reactive energy',     2, False, 0x16f, 3, 10., 0x134a, 2, 'varh'),  
  '-kvarh3-C_t2' : (148, 'kvarh3_C_T2_exp',  'Phase 3 Exported Capacitive Reactive Energy, Tariff 2', 'Phase 3 exported leading reactive energy',     3, False, 0x172, 3, 10., 0x134c, 2, 'varh'),  
  '-kvarh∑-C_t2' : (149, 'kvarhSYS_C_T2_exp','System Exported Capacitive Reactive Energy, Tariff 2',  'System exported leading reactive energy',  'sys', False, 0x175, 3, 10., 0x134e, 2, 'varh'),  
  # PARTIAL_COUNTER_VALUES
  '+kWh∑_prtl'    :(150, 'kWhSYS_PAR_imp',    'System Imported Active Energy, Partial',               'System imported active energy',           'sys', False, 0x0400, 3, 10., 0x1400, 2,   'Wh'),
  '-kWh∑_prtl'    :(151, 'kWhSYS_PAR_exp',    'System Exported Active Energy, Partial',               'System exported active energy',           'sys', False, 0x0403, 3, 10., 0x1402, 2,   'Wh'),
  '+kVAh∑-L_prtl' :(152, 'kVAhSYS_L_PAR_imp', 'System Imported Inductive Apparent Energy, Partial',   'System imported lagging apparent energy', 'sys', False, 0x0406, 3, 10., 0x1404, 2,  'VAh'),
  '-kVAh∑-L_prtl' :(153, 'kVAhSYS_L_PAR_exp', 'System Exported Inductive Apparent Energy, Partial',   'System exported lagging apparent energy', 'sys', False, 0x0409, 3, 10., 0x1406, 2,  'VAh'),
  '+kVAh∑-C_prtl' :(154, 'kVAhSYS_C_PAR_imp', 'System Imported Capacitive Apparent Energy, Partial',  'System imported leading apparent energy', 'sys', False, 0x040C, 3, 10., 0x1408, 2,  'VAh'),
  '-kVAh∑-C_prtl' :(155, 'kVAhSYS_C_PAR_exp', 'System Exported Capacitive Apparent Energy, Partial',  'System exported leading apparent energy', 'sys', False, 0x040F, 3, 10., 0x140A, 2,  'VAh'),
  '+kvarh∑-L_prtl':(156, 'kvarhSYS_L_PAR_imp','System Imported Inductive Reactive Energy, Partial',   'System imported lagging reactive energy', 'sys', False, 0x0412, 3, 10., 0x140C, 2, 'varh'),
  '-kvarh∑-L_prtl':(157, 'kvarhSYS_L_PAR_exp','System Exported Inductive Reactive Energy, Partial',   'System exported lagging reactive energy', 'sys', False, 0x0415, 3, 10., 0x140E, 2, 'varh'),
  '+kvarh∑-C_prtl':(158, 'kvarhSYS_C_PAR_imp','System Imported Capacitive Reactive Energy, Partial',  'System imported leading reactive energy', 'sys', False, 0x0418, 3, 10., 0x1410, 2, 'varh'),
  '-kvarh∑-C_prtl':(159, 'kvarhSYS_C_PAR_exp','System Exported Capacitive Reactive Energy, Partial',  'System exported leading reactive energy', 'sys', False, 0x041B, 3, 10., 0x1412, 2, 'varh'),
  # BALANCE_VALUES
  'kWh∑'      :    (160, 'kWhSYS_BIL',    'System Active Energy, Balance',                     'System active energy',           'sys', True,  0x041E, 3, 10., 0x1414, 2,   'Wh'),
  'kVAh∑-L'   :    (161, 'kVAhSYS_L_BIL', 'System Inductive Apparent Energy, Balance',         'System lagging apparent energy', 'sys', True,  0x0421, 3, 10., 0x1416, 2,  'VAh'),
  'kVAh∑-C'   :    (162, 'kVAhSYS_C_BIL', 'System Capacitive Apparent Energy, Balance',        'System leading apparent energy', 'sys', True,  0x0424, 3, 10., 0x1418, 2,  'VAh'),
  'kvarh∑-L'  :    (163, 'kvarhSYS_L_BIL','System Inductive Reactive Energy, Balance',         'System lagging reactive energy', 'sys', True,  0x0427, 3, 10., 0x141A, 2, 'varh'),
  'kvarh∑-C'  :    (164, 'kvarhSYS_C_BIL','System Capacitive Reactive Energy, Balance',        'System leading reactive energy', 'sys', True,  0x042A, 3, 10., 0x141C, 2, 'varh'),
  # partially from COUNTER COMMUNICATION
  'at' :  (165,      'ACTUAL_TARIFF_(EC)',   'Actual Tariff',                              '',                               'sys', False, 0x050B, 1, 1, None, None, None),
  'psv':  (166,      'PRI_S(EC)_VALUE_(EC)', 'Pri/Sec Value',                              '',                               'sys', False, 0x050C, 1, 1, None, None, None),
}

#REAL_TIME_LIST = list(range(0, 30))
REAL_TIME_LIST = [
  'V1', 'V2', 'V3', 'V12', 'V23', 'V31', 'V∑', 'A1', 'A2', 'A3', 'AN', 'A∑',
  'PF1', 'PF2', 'PF3', 'PF∑', 'P1', 'P2', 'P3', 'P∑',
  'S1', 'S2', 'S3', 'S∑', 'Q1', 'Q2', 'Q3', 'Q∑', 'F', 'ps',
]

#COUNTER_LIST_TOTAL   = list(range(30, 70))
COUNTER_LIST_TOTAL = [
  '+kWh1',     '+kWh2',     '+kWh3',     '+kWh∑',     '-kWh1',     '-kWh2',     '-kWh3',     '-kWh∑',
  '+kVAh1-L',  '+kVAh2-L',  '+kVAh3-L',  '+kVAh∑-L',  '-kVAh1-L',  '-kVAh2-L',  '-kVAh3-L',  '-kVAh∑-L',
  '+kVAh1-C',  '+kVAh2-C',  '+kVAh3-C',  '+kVAh∑-C',  '-kVAh1-C',  '-kVAh2-C',  '-kVAh3-C',  '-kVAh∑-C',
  '+kvarh1-L', '+kvarh2-L', '+kvarh3-L', '+kvarh∑-L', '-kvarh1-L', '-kvarh2-L', '-kvarh3-L', '-kvarh∑-L',
  '+kvarh1-C', '+kvarh2-C', '+kvarh3-C', '+kvarh∑-C', '-kvarh1-C', '-kvarh2-C', '-kvarh3-C', '-kvarh∑-C'
]
#COUNTER_LIST_TARIFF1 = list(range(70, 110))
COUNTER_LIST_TARIFF1 = [el + '_t1' for el in COUNTER_LIST_TOTAL]
#COUNTER_LIST_TARIFF2 = list(range(110, 150))
COUNTER_LIST_TARIFF2 = [el + '_t2' for el in COUNTER_LIST_TOTAL]

#PARTIAL_COUNTER_LIST = list(range(150, 160))
PARTIAL_COUNTER_LIST = [
  '+kWh∑_prtl',     '-kWh∑_prtl',
  '+kVAh∑-L_prtl',  '-kVAh∑-L_prtl',  '+kVAh∑-C_prtl',  '-kVAh∑-C_prtl', 
  '+kvarh∑-L_prtl', '-kvarh∑-L_prtl', '+kvarh∑-C_prtl', '-kvarh∑-C_prtl'
]

#BALANCE_LIST = list(range(160, 165))
BALANCE_LIST = ['kWh∑', 'kVAh∑-L', 'kVAh∑-C', 'kvarh∑-L', 'kvarh∑-C']

#RR_LIST = list(range(0, 167))
RR_LIST = REAL_TIME_LIST + COUNTER_LIST_TOTAL + COUNTER_LIST_TARIFF1 + COUNTER_LIST_TARIFF2 + PARTIAL_COUNTER_LIST + BALANCE_LIST + ['at', 'psv']


COUNTER_COMMUNICATION_DATA_RAW = {
  'mapping' :
  {
   'key'  : 'code',
    0     : 'xml_name',
    1     : 'descr',
    2     : 'reg_int_start_addr',
    3     : 'reg_int_num_words',
  },
  'serial'     : ('ec_serial', 'Energy counter serial number',                       0x0500, 5, ),
  'model'      : ('model',     'Energy counter model',                               0x0505, 1, ),
  'type'       : ('type',      'Energy counter type',                                0x0506, 1, ),
  'firmware'   : ('fw',        'Energy counter firmware release',                    0x0507, 1, ),
  'hardware'   : ('hw',        'Energy counter hardware version',                    0x0508, 1, ),
 #'6'          : (None,        'Reserved',                                           0x0509, 2, ),
  'tariff'     : (None,        'Tariff in use',                                      0x050B, 1, ),
  'pri_sec'   :  (None,        'Primary/secondary value',                            0x050C, 1, ),
  'error'      : (None,        'Energy counter error code',                          0x050D, 1, ),
 #'ct'         : (None,        'ct_ratio', 'CT value (only for counter 6A 3phase model)',        0x050E, 1, ),
 #'11'         : (None,        'Reserved',                                           0x050F, 2, ),
  'fsa'        : ('fsa',       'Current full scale value (A)',                       0x0511, 1, ),
  'wiring'     : ('wmode',     'Wiring mode',                                        0x0512, 1, ),
 #'14'         : (None,        'MODBUS address (not available for MODBUS TCP)',      0x0513, 1, ),
 #'15'         : (None,        'MODBUS mode (not available for MODBUS TCP)',         0x0514, 1, ),
 #'16'         : (None,        'Communication speed (not available for MODBUS TCP)', 0x0515, 1, ),
 #'17'         : (None,        'Reserved',                                           0x0516, 2, ),
  'partial'    : (None,        'Partial counters status',                            0x0517, 1, ),
  'm_serial'   : (None,        'Module serial number',                               0x0518, 5, ),
 #'svr'        : (None,        'Signed value representation',                        0x051D, 1, ),
 #'21'         : (None,        'Reserved',                                           0x051E, 1, ),
  'm_firmware' : (None,        'Module firmware release',                            0x051F, 1, ),
  'm_hardware' : (None,        'Module hardware version',                            0x0520, 1, ),
 #'24'         : (None,        'Reserved',                                           0x0521, 2, ),
 #'25'         : (None,        'Register set type',                                  0x0523, 1, ),
}

# XML element name in
# http://192.168.178.253/cgi-bin/state?xml=1
# status          1
# status_str      Active
# ec_serial       AB1OB00424
# fw              01.02
# hw              02.00
# wmode           3Phase/4Wire-3CT
# model           EC80A 3Phase 4Wire
# type            MID
# ct_ratio        1
# err             -
# fsa             80
# 
# oor0            0  (indicates no error)
# ...
# oor23           0

COUNTER_COMMUNICATION_DATA_LIST = [
  'serial', 'model', 'type', 'firmware', 'hardware', 'tariff', 'pri_sec', 'error',
  'fsa', 'wiring', 'partial', 'm_serial', 'm_firmware', 'm_hardware',
]

# for the coils:
# http://192.168.178.253/cgi-bin/counters?xml=refresh_items
# 
# <root>
#   <ustate>0</ustate>
#   <cstate>1023</cstate>
# </root>

COILS_RAW = {
  'mapping' :
  {
   'key'  : 'code',
    0     : 'descr',
  },
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

# Limits/Thresholds triggering the COILS:
# (Vnom = 3x230/400 V ... 3x240/415 V)
#
# * Phase Voltage:
#   * UVL-n: Vnom -20%
#   * OVL-n: Vnom +20%
#
# * Line Voltage:
#   * UVL-L: Vnom * √3 -20%
#   * OVL-L: Vnom * √3 +20%
#
# * Current:
#   * UI: Start current value (Ist)
#   * OI: Full scale value (FS)
#
# * Frequency:
#   * F low: 45Hz
#   * F high: 65Hz

COILS_LIST = [
  'OV∑', 'OV1', 'OV2', 'OV3', 'UV∑', 'UV1', 'UV2', 'UV3',
  'OV12', 'OV23', 'OV31', 'UV12', 'UV23', 'UV31', 'RES', 'COM',
  'UI3', 'UIN', 'RES', 'RES', 'RES', 'RES', 'RES', 'RES',
  'OI∑', 'OI1', 'OI2', 'OI3', 'OIN', 'UI∑', 'UI1', 'UI2',
  'F', 'RES', 'RES', 'RES', 'RES', 'RES', 'RES', 'RES',
]

def convert_registers(reg_dict):
    ret_dict = dict()
    mapping = reg_dict['mapping']
    for key in reg_dict:
        if key == 'mapping': continue
        tpl = reg_dict[key] # tuple
        register = dict()
        for m in mapping:
            if type(m) == int:
                register[mapping[m]] = tpl[m]
            elif m == 'key':
                register[mapping[m]] = key
        ret_dict[key] = register
    return ret_dict

RR = convert_registers(RR_RAW)
COUNTER_COMMUNICATION_DATA = convert_registers(COUNTER_COMMUNICATION_DATA_RAW)
COILS = convert_registers(COILS_RAW)

class U180CException(NameError):
    pass

class U180CAuthException(NameError):
    pass

class U180CConnectionException(U180CException):
    pass

class U180C(object):

    def __init__(self, host, port=502):
        self.host = host
        self.port = port
        import pymodbus.client.sync
        import pymodbus.exceptions
        self.pymodbus = pymodbus
        try:
            self.client = self.pymodbus.client.sync.ModbusTcpClient(host, port=502)
            self.client.connect()
            self.set_properties()
        except pymodbus.exceptions.ConnectionException:
            raise U180CConnectionException('Cannot connect')

    def set_properties(self):
        conf_vals = self.read_cc()
        for conf, val in conf_vals:
            if conf['code'] == 'serial':
                self.serial = val

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

    @property
    def real_time_measures(self):
        return self.read_ieee_registers(REAL_TIME_LIST)

    @property
    def counters_total(self):
        return self.read_ieee_registers(COUNTER_LIST_TOTAL)

    @property
    def counters_tariff1(self):
        return self.read_ieee_registers(COUNTER_LIST_TARIFF1)

    @property
    def counters_tariff2(self):
        return self.read_ieee_registers(COUNTER_LIST_TARIFF2)

    @property
    def counters_partial(self):
        return self.read_ieee_registers(PARTIAL_COUNTER_LIST)

    @property
    def counters_balance(self):
        return self.read_ieee_registers(BALANCE_LIST)

    @property
    def all_measures(self):
        return self.real_time_measures + self.counters_total + self.counters_tariff1 + self.counters_tariff2 + self.counters_partial + self.counters_balance

    def read_coherent_block(self, register_list):
        num_words = sum([RR[key]['reg_int_num_words'] for key in register_list])
        rr = self.client.read_input_registers(RR[register_list[0]]['reg_int_start_addr'], num_words)
        assert rr.function_code < 0x80
        assert len(rr.registers) == num_words
        ret_list = []
        pos = 0
        for key in RR_RT_ORDER:
            reg = RR[key]
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

    def reset_counters(self, which='all counters'):
        """ Will work only if your counter is resettable! """
        which_map = {
          'total counters': 0x0,
          'tariff 1 counters': 0x1,
          'tariff 2 counters': 0x2,
          'all counters': 0x3
        }
        rr = self.client.write_registers(0x0516, [which_map[which]])
        assert rr.function_code < 0x80, 'Error: returned function code is ' + hex(rr.function_code)

    def start_partial_counters(self, which='all'):
        self.write_partial_settings(which, 'start')

    def stop_partial_counters(self, which='all'):
        self.write_partial_settings(which, 'stop')

    def reset_partial_counters(self, which='all'):
        self.write_partial_settings(which, 'reset')

    def write_partial_settings(self, which, action):
        if type(which) in (list, tuple):
            for pc in which:
                self.write_partial_setting(pc, action)
        elif which == 'all':
            self.write_partial_setting(which, action)
        else:
            raise NameError('Using this function incorrectly with ' + which + ' as parameter.')

    def start_partial_counter(self, which):
        self.write_partial_setting(which, 'start')

    def stop_partial_counter(self, which):
        self.write_partial_setting(which, 'stop')

    def reset_partial_counter(self, which):
        self.write_partial_setting(which, 'reset')

    def write_partial_setting(self, which, action):
        which_map = {
          '+kWh∑ PAR':     0x0, '-kWh∑ PAR':     0x1,
          '+kVAh∑-L PAR':  0x2, '-kVAh∑-L PAR':  0x3,
          '+kVAh∑-C PAR':  0x4, '-kVAh∑-C PAR':  0x5,
          '+kvarh∑-L PAR': 0x6, '-kvarh∑-L PAR': 0x7,
          '+kvarh∑-C PAR': 0x8, '-kvarh∑-C PAR': 0x9,
          'all': 0xA
        }
        action_map = {
          'start': 0x1,
          'stop':  0x2,
          'reset': 0x3,
        }
        byte1 = which_map[which]
        byte2 = action_map[action]
        rr = self.client.write_registers(0x0517, [byte1 << 8 | byte2])
        assert rr.function_code < 0x80, 'Error: returned function code is ' + hex(rr.function_code)

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
try:
    clock = time.perf_counter
except AttributeError:
    clock = time.time

class U180CWeb(object):

    MIN_INTERVAL = 5.

    def __init__(self, host):
        self.host = host
        self.last = clock() - 100000
        self._cookies = None
        import requests
        import xml.dom.minidom
        self.requests = requests
        self.minidom = xml.dom.minidom
        self.authenticated = False
        self.update_values(set_serial = True)

    def update_values(self, set_serial=False):
        if clock() - self.last < self.MIN_INTERVAL: return
        self.last = clock()
        r = self.http_get('{host}/tmp/index.readings.xml?{timestamp}'.format(host=self.host, timestamp=int(time.time())))
        dom = self.minidom.parseString(r.text)
        addr = dom.getElementsByTagName('readings')[0].firstChild.nodeValue
        r = self.http_get('{host}/tmp/{addr}_readings.xml?{timestamp}'.format(host=self.host, addr=addr, timestamp=int(time.time())))
        dom = self.minidom.parseString(r.text)
        root = dom.firstChild
        if set_serial:
            self.serial = root.getElementsByTagName('sn')[0].firstChild.nodeValue
        datet = root.getElementsByTagName('datet')[0].firstChild.nodeValue
        da, ti = datet.split()
        da = da.split('/')
        ti = ti.split(':')
        datet = [int(el) for el in reversed(da)] + [int(el) for el in ti]
        datet = dt(*datet)
        #import pdb; pdb.set_trace()
        paracnt = root.getElementsByTagName('paracnt')[0].firstChild.nodeValue
        sn = root.getElementsByTagName('sn')[0].firstChild.nodeValue
        assert int(paracnt) == 167
        ret_list = []
        for key in RR_LIST:
            rd = RR[key].copy()
            val = root.getElementsByTagName('param'+str(rd['api_no']))[0].firstChild.nodeValue
            ret_list.append((rd, val))
        self._values = ret_list
        return

    @property
    def counters_total(self):
        self.update_values()
        return [val for val in self._values if val[0]['code'] in COUNTER_LIST_TOTAL]

    @property
    def counters_balance(self):
        self.update_values()
        return [val for val in self._values if val[0]['code'] in BALANCE_LIST]

    @property
    def counters_tariff1(self):
        self.update_values()
        return [val for val in self._values if val[0]['code'] in COUNTER_LIST_TARIFF1]

    @property
    def counters_tariff2(self):
        self.update_values()
        return [val for val in self._values if val[0]['code'] in COUNTER_LIST_TARIFF2]

    @property
    def counters_partial(self):
        self.update_values()
        return [val for val in self._values if val[0]['code'] in PARTIAL_COUNTER_LIST]

    @property
    def all_measures(self):
        self.update_values()
        return self._values

    @property
    def real_time_measures(self):
        self.update_values()
        return [val for val in self._values if val[0]['code'] in REAL_TIME_LIST]

    def http_get(self, *args, **kwargs):
        if self._cookies:
            kwargs['cookies'] = self._cookies
        return self.requests.get(*args, **kwargs)

    def logout(self):
        r = self.http_get('{host}/cgi-bin/index'.format(host=self.host))
        if 'Logout' in r.text:
            r = self.http_get('{host}/cgi-bin/index?logout=1'.format(host=self.host))
            self.authenticated = False

    def authenticate(self, username='admin', password='admin'):
        r = self.http_get('{host}/cgi-bin/index'.format(host=self.host))
        if 'Logout' in r.text:
            self.authenticated = True
            return True
        data = {
          'action': 'login',
          'login': 'Login',
          'password': password,
          'user': username
        }
        r = self.requests.post('{host}/cgi-bin/index'.format(host=self.host), data=data)
        if 'Logout' in r.text:
            self.authenticated = True
            self._cookies = r.cookies
            return True
        else:
            return False

    def read_coils(self):
        if not self.authenticated: raise U180CAuthException('Need to authenticate before calling this function')
        r = self.http_get('{host}/cgi-bin/counters?xml=refresh_items'.format(host=self.host))
        # <root>
        #   <ustate>0</ustate>
        #   <cstate>1023</cstate>
        # </root>
        dom = self.minidom.parseString(r.text)
        root = dom.firstChild
        ustate = root.getElementsByTagName('ustate')[0].firstChild.nodeValue
        cstate = root.getElementsByTagName('cstate')[0].firstChild.nodeValue
        #import pdb; pdb.set_trace()
        return []

    def close(self):
        self.logout()

    def read_state(self):
        if not self.authenticated: raise U180CAuthException('Need to authenticate before calling this function')
        r = self.http_get('{host}/cgi-bin/state?xml=1'.format(host=self.host))
        #import pdb; pdb.set_trace()
        dom = self.minidom.parseString(r.text)
        root = dom.firstChild

def U180CFactory(connection_string):
    cs = connection_string
    if cs.startswith('http://'):
        return U180CWeb(cs)
    else:
        return U180C(cs)

