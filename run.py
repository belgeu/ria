#!/usr/bin/env python3
import argparse
import logging
import logging.handlers
from src.log import RiaLogger
import sys
import time
from src.search import Advertisement
from src.search import VehicleDetails
from src.output import Output
from tqdm import tqdm


def main():
    logger = logging.getLogger("ria.run")
    fh = logging.FileHandler("ria.log")
    formatter = logging.Formatter(RiaLogger.log_format_info)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Initialize search
    search = Advertisement()
    local_output = Output()

    ria_description = 'Get car advertisements from https://auto.ria.com'
    example = 'EXAMPLE ./run.py -m Ford -M Focus'

    parser = argparse.ArgumentParser(description=ria_description, epilog=example)
    parser.add_argument('-get', choices=search.aux)
    parser.add_argument('-k', '--key', type=str, dest='api_key', metavar='API_KEY',
                        help='Update RIA API key.')
    parser.add_argument('-m', '--make', type=str, dest='marka_id', metavar='MAKE', choices=search.make_names,
                        help='Car make.')
    parser.add_argument('-M', '--model', type=str, dest='model_id', metavar='MODEL',
                        help='Car model.')
    parser.add_argument('-b', '--body', type=str, dest='bodystyle', metavar='BODY', choices=search.bodies,
                        help='Body style.')
    parser.add_argument('-y', '--year-start', type=int, dest='s_yers', metavar='YEAR',
                        help='Car production year lower limit.')
    parser.add_argument('-Y', '--year-end', type=int, dest='po_yers', metavar='YEAR',
                        help='Car production year upper limit.')
    parser.add_argument('-l', '--capacity-from', type=float, dest='engineVolumeFrom', metavar='CAPACITY',
                        help='Engine capacity lower limit.')
    parser.add_argument('-L', '--capacity-to', type=float, dest='engineVolumeTo', metavar='CAPACITY',
                        help='Engine capacity upper limit.')
    parser.add_argument('-g', '--gearbox', type=str, metavar='GEARBOX', choices=search.gearboxes,
                        help='Gearbox type.')
    parser.add_argument('-f', '--fuel', type=str, dest='type', metavar='FUEL',
                        choices=search.fuel_type.keys(),
                        help='Fuel type.')
    parser.add_argument('-c', '--color', type=str, metavar='COLOR', choices=search.colors.keys(),
                        help='Car color.')
    parser.add_argument('-C', '--country', type=str, dest='brandOrigin', metavar='COUNTRY', choices=search.countries,
                        help='Brand origin.')
    parser.add_argument('-O', '--options', type=str, dest='auto_options', metavar='OPTIONS', choices=search.options,
                        help='Car options.')
    parser.add_argument('-p', '--period', type=str, dest='top', metavar='PERIOD', choices=search.period.keys(),
                        help='Period in hours. Also options like "week", "month", "quarter", "today" possible.')
    parser.add_argument('-s', '--sort', type=str, dest='order_by', metavar='SORT', choices=search.sort.keys(),
                        help='Sort search results, default is "price_up".')
    parser.add_argument('-S', '--status', type=str, dest='saledParam', metavar='STATUS',
                        choices=search.status.keys(),
                        help='Sale status: "all", "sold", "sale". Default is "sale".')
    parser.add_argument('-d', '--damage', type=str, dest='damage', metavar='DAMAGE',
                        choices=search.damage.keys(),
                        help='Has damage: "yes", "no", "all". Default is "no".')
    parser.add_argument('-o', '--output', type=str, dest='output', metavar='OUTPUT', choices=['txt', 'csv'],
                        help='Search output. Default is "csv".')
    parser.add_argument("-v", "--verbose", help="Increase output verbosity.", action="store_true")

    opts = parser.parse_args()

    if opts.api_key:
        search.config.store_api_key('config/key.pkl', opts.api_key)
        exit(0)

    if opts.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Set 'requests' lib WARN level logger
    logging.getLogger("requests").setLevel(logging.WARN)

    if opts.marka_id:
        search.make_name = opts.marka_id
        search.make_id = opts.marka_id = search.get_car_make_id(search.make_name)
    else:
        if not opts.get:
            RiaLogger.log('Please specify a car make (e.g. --make Ford)', 'error')
            sys.exit(2)

    if opts.model_id:
        if not opts.marka_id:
            RiaLogger.log('Need a car make first (e.g. --make Ford)', 'error')
            sys.exit(2)
        search.models = search.all_models()
        search.model_names = search.extract_key_names(search.models)
        if search.model_is_valid(opts.model_id):
            search.model_name = opts.model_id
            search.model_id = opts.model_id = search.get_car_model_id(search.model_name)

    # Check if 'get' function invoked
    if opts.get:
        if opts.get == 'average-price':
            ap_opts = ['marka_id', 'model_id', 'gearbox', 's_yers', 'type']
            search.set_avg_price_criteria({k: v for (k, v) in vars(opts).items() if v and k in ap_opts})
            search.average_price()
            logger.info('Printed out Ria average prices to stdout')
        sys.exit(0)

    if opts.bodystyle:
        opts.bodystyle = search.bodies[opts.bodystyle]
    if opts.gearbox:
        opts.gearbox = search.gearboxes[opts.gearbox]
    if opts.type:
        opts.type = search.fuel_type[opts.type]
    if opts.color:
        opts.color = search.colors[opts.color]
    if opts.top:
        opts.top = search.period[opts.top]
    if opts.order_by:
        opts.order_by = search.sort[opts.order_by]
    else:
        opts.order_by = search.sort['price-up']
    if opts.saledParam:
        opts.saledParam = search.status[opts.saledParam]
    else:
        opts.saledParam = search.status['sale']
    if opts.damage:
        opts.damage = search.damage[opts.damage]
    else:
        opts.damage = search.damage['no']
    if opts.output:
        local_output.format = opts.output
    if opts.auto_options:
        opts.auto_options = search.options[opts.auto_options]
    if opts.brandOrigin:
        opts.brandOrigin = search.countries[opts.brandOrigin]

    # Convert options into query parameters
    search.criteria = {k: v for (k, v) in vars(opts).items() if v and k not in search.opts_to_remove}

    logger.debug("Searching by following criteria %s" % search.dump_json(
        search.criteria, 1, (',', '='), data_type=dict))

    # Start searching ads
    ads_ids = search.vehicle_ads()

    # Token connection limit warning
    if len(ads_ids) >= 500:
        print('Might go over the token connection limit,')
        ask = 'continue? (y/n)'
        if not search.continue_search(ask):
            logger.info('Search is cancelled by user')
            exit(0)

    logger.debug('Extracting following fields: %s' % search.dump_json(search.config.convert_field.values(),
                                                                      data_type='list'))
    advertisements = [VehicleDetails(adv, search.bodies) for adv in ads_ids]
    for a in tqdm(advertisements, desc='Downloading cars info', unit='cars'):
        a.get()
        if a.failed:
            break

    ads_src_data = [a.csv for a in advertisements if a.code]
    search_runtime_debug = [{"id": a.id, "search_time": a.run_time} for a in advertisements]

    if len(ads_src_data) == 0:
        exit('Search error')
    elif len(ads_src_data) != len(ads_ids):
        logger.warning('Inaccurate search results due to errors, check log for more details')
        search.warn = True

    logger.info("Downloaded details for %s cars" % len(ads_src_data))
    logger.debug('Converted Ria results into source CSV values: %s' % search.dump_json(ads_src_data))

    # Set file name
    local_output.set_path(search.make_name, search.model_name, len(ads_src_data), search.warn)

    # Write to file
    local_output.write(ads_src_data)

    search.end_time = time.time()
    search.runtime = search.end_time - search.start_time
    if search.warn:
        logger.warning("Finished search in %.2f seconds with warnings" % search.runtime)
    else:
        logger.debug("Finished search in %.2f seconds" % search.runtime)
    search.logger.debug("Detailed run times: %s" % search.dump_json(search_runtime_debug))


if __name__ == "__main__":
    main()
