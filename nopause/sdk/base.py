import os
import nopause

from nopause.sdk.error import InvalidRequestError, NoPauseError


class BaseAPI():
    @staticmethod
    def parse_setting(name, env_name, value):
        # function_param > environment > nopause.env
        if value:
            final_value = value
            parsed_from = 'function_param: {}'.format(name)
        else:
            env_value = os.environ.get(env_name, None)
            if env_value is None:
                final_value = getattr(nopause, name)
                parsed_from = 'nopause.{}'.format(name)
            else:
                final_value = env_value
                parsed_from = 'environment: {}'.format(env_name)

        if final_value is None or final_value.strip() == "":
            raise NoPauseError(f'No {env_name} provided (parsed from {parsed_from}). Set the key by function param or {env_name} environment variable or nopause.{name} first.')

        return dict(value=final_value, parsed_from=parsed_from)

    @classmethod
    def parse_settings(cls, api_key: str = None, api_base: str = None, api_version: str = None) -> dict:
        parsed_api_key = cls.parse_setting('api_key', 'NO_PAUSE_API_KEY', api_key)
        parsed_api_base = cls.parse_setting('api_base', 'NO_PAUSE_API_BASE', api_base)
        parsed_api_version = cls.parse_setting('api_version', 'NO_PAUSE_API_VERSION', api_version)

        return parsed_api_key, parsed_api_base, parsed_api_version

    @classmethod
    def display_parsed_settings(cls, api_base: str, api_version: str, url: str, error: str = None):
        if error is None:
            error = ''
        else:
            error += '\n'
        return f'{error}\n[NoPause Settings] (Parsing Order: function_param > environment > nopause.env)' \
               f'\n* API_BASE: {api_base}\n* API_VERSION: {api_version}\n* API_URL: {url}'