#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from matplotlib import pyplot as plt, pylab
import matplotlib.dates as mdates
import numpy as np
#import seaborn as sns
#sns.set(palette="Set2")
import sys
from itertools import product
from datetime import datetime as dt, timedelta, date
import datetime
import os
import argparse
import inspect

# change the default plot size:
pylab.rcParams['figure.figsize'] = 10, 6


DPI = 200

class U180CPlotService(object):

    def __init__(self, store, output_folder):
        self.store = store
        self.output_folder = output_folder
        self.df = store.select('df')
        try:
            os.makedirs(self.output_folder)
        except FileExistsError:
            pass

        min_max = self.min_max_datetime()
        print("Min: {}".format(min_max[0].isoformat(sep=' ')))
        print("Max: {}".format(min_max[1].isoformat(sep=' ')))

        print("Number of Days: {}".format(self.number_of_days()))

        self.check_early_late_data()
        self.check_num_datapoints()

    def check_early_late_data(self):
        print(self.days_with_early_and_late_data())
        print()

    def check_num_datapoints(self):
        ndp = self.num_datapoints_daily()
        print("Dates with too many datapoints:")
        print(ndp[ndp > 17000])
        print()
        print("Dates with an insufficent number of datapoints:")
        print(ndp[ndp < 16000])
        print()

    def plot_all(self):
        """ We call all methods with a name that ends with _plot """
        for method_name in self.available_plots():
            self.plot_individual(method_name)

    def available_plots(self):
        plot_methods = []
        for method in inspect.getmembers(self, predicate=inspect.ismethod):
            method_name = method[0]
            if method_name.endswith('_plot'):
                plot_methods.append(method_name)
        return plot_methods

    def plot_individual(self, method_name):
        method = getattr(self, method_name)
        print(' -   {:40s}'.format(method_name+'()'), end='  ')
        docstring = method.__doc__
        if docstring:
            print(docstring.strip())
        else:
            print()
        method()

    def power_single_plot(self):
        """ Power of all phases over time. """
        number_of_days = self.number_of_days()
        figsize = (min(5*number_of_days, 30000/DPI), 6)
        fig = plt.figure(num=None, figsize=figsize, dpi=DPI, facecolor='w', edgecolor='k')
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
        self.df.ix[:,['P1','P2','P3']].plot(ax=ax)
        ax.xaxis.grid(True, which="minor")
        ax.xaxis.grid(True, which="major")
        plt.savefig(self.fn('power_over-time_P1_P2_P3.png'), bbox_inches='tight')

    def five_min_avg_min_max_band_plot(self):
        """ 5min avg and min-max-band plot """
        dfr = self.df.loc[:,['P1', 'P2', 'P3', 'PSYS']].resample("5min", how=['min', 'max', 'mean'])
        # for the phases individually:
        number_of_days = self.number_of_days()
        figsize = (min(5*number_of_days, 30000/DPI), 6)
        fig = plt.figure(num=None, figsize=figsize, dpi=DPI, facecolor='w', edgecolor='k')
        ax = fig.add_axes([0.05, 0.05, 0.9, 0.9])
        ax.plot(dfr.index, dfr.P1['mean'])
        ax.fill_between(dfr.index, dfr.P1['min'],dfr.P1['max'],facecolor='b',alpha=0.5)
        ax.plot(dfr.index, dfr.P2['mean'])
        ax.fill_between(dfr.index, dfr.P2['min'],dfr.P2['max'],facecolor='g',alpha=0.5)
        ax.plot(dfr.index, dfr.P3['mean'])
        ax.fill_between(dfr.index, dfr.P3['min'],dfr.P3['max'],facecolor='r',alpha=0.5)
        plt.savefig(self.fn('5m_avg_min-max-band_P1_P2_P3.png'), bbox_inches='tight')
        # or for the sum of all phases:
        figsize = (min(5*number_of_days, 30000/DPI), 6)
        fig = plt.figure(num=None, figsize=figsize, dpi=DPI, facecolor='w', edgecolor='k')
        ax = fig.add_axes([0.05, 0.05, 0.9, 0.9])
        ax.plot(dfr.index, dfr.PSYS['mean'])
        ax.fill_between(dfr.index, dfr.PSYS['min'],dfr.PSYS['max'],facecolor='r',alpha=0.5)
        plt.savefig(self.fn('5m_avg_min-max-band_PSYS.png'), bbox_inches='tight')

    def power_diff_histo_plot(self):
        """ Power differences of the different phases for each day (individual plots per phase). """

        def diffs(ds, max_periods=4):
            # input: data series
            data = ds.diff(periods=1)
            periods = 2
            while periods <= max_periods:
                data = data.append(ds.diff(periods=periods))
                periods += 1
            return data.abs()
        
        def day_diff_hists(ds, nbins, first_date, last_date, start_end=(0.0, 3.0)):
            # ds: data series
            # returns a matrix with one power diff histogram per day
            ndays = (last_date - first_date).days + 1
            gd = np.zeros([ndays, nbins])
            bins = None
            i = 0
            while i < ndays:
                d = diffs(ds[(first_date + timedelta(days=i)).isoformat()])
                histo = np.histogram(d, range=start_end, bins=nbins)
                if bins is None: bins = histo[1]
                # http://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram.html
                #for j in range(day_scaler):
                #    gd[i*day_scaler+j,:] = histo[0]
                gd[i] = histo[0]
                i += 1
            return gd
        
        for measure in ('P1', 'P2', 'P3', 'PSYS'):
            first_date, last_date = self.min_max_date()
            ndays = (last_date - first_date).days + 1
            nbins = 400
            start_end = (0,4000)
            first_dt = dt.combine(first_date, datetime.time(0))
            last_dt = dt.combine(last_date+timedelta(days=1), datetime.time(0))
            y_lims = (first_dt, last_dt)
            y_lims = mdates.date2num(y_lims)
            y_lims = list(y_lims)
            y_lims = list(reversed(y_lims))
            x_lims = [0, start_end[1]]
            extent = x_lims + y_lims
            gd = day_diff_hists(self.df[measure], nbins, first_date, last_date, start_end=start_end)
            ld = np.log10(gd)
            fig, ax = plt.subplots()
            ax.imshow(ld, aspect=0.5*start_end[1]/ndays, extent=extent, interpolation='nearest')
            ax.yaxis_date()
            plt.title('Daily Power Diff Histograms for {}'.format(measure))
            plt.savefig(self.fn('histogram_each_day_{}.png'.format(measure)), bbox_inches='tight')

    def power_over_the_day_plot(self):
        """ Power over the day, plottet in 2D as date vs time of the day (individual plots per phase) """

        def day_power(ds, first_date, ndays):
            # ds: data series
            # returns a matrix with one power diff histogram per day
            ds = ds.resample('2min')
            if ds.index[0].time() != datetime.time(0, 0):
                # enlarging the DataFrame at the start of the data (to a full day)
                ds.loc[dt.combine(ds.index[0].date(), datetime.time(0,0))] = float('nan')
            if ds.index[-1].time() != datetime.time(0, 0):
                # enlarging the DataFrame at the end of the data (to a full day)
                ds.loc[dt.combine(ds.index[-1].date()+timedelta(days=1), datetime.time(0,0))] = float('nan')
            ds = ds.resample('2min')
            gd = np.zeros([ndays, int(60*60*24/120)])
            i = 0
            while i < ndays:
                gd[i] = ds[(first_date + timedelta(days=i)).isoformat()]
                i += 1
            return gd

        for measure in ('P1', 'P2', 'P3', 'PSYS'):
            # Date/Time as axis label on imshow():
            # http://stackoverflow.com/a/23142190/183995
            first_date, last_date = self.min_max_date()
            nbins = 200
            ndays = (last_date - first_date).days + 1
            gd = day_power(self.df[measure], first_date, ndays)
            ld = np.log10(gd)
            first_dt = dt.combine(first_date, datetime.time(0))
            last_dt = dt.combine(last_date+timedelta(days=1), datetime.time(0))
            x_lims = (first_dt, first_dt+timedelta(days=1))
            # http://matplotlib.org/api/dates_api.html#matplotlib.dates.date2num
            x_lims = mdates.date2num(x_lims)
            x_lims = [x_lims[0] + 0.0, x_lims[1] - 0.0]
            y_lims = (first_dt, last_dt)
            y_lims = mdates.date2num(y_lims)
            y_lims = list(y_lims)
            #y_lims = [first_date.day, last_date.day]
            y_lims = list(reversed(y_lims))
            fig, ax = plt.subplots()
            ax.imshow(ld, aspect=0.5 * 1/ndays, extent=x_lims+y_lims, interpolation='none')
            ax.xaxis_date()
            ax.yaxis_date()
            time_format = mdates.DateFormatter('%H:%M:%S')
            ax.xaxis.set_major_formatter(time_format)
            #ax.yaxis.set_major_formatter(date_format)
            # This simply sets the x-axis data to diagonal so it fits better.
            fig.autofmt_xdate() 
            plt.title('Power {}'.format(measure))
            #cbar = plt.colorbar() 
            #cbar.set_label('Power consumption',size=18)
            plt.savefig(self.fn('power_over_the_day_{}.png'.format(measure)), bbox_inches='tight')

    def total_energy_detrended_plot(self):
        """ Plots the energy counter value of time with its overall linear trend removed """

        colname = 'kWhSYS_BIL'

        col = self.df[colname]

        # pip install statsmodels patsy
        dfr = self.df[colname].resample('30min', how='mean')
        #dfr /= 1000.
        dfr = dfr.dropna()
        dfr = dfr.reset_index()
        #dfr.Date_Time.apply(lambda x: int(x.timestamp()))
        x = dfr.Date_Time.astype(np.int64) // 10**9 # ns -> s
        #x /= 3600. # s -> h
        y = dfr[colname]
        model = pd.ols(y=y, x=x)
        x = x.values
        x = (x[0], x[-1])
        y = model.predict(x=pd.Series(x))
        x = pd.to_datetime(x, unit='s')
        #plt.plot(x, y)
        y = y.values
        ols_df = pd.Series(y, x)

        y_range = y[1] - y[0]
        time_range = x[1] - x[0]

        ac_series = dfr[colname] - y_range * ((dfr.Date_Time - dfr.Date_Time.min())/time_range)
        #ac_series -= dfr[colname][0]
        ac_series -= y[0]
        ac_series /= 1000.
        slope = y_range / time_range.total_seconds() / 1000 * 24*3600

        plt.figure()
        ax = ac_series.plot()
        #ols_df.plot(ax=ax)
        ax.plot((ac_series.index.min(), ac_series.index.max()), (0,0), 'r-')
        ax.set_ylabel('Total energy consumed w/o linear trend [kWh]')
        ax.set_xlabel('')
        kwargs = dict(horizontalalignment='center',verticalalignment='center',transform = ax.transAxes)
        linear_trend_msg = 'Linear trend (average power): {:.1f} kWh/day = {:.0f} W'.format(slope, slope*1000/24)
        ax.text(0.5, 0.15, linear_trend_msg, **kwargs)
        ax.text(0.5, 0.10, 'Positive slope:   over  avg consumption', **kwargs)
        ax.text(0.5, 0.05, 'Negative slope: under avg consumption', **kwargs)
        plt.savefig(self.fn('total_energy_detrended.png'), bbox_inches='tight')

    def energy_consumed_per_day_plot(self):
        """ energy consumed (on each phase) per day """
        dfr = self.df.loc[:,['kWh1_imp','kWh2_imp', 'kWh3_imp']].resample("D", how=['min', 'max'])
        dfr['L1'] = dfr['kWh1_imp']['max'] - dfr['kWh1_imp']['min']
        dfr['L2'] = dfr['kWh2_imp']['max'] - dfr['kWh2_imp']['min']
        dfr['L3'] = dfr['kWh3_imp']['max'] - dfr['kWh3_imp']['min']
        dfr.columns = dfr.columns.droplevel(level=1)
        dfr = dfr.loc[:, ['L1', 'L2', 'L3']]
        complete_data = self.days_with_early_and_late_data()
        for date_time in complete_data.index:
            if not complete_data.ix[date_time]:
                dfr.ix[date_time]['L1'] = float('nan')
                dfr.ix[date_time]['L2'] = float('nan')
                dfr.ix[date_time]['L3'] = float('nan')
        dfr /= 1000.
        dfr['all'] = dfr.L1 + dfr.L2 + dfr.L3
        ax = dfr.plot(title='energy used per day', lw=2,colormap='jet',marker='.',markersize=10)
        ax.set_ylabel("kWh")
        plt.savefig(self.fn('energy_consumed_per_day.png'), bbox_inches='tight')

    def fn(self, name):
        """ returns the full filename """
        return os.path.join(self.output_folder, name)

    def days_with_early_and_late_data(self, minutes_from_midnight = 10):
        # minutes_from_midnight max value : 60
        dweald = dict(Date_Time=[], early_late_data=[])
        for grp, daydf in self.df.groupby(pd.TimeGrouper('D')):
            dweald['Date_Time'].append(grp)
            early_data = daydf.ix[daydf.index.indexer_between_time(datetime.time(0), datetime.time(0, minutes_from_midnight))]
            late_data = daydf.ix[daydf.index.indexer_between_time(datetime.time(23, 60-minutes_from_midnight), datetime.time(23,55,59))]
            if len(early_data) < 1 or len(late_data) < 1:
                dweald['early_late_data'].append(False)
            else:
                dweald['early_late_data'].append(True)
        return pd.DataFrame.from_dict(dweald).set_index('Date_Time')['early_late_data']

    def num_datapoints_daily(self):
        num_datapoints = dict(Date_Time=[], num_datapoints=[])
        for grp, daydf in self.df.groupby(pd.TimeGrouper('D')):
            num_datapoints['Date_Time'].append(grp)
            num_datapoints['num_datapoints'].append(len(daydf))
        return pd.DataFrame.from_dict(num_datapoints).set_index('Date_Time')['num_datapoints']

    def min_max_timestamp(self):
        return self.df.index.min(), self.df.index.max()
    def min_max_datetime(self):
        min_max = self.min_max_timestamp()
        return min_max[0].to_datetime(), min_max[1].to_datetime()
    def min_max_date(self):
        min_max = self.min_max_datetime()
        return min_max[0].date(), min_max[1].date()
    def number_of_days(self):
        min_max = self.min_max_date()
        return (min_max[1] - min_max[0]).days + 1

def main():
    parser = argparse.ArgumentParser(description='Analysis software for a U189A energy counter with U180C LAN interface.')
    parser.add_argument('input_file', help='The data file to read')
    parser.add_argument('output_folder', help='The folder to store the plots in')
    parser.add_argument('plot_functions', nargs='*', help='The plot functions you want to run. [Default: all].')
    args = parser.parse_args()

    if not args.input_file.lower().endswith('.h5'):
        parser.error('Expecting a HDF5 file as input (file ending .h5).')

    store = pd.HDFStore(args.input_file, mode='r')
    ups = U180CPlotService(store=store, output_folder=args.output_folder)
    if not args.plot_functions:
        print("Now creating all plots:")
        ups.plot_all()
    else:
        print("Now creating the specified plots:")
        for plot_function in args.plot_functions:
            ups.plot_individual(plot_function)
    store.close()

if __name__ == "__main__":
    main()
