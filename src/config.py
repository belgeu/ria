from src.log import RiaLogger
import collections
import configparser
import os
import pickle
import time


class Config:

    def __init__(self):
        self.parser = configparser.ConfigParser()
        self.file = os.path.join('config', 'ria.ini')
        self.store_default_config()

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        setattr(self, item, value)

    def store_default_config(self):
        sections = ['RIA_CONFIG', 'OUTPUT']
        if not os.path.isfile(self.file):
            if not os.path.isdir('config'):
                os.mkdir('config')
            for section in sections:
                self.parser.add_section(section)
            self.parser.set("OUTPUT", "fields", ",".join(self.convert_field.values()))
            self.parser.set('RIA_CONFIG', 'search_results_location', 'results/')
            self.parser.set('RIA_CONFIG', 'cache_files_location', 'tmp/')
            self.parser.set('RIA_CONFIG', 'cache_expiry_time', '86400')
            self.parser.set('RIA_CONFIG', 'output_format', 'csv')
            with open(self.file, 'w') as configfile:
                self.parser.write(configfile)
            RiaLogger.log("Default config is stored into '%s'" % self.file)

    def read_config(self, section, param=None):
        self.parser.read(self.file)
        if param:
            return self.parser.get(section, param)
        else:
            return dict(self.parser.items(section))

    @staticmethod
    def get_api_key(f='config/key.pkl'):
        try:
            with open(f, 'rb') as key:
                return pickle.load(key)
        except IOError:
            ria_key_init = input('MORE INFO ABOUT GETTING A KEY IS HERE https://developers.ria.com\n'
                                 'PASTE KEY HERE: ')
            Config.store_api_key(f, ria_key_init)
            exit()

    @staticmethod
    def store_api_key(f, key):
        with open(f, 'wb') as pkl:
            pickle.dump(key, pkl, pickle.HIGHEST_PROTOCOL)
        RiaLogger.log("Stored api key '%s' successfully" % f)

    def get_fields_to_extract(self):
        ria_fields_to_extract = []
        fields = self.read_config('OUTPUT', 'fields')
        fields_enabled = fields.split(',')

        for df in fields_enabled:
            for src, tgt in self.convert_field.items():
                if tgt == df:
                    ria_fields_to_extract.append(src)
                    break
        return ria_fields_to_extract

    def store_cache_data(self, data, pkl_name, suffix=None):
        location = self.read_config('RIA_CONFIG', 'cache_files_location')
        if not os.path.isdir(location):
            os.mkdir(location)
        pkl_path = self.get_cache_path(location, pkl_name, suffix)

        with open(pkl_path, 'wb') as pkl:
            pickle.dump(data, pkl, pickle.HIGHEST_PROTOCOL)
        RiaLogger.log('Stored "%s" cache file successfully' % pkl_path, suppress_stdout=True)

    def get_cache_data(self, pkl_name, suffix=None):
        location = self.read_config('RIA_CONFIG', 'cache_files_location')
        pkl_path = self.get_cache_path(location, pkl_name, suffix)

        with open(pkl_path, 'rb') as data:
            RiaLogger.log('Loading data from "%s" cache file' % pkl_path, suppress_stdout=True)
            return pickle.load(data)

    def cache_valid(self, pkl_name, suffix=None):
        location = self.read_config('RIA_CONFIG', 'cache_files_location')
        ttl = int(self.read_config('RIA_CONFIG', 'cache_expiry_time'))
        pkl_path = self.get_cache_path(location, pkl_name, suffix)

        if os.path.isfile(pkl_path):
            t = time.time()
            mtime = os.path.getmtime(pkl_path)
            cache_age = t - mtime
            if cache_age < ttl:
                RiaLogger.log('"%s" cache data is valid, TTL is %s seconds' % (pkl_path, round(ttl-cache_age, 2)),
                              suppress_stdout=True)
                return True
            else:
                RiaLogger.log('"%s" cache is expired' % pkl_path, suppress_stdout=True)
                return False
        else:
            RiaLogger.log('"%s" cache file not found' % pkl_path, suppress_stdout=True)
            return False

    @staticmethod
    def get_cache_path(location, cache_name, suffix):
        separator = '_'
        if suffix:
            return os.path.join(location, cache_name + separator + str(suffix) + '.pkl')
        else:
            return os.path.join(location, cache_name + '.pkl')

    convert_field = collections.OrderedDict(
            {
                'autoData_autoId': 'id',
                'title': 'title',
                'autoData_year': 'year',
                'autoData_raceInt': 'mileage',
                'UAH': 'price(uah)',
                'USD': 'price(usd)',
                'EUR': 'price(eur)',
                'autoData_fuelName': 'fuel',
                'autoData_gearboxName': 'gearbox',
                'locationCityName': 'city',
                'stateData_regionName': 'region',
                'autoData_bodyId': 'type',
                'linkToView': 'url',
                'userPhoneData_phone': 'phone',
                'addDate': 'created',
                'updateDate': 'updated',
                'soldDate': 'sold',
                'exchangeType': 'exchange',
                'autoData_description': 'description',
            }
        )
