import os
import json
import requests
import posixpath
from pathlib import Path
from typing import List
from requests.exceptions import RequestException

import nopause
from nopause.core.base import NoPauseResponse
from nopause.sdk.base import BaseAPI
from nopause.sdk.error import InvalidRequestError, FormatError, NoPauseError


class Voice(BaseAPI):
    name: str = "voices"
    protocol: str = 'https'

    def __init__(
        self,
        api_key: str = None,
        api_base: str = None,
        api_version: str = None
    ):
        self.parsed_api_key, self.parsed_api_base, self.parsed_api_version = self.parse_settings(api_key, api_base, api_version)
        self.protocol = os.environ.get('NO_PAUSE_HTTP_PROTOCOL', self.protocol)
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-KEY': self.parsed_api_key['value'],
            'NOPAUSE_PYTHON_SDK_VERSION': nopause.__version__,
        })

    @classmethod
    def prepare_audio_files(cls, audio_files: List[str]):
        un_supported_files = []
        for audio_file in audio_files:
            if audio_file.endswith('.wav') or audio_file.endswith('.mp3'):
                continue
            else:
                un_supported_files.append(audio_file)
        if len(un_supported_files) > 0:
            raise FormatError("Only the audio formats with .wav and .mp3 are supported to add voice, but got {}".format(un_supported_files))

        form_audio_data = []
        for audio_file in audio_files:
            form_audio_data.append((Path(audio_file).name, open(audio_file, 'rb')))
        return form_audio_data

    @classmethod
    def parse_result(cls, result):
        message = None

        try:
            response = result.json()
        except json.decoder.JSONDecodeError:
            message = result.content
            response = {}

        if result.status_code != 200:
            if message is None:
                message = response.get('detail')
                if message is None:
                    message = response.get('message')
            raise InvalidRequestError(message=message, code=result.status_code)

        if response.get('code') != 0:
            raise NoPauseError(message=response.get('status'), code=response.get('code'))
        return response

    @classmethod
    def add(cls, audio_files: List[str], voice_name: str, language: str = 'en', description: str = None, gender: str = None, **kwargs):
        api = cls(**kwargs)
        try:
            form_audio_data = cls.prepare_audio_files(audio_files)
            files = [ ('audio_files', x) for x in form_audio_data ]
            files.extend([
                ("voice_name", (None, voice_name)),
                ("language", (None, language)),
                ("description", (None, description)),
                ("gender", (None, gender)),
            ])
            url = '{protocol}://{path}'.format(protocol=api.protocol, path=posixpath.join(api.parsed_api_base['value'], api.parsed_api_version['value'], api.name))
            result = api.session.put(url, files=files)
        except RequestException as e:
            raise InvalidRequestError(cls.display_parsed_settings(api.parsed_api_base, api.parsed_api_version, url, error=str(e)))
        except BaseException as e:
            raise e
        parsed_result = cls.parse_result(result)
        data = parsed_result.get('data')
        data['trace_id'] = parsed_result['trace_id']
        return NoPauseResponse.create(data, name='AddVoice')

    @classmethod
    def get_voices(cls, page: int = 1, page_size: int = 100, **kwargs):
        api = cls(**kwargs)
        try:
            url = '{protocol}://{path}'.format(protocol=api.protocol, path=posixpath.join(api.parsed_api_base['value'], api.parsed_api_version['value'], api.name))
            result = api.session.get(url, params=dict(page=page, page_size=page_size))
        except RequestException as e:
            raise InvalidRequestError(cls.display_parsed_settings(api.parsed_api_base, api.parsed_api_version, url, error=str(e)))
        except BaseException as e:
            raise e
        parsed_result = cls.parse_result(result)
        data = parsed_result.get('data')
        data['page'] = page # todo: check the page based on the total and page_size
        data['page_size'] = page_size
        data['trace_id'] = parsed_result['trace_id']
        return NoPauseResponse.create(data, name='Voices')

    @classmethod
    def delete(cls, voice_id: str, **kwargs):
        api = cls(**kwargs)
        try:
            url = '{protocol}://{path}'.format(protocol=api.protocol, path=posixpath.join(api.parsed_api_base['value'], api.parsed_api_version['value'], api.name))
            result = api.session.delete(url, json=dict(voice_id=voice_id))
        except RequestException as e:
            raise InvalidRequestError(cls.display_parsed_settings(api.parsed_api_base, api.parsed_api_version, url, error=str(e)))
        except BaseException as e:
            raise e
        parsed_result = cls.parse_result(result)
        data = parsed_result.get('data')
        data['trace_id'] = parsed_result['trace_id']
        return NoPauseResponse.create(data, name='DeleteVoice')
