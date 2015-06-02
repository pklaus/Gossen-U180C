#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bottle import Bottle, request, response, view, static_file, TEMPLATE_PATH
from U180C_analyze import read_data_file
from datetime import date, timedelta

class U180CPlotWebServerAPI(Bottle):

    DPI = 72
    MIME_MAP = {
      'pdf': 'application/pdf',
      'png': 'image/png',
      'svg': 'image/svg+xml'
    }

    def __init__(self, df):
        """
        the U180C plot web server
        """
        self.df = df
        super(U180CPlotWebServerAPI, self).__init__()
        self.route('/list/measures', callback = self._list_measures)
        self.route('/describe', callback = self._describe)
        self.route('/describe/<column>', callback = self._describe)
        self.route('/plot/tseries/<measure>.<fileformat>', callback = self._plot_tseries)

    def _plot_tseries(self, measure, fileformat):
        from io import BytesIO
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import base64
        import numpy as np

        df = self.df

        # Handling of URL query variables
        q_range = request.query.range
        if q_range:
            if ',' in q_range:
                q_range = q_range.split(',')
                df = df[q_range[0]:q_range[1]]
            else:
                df = df[q_range]
        else:
            q_range = 'All Time'
        figsize = request.query.figsize or '10,6'
        figsize = (float(num) for num in figsize.split(','))
        dpi = request.query.dpi or self.DPI
        dpi = float(dpi)
        resample = request.query.resample or '2min'

        fig = plt.figure(num=None, figsize=figsize, facecolor='w', edgecolor='k')
        ax = fig.add_axes([0.2, 0.2, 0.7, 0.7])
        #ax = fig.add_subplot(111)
        df.ix[:,measure.split(',')].resample(resample).plot(ax=ax)
        #start, end = ax.get_xlim()
        #ax.xaxis.set_ticks(np.arange(start, end, 1.0))
        ax.xaxis.grid(True, which="minor")
        if type(q_range) == str:
            ax.set_xlabel(q_range)
        else:
            ax.set_xlabel(' - '.join(q_range))
        ax.set_ylabel('Power [Watt]')
        ax.legend()

        io = BytesIO()
        fig.savefig(io, format=fileformat, dpi=dpi)
        # Encode image to png in base64
        #return base64.b64encode(io.getvalue()).decode('ascii')
        response.content_type = self.MIME_MAP[fileformat]
        return io.getvalue()

    def _list_measures(self):
        return {'measures': [col for col in self.df.columns]}

    def _describe(self, column='all'):
        from pandas import compat
        def to_dict_dropna(df):
            return dict((k, v.dropna().to_dict()) for k, v in compat.iteritems(df))
        #def to_dict_dropna(df):
        #  return [dict((k, v.dropna().to_dict())) for k, v in compat.iteritems(df)]

        return to_dict_dropna(self.df.describe(include=column))
        #for col in descr.columns:
        #    ret += col + '\n'
        #    ret += descr[col].to_string()
        #    ret += '\n\n'
        #ret += '</code></pre>'
        #return ret
        #ret = ("<iframe " +
        #       "srcdoc='" + self.df.describe().to_html() + "' " +
        #       "width=1000 height=500>" +
        #       "</iframe>")
        #return ret

class U180CPlotWebServer(Bottle):
    def __init__(self, df):
        """
        the U180C plot web server
        """
        self.df = df
        super(U180CPlotWebServer, self).__init__()
        self.mount('/api', U180CPlotWebServerAPI(df))
        self.route('/',     callback = self._index)
        #self.route('/static/<filename:path>', callback = self._serve_static)

    @view('index')
    def _index(self):
        return {'yesterday': (date.today() - timedelta(days=1)).isoformat()}

def main():
    import argparse
    parser = argparse.ArgumentParser(description='U180C Plot Server')
    parser.add_argument('logfile', help='The logfile to use')
    parser.add_argument('--port', '-p', default=8273, help='Web server port')
    parser.add_argument('--ipv6', '-6', action='store_true', help='IPv6 mode')
    parser.add_argument('--debug', '-d', action='store_true', help='Debug mode')
    args = parser.parse_args()
    try:
        df = read_data_file(args.logfile)
        upws = U180CPlotWebServer(df)
        if args.debug:
            upws.run(host='0.0.0.0', port=args.port, debug=True)
        else:
            if args.ipv6:
                # CherryPy is Python3 ready and has IPv6 support:
                upws.run(host='::', server='cherrypy', port=args.port)
            else:
                upws.run(host='0.0.0.0', server='cherrypy', port=args.port)
    except KeyboardInterrupt:
        print('Ctrl-C pressed. Exiting...')

if __name__ == "__main__":
    main()

