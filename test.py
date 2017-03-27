#!/usr/bin/python2
# from withings import WithingsAuth, WithingsApi
from withings.withings_api import *
# import withings.withings_api
from optparse import OptionParser
# from settings import CONSUMER_KEY, CONSUMER_SECRET
try:
    import configparser
except ImportError:  # Python 2.x fallback
    import ConfigParser as configparser

parser = OptionParser()
parser.add_option('-k', '--consumer-key', dest='consumer_key', help="Consumer Key")
parser.add_option('-s', '--consumer-secret', dest='consumer_secret', help="Consumer Secret")
parser.add_option('-a', '--access-token', dest='access_token', help="Access Token")
parser.add_option('-t', '--access-token-secret', dest='access_token_secret', help="Access Token Secret")
parser.add_option('-u', '--userid', dest='user_id', help="User ID")
parser.add_option('-c', '--config', dest='config', help="Config file")

(options, args) = parser.parse_args()

options.config = 'hv_settings'
config = configparser.ConfigParser(vars(options))
config.read(options.config)
options.consumer_key = config.get('withings', 'consumer_key')
options.consumer_secret = config.get('withings', 'consumer_secret')
options.access_token = config.get('withings', 'access_token')
options.access_token_secret = config.get('withings', 'access_token_secret')
options.user_id = config.get('withings', 'user_id')
creds = WithingsCredentials(options.access_token, options.access_token_secret,
                                options.consumer_key, options.consumer_secret,
                                options.user_id)

client = WithingsApi(creds)


# measures = client.get_measures(limit=5)
measures = client.get_measures(limit=1,meastype=76,startdateymd='2017-03-17',enddateymd='2017-03-25')
# measures = client.get_measures()
# print "Your last measured weight: %skg" % measures[0].weight
# for key in measures:
#     print("%s => %s" % (key,measures[key]))
# startdateymd=2015-09-04&enddateymd=2015-09-08
# activity = client.get_activity(date='2017-03-21')
activity = client.get_activity(startdateymd='2017-03-17',enddateymd='2017-03-25')
for key in activity:
    print("%s = %s" % (key,activity[key]))
# for n, t in WithingsMeasureGroup.MEASURE_TYPES:
    # print("%s: %s" % (n.replace('_', ' ').capitalize(), measures.get_measure(t)))
sleep = client.get_sleep(startdate='2017-03-17',enddate='2017-03-25')
for key in sleep:
    print("%s = %s" % (key,activity[key]))
