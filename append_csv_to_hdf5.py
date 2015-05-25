#!/usr/bin/env python

import pandas as pd
import numpy as np
# Python Std Lib
from itertools import product
import glob
import os
import sys
from datetime import datetime as dt

def read_csv(filename):
    df = pd.io.parsers.read_csv(filename, sep=';', parse_dates=[['Date', 'Time']], dayfirst=True)
    df.set_index('Date_Time', inplace = True)
    cols_to_drop = 'SN', 'ACTUAL_TARIFF_(EC)', 'PRI_S(EC)_VALUE_(EC)'
    for col in cols_to_drop:
        if col in df.columns: df.drop(col, axis=1, inplace = True)
    if 'kWh SYS_exp' in df.columns:
        df['kWhSYS_exp'] = df['kWh SYS_exp']
        df.drop('kWh SYS_exp', axis=1, inplace = True)
    ## divide columns with kW / kVA / kvar by 1000 to get the unit right:
    #relevant_fragments = ['kW', 'kVA', 'kvar']
    #relevant_fragments += [''.join(p) for p in product(['P', 'S', 'Q'], ['1', '2', '3', 'SYS'])]
    #for col in df.columns:
    #    if any(x in col for x in relevant_fragments):
    #        df[col] = df[col]/1000.
    # change all columns of type np.float64 to type np.float32:
    for column in df.columns:
        if df[column].dtype == np.float64:
            df[column] = df[column].astype(np.float32)
    # Finished reading the data file in
    return df

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Append data from a Gossen U180C/U189A CSV file to an HDF5 file on a daily basis')
    parser.add_argument('log_folder', help='The folder containing the log files')
    parser.add_argument('output_file', help='The data file to append to')
    args = parser.parse_args()

    store = pd.HDFStore(args.output_file)

    basenames = []
    try:
        # only works if basename is a data column:
        #basenames = list(store.select_column('logfiles', 'basename'))
        basenames = list(store.select('logfiles').basename)
    except KeyError:
        pass
    print("Log files already stored in the HDF5 file:")
    print('\n'.join(basenames))

    for logfile in glob.glob(args.log_folder):
        print("Checking {}".format(logfile))
        if os.path.basename(logfile) not in basenames:
            print("Adding the logfile {} to the HDF5 file.".format(logfile))
            added_logfiles = {'path': [], 'basename': [], 'dt': []}
            added_logfiles['path'].append(logfile)
            added_logfiles['basename'].append(os.path.basename(logfile))
            added_logfiles['dt'].append(dt.now())
            df = read_csv(logfile)
            store.append('df', df, format='t', complib=None)
            #store.append('df', df, format='t', complib='zlib')
            #store.append('df', df, format='t', complib='lzo', data_columns=True)
            #store.append('df', df, format='t', complib=None, data_columns=True)
            logfiles = pd.DataFrame.from_dict(added_logfiles)
            logfiles.set_index('dt', drop=True, inplace=True)
            store.append('logfiles', logfiles, format='t', append=True)
    store.close()

    ## Calculate unique dates from the timestamp index column:
    #unique_dates = store.select_column('df', 'index').apply(lambda x: x.date()).unique()

    ## Get the day 2015-04-15 from the dataframe:
    #start_date = '2015-04-15'
    #end_date = '2015-04-16'
    #pd.read_hdf(args.output_file,'df',where='index > start_date & index < end_date')

if __name__ == "__main__":
    main()
