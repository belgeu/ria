import collections
from src.config import Config
from flatten_json import flatten
import json
from src.log import RiaLogger
import logging
import requests
import sys
import time
from tqdm import tqdm


class Search(object):
    logger = logging.getLogger("ria.run")

    def __init__(self):
        self.config = Config()
        self.parameters = {'api_key': self.config.get_api_key()}
        self.ria_dev_url = 'https://developers.ria.com'
        self.ria_url = 'https://auto.ria.com'
        self.start_time = time.time()
        self.end_time = None
        self.run_time = None

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        setattr(self, item, value)

    def make_request(self, url, parameters):
        self.logger.debug('Sending request to %s URL with the following parameters: %s' % (url,
                                                                                           self.dump_json(parameters)))
        try:
            r = requests.get(url, params=parameters, timeout=10)
            code = r.status_code
            if code != 200:
                    print("ERROR response: %s" % code)
                    decode = r.content.decode('utf8').replace("'", '"')
                    data = json.loads(decode)
                    message = data['error']
                    RiaLogger.log(message['code'] + ': ' + message['message'], 'error')
                    if code == 403:
                        exit(1)
                    return False
            else:
                return r
        except json.decoder.JSONDecodeError as e:
            RiaLogger.log(e, 'error')
            return False
        except requests.exceptions.RequestException as e:
            RiaLogger.log(e, 'error')
            return False

    def check_response(self, request_name, response):
        if response:
            return response
        else:
            self.logger.error('Failed to make "%s" request.' % request_name)
            exit(1)

    @staticmethod
    def dump_json(j, indent=2, sep=(',', ':'), data_type=None):
        if data_type == 'list':
            j = list(j)
        if data_type == 'dict':
            j = dict(j)
        return json.dumps(j, ensure_ascii=False, indent=indent, sort_keys=True, separators=sep)

    def log_order_squeeze(self, d):
        data = self.squeeze(d)
        return self.order_elements(self.sort_elements(data.items()))

    @staticmethod
    def squeeze(d):
        sq = {}
        for el in d:
            sq.update({el['name']: el['value']})
        return sq

    @staticmethod
    def order_elements(d):
        return collections.OrderedDict(d)

    @staticmethod
    def sort_elements(d):
        return sorted(d)

    @staticmethod
    def continue_search(message=''):
        positive = ('y', 'Y', 'Yes', 'YES')
        negative = ('n', 'N', 'No', 'NO')
        answer_options = positive + negative

        while True:
            decision = input(message)
            if decision in answer_options:
                break
            else:
                print("\nPlease input %s" % str(answer_options))

        if decision in negative:
            return False
        elif decision in positive:
            return True
        else:
            return False

    @staticmethod
    def has_number(input_string):
        return any(char.isdigit() for char in input_string)

    @staticmethod
    def has_comma(input_string):
        if ',' in input_string:
            return True
        else:
            return False

    def log_error_list(self, message, ria_data, code=1):
        self.logger.error(message + self.dump_json(ria_data))
        self.print_out(ria_data, message)
        sys.exit(code)

    @staticmethod
    def extract_key_names(vd):
        details = []
        for m in vd:
            details.append(m['name'])
        return details

    @staticmethod
    def print_out(l, message=None):
        if message:
            print(message)
        for e in l:
            print("'" + e + "'"),

    aux = [
        'average-price'
    ]

    status = {
        'all': 0,
        'sold': 1,
        'sale': 2
    }

    period = {
        '1': 1,
        '3': 8,
        '6': 9,
        '12': 14,
        'today': 2,
        '24': 11,
        '48': 10,
        '72': 3,
        'week': 4,
        'month': 5,
        'quarter': 6
    }

    sort = {
        'price-up': 2,
        'price-down': 3,
        'date': 7,
        'prod-year-up': 6,
        'prod-year-down': 5,
        'mileage-up': 13,
        'mileage-down': 12
    }

    damage = {
        'no': 1,
        'yes': 2,
        'all': 0
    }


class Advertisement(Search):

    def __init__(self, category=1):
        super(Advertisement, self).__init__()
        self.category_id = category
        self.opts = None
        self.make_name = None
        self.makes = self.all('makes')
        self.make_names = self.extract_key_names(self.makes)
        self.make_id = None
        self.model_name = ''
        self.models = None
        self.model_names = None
        self.model_id = None
        self.gearboxes = self.squeeze(self.all('gearboxes'))
        self.options = self.squeeze(self.all('options'))
        self.bodies = self.squeeze(self.all('styles'))
        self.fuel_type = self.squeeze(self.all('fuel_types'))
        self.colors = self.squeeze(self.all('colors'))
        self.countries = self.squeeze(self.all('countries'))
        self.countpage = 100
        self.page = 0
        self.criteria = None
        self.opts_to_remove = ['get', 'verbose']
        self.warn = False

    def set_avg_price_criteria(self, options):
        apc = {}
        if options.get('marka_id', None):
            apc['marka_id'] = self.make_id
        if options.get('model_id', None):
            apc['model_id'] = self.model_id
        if options.get('gearbox', None):
            apc['gear_id'] = self.gearboxes[options['gearbox']]
        if options.get('s_yers', None):
            apc['yers'] = options['s_yers']
        if options.get('type', None):
            apc['fuel_id'] = self.fuel_type[options['type']]
        self.criteria = apc

    def all(self, spec):
        ria = self.ria_dev_url + '/auto'
        endpoint = {
            'makes': ria + '/categories/1/marks',
            'styles': ria + '/categories/1/bodystyles',
            'gearboxes': ria + '/categories/1/gearboxes',
            'options': ria + '/categories/1/options',
            'fuel_types': ria + '/type',
            'colors': ria + '/colors',
            'countries': ria + '/countries'
        }
        self.logger.debug("Checking available %s to search" % spec)

        if self.config.cache_valid(spec):
            return self.config.get_cache_data(spec)
        else:
            r = self.make_request(endpoint[spec], self.parameters)
            super(Advertisement, self).check_response('get all %s' % spec, r)
            car_spec = r.json()
            self.config.store_cache_data(car_spec, spec)
            return car_spec

    def all_models(self):
        url = "%s/auto/categories/1/marks/%s/models" % (self.ria_dev_url, self.make_id)
        self.logger.debug("Checking available '%s' models" % self.make_name)
        if self.config.cache_valid('models', self.make_id):
            models = self.config.get_cache_data('models', self.make_id)
        else:
            r = self.make_request(url, self.parameters)
            self.check_response('get all models', r)
            models = r.json()
            self.config.store_cache_data(models, 'models', self.make_id)
        self.logger.debug("Ria '%s' models: %s" % (self.make_name, self.dump_json(self.log_order_squeeze(models))))
        return models

    def average_price(self):
        url = "%s/auto/average_price" % self.ria_dev_url
        self.logger.debug("Checking average price")
        self.parameters.update(self.criteria)
        r = self.make_request(url, self.parameters)
        print("Total cars: %s" % r.json()['total'])
        print("Arithmetic mean: %s" % r.json()['arithmeticMean'])
        print("Inter quartile mean: %s" % r.json()['interQuartileMean'])
        print("Percentiles: %s" % r.json()['percentiles'])

    def get_car_make_id(self, make_name):
        make_id = [make['value'] for make in self.makes if make['name'] == make_name]
        self.logger.debug("'%s' id: %s" % (make_name, make_id[0]))
        return make_id[0]

    def get_car_model_id(self, model_name):
        model_id = [model['value'] for model in self.models if model['name'] == model_name]
        self.logger.debug("'%s' id: %s" % (model_name, model_id[0]))
        return model_id[0]

    def vehicle_ads(self):
        url = "%s/auto/search/" % self.ria_dev_url
        self.logger.debug("Searching for '%s' advertisements" % self.make_name)

        self.parameters.update({'category_id': self.category_id,
                                'countpage': self.countpage,
                                'page': self.page
                                })
        self.parameters.update(self.criteria)

        r = self.make_request(url, self.parameters)

        # Exit if request unsuccessful
        if not r:
            exit('Request not successful')
        # Return ad ids
        ads_ria = r.json()
        self.logger.debug("'%s' search result from page 1: %s" % (self.make_name, self.dump_json(ads_ria)))

        # Check count of records returned
        adverts_total_count = ads_ria['result']['search_result']['count']

        if adverts_total_count == 0:
            RiaLogger.log('No cars found by given criteria', 'info')
            sys.exit(0)

        # Ask if user needs to continue the search
        if self.make_name and self.model_name:
            print('Found %s matches for "%s %s" with given criteria' % (adverts_total_count, self.make_name, self.model_name))
        else:
            print('Found %s matches for "%s" with given criteria' % (adverts_total_count, self.make_name))

        if not self.continue_search('Get? (y/n)'):
            self.logger.info('Search is cancelled by user')
            exit(0)

        # Get ad ids
        adverts_ids = ads_ria['result']['search_result']['ids']

        if adverts_total_count > 100:
            # Calculate number of pages
            page_num = int(adverts_total_count / self.countpage)

            if adverts_total_count % self.countpage == 0:
                page_num -= 1

            for ad in tqdm(range(page_num), desc='Searching cars on pages', unit='page'):
                self.parameters['page'] = ad + 1

                self.logger.debug("Searching cars on page %s" % (self.parameters['page'] + 1))
                r = self.make_request(url, self.parameters)
                ads_ria = r.json()
                self.logger.debug("'%s %s' search result from page %s: %s" % (self.make_name,
                                                                              self.model_name,
                                                                              str(self.parameters['page'] + 1),
                                                                              self.dump_json(ads_ria)))
                adverts_ids_pages = ads_ria['result']['search_result']['ids']

                if adverts_ids_pages:
                    adverts_ids += adverts_ids_pages
                else:
                    break
            self.logger.debug("Got IDs for %s matching car(s)" % len(adverts_ids))

        if adverts_total_count != len(adverts_ids):
            self.logger.warning('Advertisement ids count mismatch: found %s, got %s' % (adverts_total_count,
                                                                                        len(adverts_ids)))
        self.logger.debug("advertisement ids: %s (%s)" % (self.dump_json(adverts_ids), len(adverts_ids)))
        return adverts_ids

    def model_is_valid(self, model_name):
        if model_name in self.model_names:
            return True
        else:
            error_message = "UNKNOWN MODEL '%s', '%s' MODELS AVAILABLE TO SEARCH: " % (model_name, self.make_name)
            self.log_error_list(error_message, self.model_names, 0)


class VehicleDetails(Search):

    def __init__(self, ria_id, bodies):
        super(VehicleDetails, self).__init__()
        self.bodies = bodies
        self.start_time = None
        self.end_time = None
        self.id = ria_id
        self.info = None
        self.code = None
        self.csv = None
        self.failed = False

    def get(self):
        self.start_time = time.time()
        url = "%s/auto/info/" % self.ria_dev_url
        self.parameters.update({'auto_id': self.id})
        r = self.make_request(url, self.parameters)
        if r:
            self.code = r.status_code
            raw_info = r.json()
            self.logger.debug("'%s' details: %s" % (self.id, self.dump_json(raw_info)))
            self.info = flatten(raw_info)
            self.logger.debug("'%s' flattened details: %s" % (self.id, self.dump_json(self.info)))
            self.csv = self.check_set(self.info)
            self.end_time = time.time()
            self.run_time = round(self.end_time - self.start_time, 3)
        else:
            self.failed = True

    def check_set(self, ria_adv_flat):
        src_set = {}
        # Get desired fields
        for src_el in self.config.get_fields_to_extract():
            if src_el in ria_adv_flat:
                src_val = ria_adv_flat[src_el]

                # Multiply mileage value by 1000
                if src_el == 'autoData_raceInt':
                    src_val *= 1000

                # Check if Fuel field contains engine volume info
                if src_el == 'autoData_fuelName':
                    if self.has_number(src_val):
                        if self.has_comma(src_val):
                            fuel_info = src_val.split(',')
                            src_set['displacement'] = fuel_info[1].split()[0]
                            src_val = fuel_info[0]
                        else:
                            src_set['displacement'] = src_val.split()[0]
                            src_val = '-'
                    else:
                        src_set['displacement'] = '-'

                # set body type from response
                if src_el == 'autoData_bodyId':
                    body_styles = self.bodies
                    if src_val in body_styles.values():
                        src_val = list({k: v for k, v in list(body_styles.items()) if v == src_val}.keys())[0]
                    else:
                        src_val = '-'

                if src_el == 'linkToView':
                    src_val = self.ria_url + src_val

                if src_el == 'autoData_description':
                    # dispose of new line in description
                    src_val = src_val.replace('\r', '').replace('\n', '')

                src_set[self.config.convert_field[src_el]] = src_val
            else:
                src_set[self.config.convert_field[src_el]] = '-'
        return src_set
