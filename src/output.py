from src.config import Config
from datetime import datetime
from src.log import RiaLogger
import os
import statistics
import tabulate
import unicodecsv as csv


class Output:
    def __init__(self):
        self.config = Config()
        self.time = datetime.now().strftime("%Y%m%d%H%M%S")
        self.path = None
        self.format = self.config.read_config('RIA_CONFIG', 'output_format')
        self.location = self.config.read_config('RIA_CONFIG', 'search_results_location')

    def set_path(self, make, model, count, with_warning):
        sep = '_'
        is_failed = ''
        if with_warning:
            is_failed = '_'
        path = os.path.join(self.location, make+model+sep+str(count)+sep+self.time+is_failed+'.'+self.format)
        path.replace(' ', '')
        self.path = path

    @staticmethod
    def get_best(adverts):
        price_deviation = 0.1

        year = statistics.mode([a.info['autoData_year'] for a in adverts])
        price = statistics.median([a.info['USD'] for a in adverts if a.info['autoData_year'] == year])
        price_low_lim = price - price * price_deviation
        price_high_lim = price + price * price_deviation

        best = [a for a in adverts if price_high_lim >= a.info['USD'] >= price_low_lim]
        return best

    def write(self, data):
        if not os.path.isdir(self.location):
            os.mkdir(self.location)
        header = data[0].keys()
        if self.format == 'txt':
            rows = [x.values() for x in data]
            with open(self.path, 'wb') as output_file:
                output_file.write(tabulate.tabulate(rows, header).encode('utf8'))
        elif self.format == 'csv':
            with open(self.path, 'wb') as output_file:
                output_file.write(u'\ufeff'.encode('utf8'))
                dict_writer = csv.DictWriter(output_file, header)
                dict_writer.writeheader()
                dict_writer.writerows(data)
        RiaLogger.log("Saved search results into %s" % self.path)


#stats


# - lowest price
# - oldest year average price range
# - average year range average price range
# - newest year average price range
# - average year range average mileage range

