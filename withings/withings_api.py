# -*- coding: utf-8 -*-
#
"""
Python library for the Withings API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Withings Body metrics Services API
<http://www.withings.com/en/api/wbsapiv2>

Uses Oauth 1.0 to authentify. You need to obtain a consumer key
and consumer secret from Withings by creating an application
here: <https://oauth.withings.com/partner/add>

Usage:

auth = WithingsAuth(CONSUMER_KEY, CONSUMER_SECRET)
authorize_url = auth.get_authorize_url()
print "Go to %s allow the app and copy your oauth_verifier" % authorize_url
oauth_verifier = raw_input('Please enter your oauth_verifier: ')
creds = auth.get_credentials(oauth_verifier)

client = WithingsApi(creds)
measures = client.get_measures(limit=1)
print "Your last measured weight: %skg" % measures[0].weight

"""

from __future__ import unicode_literals

__title__ = 'withings'
__version__ = '0.1'
__author__ = 'Maxime Bouroumeau-Fuseau'
__license__ = 'MIT'
__copyright__ = 'Copyright 2012 Maxime Bouroumeau-Fuseau'

__all__ = [str('WithingsCredentials'), str('WithingsAuth'), str('WithingsApi'),
           str('WithingsMeasures'), str('WithingsMeasureGroup')]

import requests
from requests_oauthlib import OAuth1, OAuth1Session
import json
import datetime


class WithingsCredentials(object):
    def __init__(self, access_token=None, access_token_secret=None,
                 consumer_key=None, consumer_secret=None, user_id=None):
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.user_id = user_id


class WithingsError(Exception):
    STATUS_CODES = {
        # Response status codes as defined in documentation
        # http://oauth.withings.com/api/doc
        0: u"Operation was successful",
        247: u"The userid provided is absent, or incorrect",
        250: u"The provided userid and/or Oauth credentials do not match",
        286: u"No such subscription was found",
        293: u"The callback URL is either absent or incorrect",
        294: u"No such subscription could be deleted",
        304: u"The comment is either absent or incorrect",
        305: u"Too many notifications are already set",
        342: u"The signature (using Oauth) is invalid",
        343: u"Wrong Notification Callback Url don't exist",
        601: u"Too Many Request",
        2554: u"Wrong action or wrong webservice",
        2555: u"An unknown error occurred",
        2556: u"Service is not defined",
    }

    def __init__(self, status):
        super(WithingsError, self).__init__(u'{}: {}'.format(status, WithingsError.STATUS_CODES[status]))
        self.status = status


class WithingsAuth(object):
    URL = 'https://oauth.withings.com/account'

    def __init__(self, consumer_key, consumer_secret, callback_uri=None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.oauth_token = None
        self.oauth_secret = None
        self.callback_uri=callback_uri

    def get_authorize_url(self):
        oauth = OAuth1Session(self.consumer_key,
                              client_secret=self.consumer_secret,
                              callback_uri=self.callback_uri)

        tokens = oauth.fetch_request_token('%s/request_token' % self.URL)
        self.oauth_token = tokens['oauth_token']
        self.oauth_secret = tokens['oauth_token_secret']

        return oauth.authorization_url('%s/authorize' % self.URL)

    def get_credentials(self, oauth_verifier):
        oauth = OAuth1Session(self.consumer_key,
                              client_secret=self.consumer_secret,
                              resource_owner_key=self.oauth_token,
                              resource_owner_secret=self.oauth_secret,
                              verifier=oauth_verifier)
        tokens = oauth.fetch_access_token('%s/access_token' % self.URL)
        return WithingsCredentials(access_token=tokens['oauth_token'],
                                   access_token_secret=tokens['oauth_token_secret'],
                                   consumer_key=self.consumer_key,
                                   consumer_secret=self.consumer_secret,
                                   user_id=tokens['userid'])


class WithingsApi(object):
    URL = 'http://wbsapi.withings.net'
    URL_v2 = 'http://wbsapi.withings.net/v2'

    def __init__(self, credentials):
        self.credentials = credentials
        self.oauth = OAuth1(credentials.consumer_key,
                            credentials.consumer_secret,
                            credentials.access_token,
                            credentials.access_token_secret,
                            signature_type='query')
        self.client = requests.Session()
        self.client.auth = self.oauth
        self.client.params.update({'userid': credentials.user_id})

    def request(self, service, action, params=None, method='GET'):
        if params is None:
            params = {}
        print("%s, %s, %s" %(service, action, params))
        if (action == 'getactivity' or action == 'sleep'):
            self.URL = self.URL_v2
        params['action'] = action
        print('%s/%s %s' % (self.URL, service, params))
        r = self.client.request(method, '%s/%s' % (self.URL, service), params=params)
        response = json.loads(r.content.decode())
        if response['status'] != 0:
            raise WithingsError(response['status'])
        return response.get('body', None)

    def get_user(self):
        return self.request('user', 'getbyuserid')

    def get_measures(self, **kwargs):
        print(kwargs)
        r = self.request('measure', 'getmeas', kwargs)
        print("R = %s" % r)
        return WithingsMeasures(r)

    def get_activity(self, **kwargs):
        # kwargs = {'date' : '2017-03-17'}
        print('get_activity\n')
        print(kwargs)
        r = self.request('measure', 'getactivity', kwargs)
        # print(type(r))
        # r = self.request('measure', 'getintradayactivity', kwargs)
        # r = self.request('measure', 'getworkouts', kwargs)
        # r = self.request('measure', 'getactivity', kwargs)
        # print("R = %s" % r)
        return r

    def get_sleep(self, **kwargs):
            # kwargs = {'date' : '2017-03-17'}
        print('get_sleep\n')
        print(kwargs)
        r = self.request('sleep', 'get', kwargs)
            # print(type(r))
            # r = self.request('measure', 'getintradayactivity', kwargs)
            # r = self.request('measure', 'getworkouts', kwargs)
            # r = self.request('measure', 'getactivity', kwargs)
            # print("R = %s" % r)
        return r

    def subscribe(self, callback_url, comment, appli=1):
        params = {'callbackurl': callback_url,
                  'comment': comment,
                  'appli': appli}
        self.request('notify', 'subscribe', params)

    def unsubscribe(self, callback_url, appli=1):
        params = {'callbackurl': callback_url, 'appli': appli}
        self.request('notify', 'revoke', params)

    def is_subscribed(self, callback_url, appli=1):
        params = {'callbackurl': callback_url, 'appli': appli}
        try:
            self.request('notify', 'get', params)
            return True
        except:
            return False

    def list_subscriptions(self, appli=1):
        r = self.request('notify', 'list', {'appli': appli})
        return r['profiles']


class WithingsMeasures(list):
    def __init__(self, data):
        super(WithingsMeasures, self).__init__([WithingsMeasureGroup(g) for g in data['measuregrps']])
        self.updatetime = datetime.datetime.fromtimestamp(data['updatetime'])


class WithingsMeasureGroup(object):
    MEASURE_TYPES = (('weight', 1), ('height', 4), ('fat_free_mass', 5),
                     ('fat_ratio', 6), ('fat_mass_weight', 8),
                     ('diastolic_blood_pressure', 9), ('systolic_blood_pressure', 10),
                     ('heart_pulse', 11))

    def __init__(self, data):
        self.data = data
        self.grpid = data['grpid']
        self.attrib = data['attrib']
        self.category = data['category']
        self.date = datetime.datetime.fromtimestamp(data['date'])
        self.measures = data['measures']
        for n, t in self.MEASURE_TYPES:
            self.__setattr__(n, self.get_measure(t))

    def is_ambiguous(self):
        return self.attrib == 1 or self.attrib == 4

    def is_measure(self):
        return self.category == 1

    def is_target(self):
        return self.category == 2

    def get_measure(self, measure_type):
        for m in self.measures:
            if m['type'] == measure_type:
                return m['value'] * pow(10, m['unit'])
        return None

    def get_activity(self):
        return None
