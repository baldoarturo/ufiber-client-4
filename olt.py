import json
import logging
import os
import sys

import jsonschema
import requests
import urllib3

# No warnings for self signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Use a proper user agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
# Header for urlencoded form data
HEADER_FORM_URLENCODED = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': USER_AGENT,
    'x-auth-token': '',
}
# Header for urlencoded form data
HEADER_JSON = {
    'Content-Type': 'application/json',
    'User-Agent': USER_AGENT,
    'x-auth-token': '',
}
# GPON Profiles Path
PROFILES_PATH = os.path.join(os.getcwd(), 'profiles')


class Profile():
    '''
    Generic class to handle config profiles
    '''
    @staticmethod
    def load_json_profile(file='template.json'):
        try:
            # Load profile
            path = os.path.join(PROFILES_PATH, file)
            with open(path, 'r') as f:
                profile = json.loads(f.read())
                return profile
        except FileNotFoundError:
            logging.error('Profile {}not found.'.format(profile))
            raise
        except PermissionError:
            logging.excerroreption(
                'Cannot read profile {}, check your permissions.'.format(profile))
        except json.JSONDecodeError:
            logging.error('Profile file is not valid JSON.')

    @staticmethod
    def check_profile(profile):
        # Load schema
        schema = Profile.load_json_profile('schema.json')
        try:
            jsonschema.validate(profile, schema)
        except jsonschema.ValidationError as ex:
            logging.error(ex.message)
            return False
        return True

    @staticmethod
    def get_profile(profile_name):
        # Load profile
        path = os.path.join(PROFILES_PATH, profile_name+'.json')
        try:
            profile = Profile.load_json_profile(path)
        # Error are handled in loader
        except Exception:
            return False
        if not Profile.check_profile(profile):
            return False
        return profile


class ONU():

    ONU_URL = 'https://{host}/api/v1.0/gpon/onus/{serial}/settings'
    ONU_BULK_STATUS_URL = 'https://{host}/api/v1.0/gpon/onus'
    ONU_BULK_SETTINGS_URL = 'https://{host}/api/v1.0/gpon/onus/settings'

    def save(self, serial, name='', profile='', config=False):
        '''
        PUTs configuration to the OLT API
        '''
        # Is is overriding an existing config ?
        if not config:
            # Get profile
            config = Profile.get_profile(profile)
            if not config:
                return False
            # Set new values
            config['serial'] = serial
            config['name'] = name

        # Post payload, which is already built
        serial = config['serial']
        name = config['name']
        logging.info(
            'Saving ONU {serial} - {name} ...'.format(serial=serial, name=name))

        # API URL
        url = ONU.ONU_URL.format(host=client.host, serial=serial)
        try:
            response = self.client.put(
                url=url,
                headers=HEADER_JSON,
                json=config,
                verify=False,
            )
        # Catch all
        except Exception as ex:
            logging.debug(ex)
            return False

        # Success ?
        try:
            result = json.loads(response.text)
            if result['message'] == 'Success':
                logging.info('Saved {serial}!'.format(serial=serial))
                return True
            # Error
            logging.error('{}'.format(result['message']))
            return False
        # Catch all
        except Exception as ex:
            logging.error('Got wrong reply from OLT HTTP interface')
            logging.error(ex)
            return False

    def delete(self, serial):
        '''
        DELETEs configuration to the OLT API
        '''
        # API URL
        url = ONU.ONU_URL.format(host=client.host, serial=serial)
        try:
            response = self.client.delete(
                url=url,
                headers=HEADER_JSON,
                verify=False,
            )
        # Catch all
        except Exception as ex:
            logging.debug(ex)
            return False

        # Success ?
        try:
            result = json.loads(response.text)
            if result['message'] == 'Success':
                logging.info('Deleted {serial}!'.format(serial=serial))
                return True
            # Error
            logging.error('{}'.format(result['message']))
            return False
        # Catch all
        except Exception as ex:
            logging.error('Got wrong reply from OLT HTTP interface')
            logging.error(ex)
            return False

    def get_config_bulk(self):
        url = self.ONU_BULK_SETTINGS_URL.format(host=client.host)
        try:
            response = self.client.get(
                url=url,
                headers=HEADER_JSON,
                verify=False,
            )
        # Catch all
        except Exception as ex:
            logging.debug(ex)
            return False
        # Success ?
        try:
            result = json.loads(response.text)
            if isinstance(result, list):
                logging.info('Got {len} ONUs!'.format(len=len(result)))
                return result
        # Catch all
        except Exception as ex:
            logging.error('Got wrong reply from OLT HTTP interface')
            logging.error(ex)
            return False

    def get_config(self, serial):
        onus = self.get_config_bulk()
        try:
            onu = list(
                filter(lambda x: x['serial'].lower() == serial.lower(), onus))[0]
            return onu
        except IndexError:
            return False
        except KeyError:
            return False

    def get_status_bulk(self):
        url = self.ONU_BULK_STATUS_URL.format(host=client.host)
        try:
            response = self.client.get(
                url=url,
                headers=HEADER_JSON,
                verify=False,
            )
        # Catch all
        except Exception as ex:
            logging.debug(ex)
            return False
        # Success ?
        try:
            result = json.loads(response.text)
            if isinstance(result, list):
                logging.info('Got {len} ONUs!'.format(len=len(result)))
                return result
        # Catch all
        except Exception as ex:
            logging.error('Got wrong reply from OLT HTTP interface')
            logging.error(ex)
            return False

    def get_status(self, serial):
        onus = self.get_status_bulk()
        try:
            onu = list(
                filter(lambda x: x['serial'].lower() == serial.lower(), onus))[0]
            return onu
        except IndexError:
            return False
        except KeyError:
            return False

    def __init__(self, client):
        try:
            assert client, OLTClient
        except AssertionError:
            raise Exception(
                'Paremeter client should be an instance of OLTClient')

        self.client = client


class OLTClient():

    client = requests.Session()
    LOGIN_URL = 'https://{host}/api/v1.0/user/login'

    def login(self):
        '''
        Logins via API
        '''
        # Payload
        data = {
            'username': self.username,
            'password': self.password,
        }

        logging.info(f'Trying {self.host}')

        # Post payload
        try:
            response = self.client.post(
                url=self.LOGIN_URL,
                headers=HEADER_JSON,
                json=data,
                verify=False,
            )
        # Catch all
        except Exception as ex:
            logging.debug(ex)
            return False

        # Success ?
        try:
            result = json.loads(response.text)
            if result['message'] == 'Success':
                logging.info('Logged in!')
                return response.headers['x-auth-token']
            # Login error
            logging.info('Error: {}'.format(result['message']))
            return False
        # Catch all
        except Exception as ex:
            logging.info('Got wrong reply from OLT HTTP interface')
            logging.info(ex)
            return False

    def __init__(self, host='192.168.1.1', username='ubnt', password='ubnt', debug_level=logging.DEBUG):
        '''
        Setup logging, credentials, authorization
        '''
        # Logging
        if debug_level not in [logging.DEBUG, logging.INFO]:
            debug_level = logging.INFO
        logging.basicConfig(
            level=debug_level,
            stream=sys.stdout,
            format='%(levelname)s : %(message)s'
        )
        # Credentials
        self.host = host
        self.username = username
        self.password = password
        # API Endpoint
        self.LOGIN_URL = self.LOGIN_URL.format(host=self.host)
        # X-AUTH-TOKEN
        self.token = self.login()
        if self.token:
            # AUTH TOKEN
            HEADER_FORM_URLENCODED['x-auth-token'] = self.token
            HEADER_JSON['x-auth-token'] = self.token
            self.onu = ONU(self.client)
        else:
            raise Exception('Error logging in OLT !')


# client = OLTClient('1.1.1.1', debug_level=logging.INFO)
# client.onu.save('UBNT29f545b8', 'ONU NAME', 'SOME PROFILE')
# client.onu.get_status('UBNT29f545b8')
# config = client.onu.get_config('UBNT29f545b8')
# config['name'] = 'ewrwaerewa'
# client.onu.save('UBNT29f545b8', config=config)
