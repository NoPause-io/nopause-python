""" NoPause dual-stream TTS synthesis Python SDK
"""

import os
import base64
import asyncio
import threading
import websockets
import ujson as json
from typing import Any, Iterable, AsyncIterable, Union
from websockets.client import WebSocketClientProtocol
from websockets.sync.client import ClientConnection

import nopause
from nopause.core.audio import AudioChunk, TextChunk
from nopause.sdk.config import ModelConfig, AudioConfig, DualStreamConfig
from nopause.sdk.error import InvalidRequestError, NoPauseError

SYNTHESIS_API_NAME = 'tts/dual-stream'

DEFAULT_MODEL_NAME = 'nopause-en-beta'
DEFAULT_LANGUAGE = 'en'

class SynthesisResultGenerator:
    """It is could be used as a generator or an async generator according to the websocket protocol.
    """
    def __init__(self, ws: Union[WebSocketClientProtocol, ClientConnection], send_text_task: Union[asyncio.Task, threading.Thread]):
        self.ws = ws
        if isinstance(ws, WebSocketClientProtocol):
            self.use_async = True
        else:
            self.use_async = False

        self.send_text_task = send_text_task
        self.is_end = False

    def parse_result(self, data):
        if data['code'] != 0:
            raise NoPauseError(data['status'], code=data['code'])

        if data["audio_content"]:
            chunk = AudioChunk(
                data=base64.b64decode(data["audio_content"]),
                chunk_id=data['tts_response_chunk_meta']['chunk_id'],
                sample_rate=24000, # default
                channels=1, # default
                rtf=data['tts_response_chunk_meta']['rtf'],
                chunk_size_us=data['tts_response_chunk_meta']['chunk_size_us'],
                # is_last_chunk=data['is_end'],
            )
        else:
            chunk = None
        return chunk, data['is_end']

    def __next__(self):
        if self.is_end:
            self.close()
            raise StopIteration
        try:
            data = json.loads(self.ws.recv())
            chunk, is_end = self.parse_result(data)
        except Exception as e:
            self.close()
            if isinstance(e, websockets.exceptions.WebSocketException):
                raise InvalidRequestError(str(e))
            else:
                raise e

        if is_end:
            self.is_end = True
            if chunk is None:
                self.close()
                raise StopIteration # todo: return a empty chunk to return a is_end signal?
            else:
                return chunk
        elif chunk is None:
            # get empty chunk but not end: continue receive
            return next(self)
        else:
            return chunk

    async def __anext__(self):
        if self.is_end:
            await self.aclose()
            raise StopAsyncIteration
        try:
            data = json.loads(await self.ws.recv())
            chunk, is_end = self.parse_result(data)
        except Exception as e:
            await self.aclose()
            if isinstance(e, websockets.exceptions.WebSocketException):
                raise InvalidRequestError(str(e))
            else:
                raise e

        if is_end:
            self.is_end = True
            if chunk is None:
                await self.aclose()
                raise StopAsyncIteration # todo: return a empty chunk to return a is_end signal?
            else:
                return chunk
        elif chunk is None:
            # get empty chunk but not end: continue receive
            return await anext(self)
        else:
            return chunk

    def __iter__(self):
        return self

    def __aiter__(self):
        return self

    def terminate(self):
        assert not self.use_async
        self.is_end = True
        if not self.send_text_task.done():
            self.send_text_task.cancel()
        self.close()

    async def aterminate(self):
        assert self.use_async
        self.is_end = True
        if not self.send_text_task.done():
            self.send_text_task.cancel()
            await self.send_text_task
        await self.aclose()

    def close(self):
        assert not self.use_async
        try:
            self.ws.close()
        except websockets.exceptions.WebSocketException.ConnectionClosed:
            pass

    async def aclose(self):
        assert self.use_async
        try:
            await self.ws.close()
        except websockets.exceptions.WebSocketException.ConnectionClosed:
            pass

class Synthesis:
    """ A WebSocket client for NoPause TTS synthesis API.
    """
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

    @staticmethod
    def prepare_bos_and_eos(
        voice_id: str,
        model_name: str = DEFAULT_MODEL_NAME,
        language: str = DEFAULT_LANGUAGE,
        audio_config: AudioConfig = None,
        dual_stream_config: DualStreamConfig = None
        ):
        if dual_stream_config is None:
            dual_stream_config = {}

        BOS = {"config": ModelConfig(voice_id=voice_id, model_name=model_name, language=language, dual_stream=dual_stream_config).dict()}
        EOS = {"content": TextChunk(text='', is_end=True).dict()}
        return BOS, EOS

    @classmethod
    def stream(
        cls,
        text_iter: Iterable[str],
        voice_id: str,
        model_name: str = DEFAULT_MODEL_NAME,
        language: str = DEFAULT_LANGUAGE,
        audio_config: AudioConfig = None,
        dual_stream_config: DualStreamConfig = None,
        api_key: str = None,
        api_base: str = None,
        api_version: str = None,
    ) -> Iterable[AudioChunk]:
        """
        Creates a dual-stream synthesis
        Args:
            text_iter: An iterable of strings to be synthesized.
            voice_id: Which voice to use.
            model_name: Which NoPause model to use.
            language: Which language to use.
            dual_stream_config: A DualStreamConfig object.
            audio_config: An AudioConfig object.
            api_key: NoPause API key.
            api_base: The base URL for the NoPause API.
            api_version: The version of the NoPause API to use.
        Returns:
            A generator of AudioChunk objects.
        """
        parsed_api_key, parsed_api_base, parsed_api_version = cls.parse_settings(api_key, api_base, api_version)
        api_url = os.path.join(parsed_api_base['value'], parsed_api_version['value'], SYNTHESIS_API_NAME)
        try:
            websocket = websockets.sync.client.connect(
                api_url,
                additional_headers={
                    'X-API-KEY': parsed_api_key['value']
                }
            )
        except websockets.exceptions.WebSocketException as e:
            raise InvalidRequestError(
                f'{str(e)}\n\n[NoPause Settings] (Parsing Order: function_param > environment > nopause.env)'
                f'\n* API_BASE: {parsed_api_base}\n* API_VERSION: {parsed_api_version}\n* API_URL: {api_url}')
        except BaseException as e:
            raise e

        BOS, EOS = cls.prepare_bos_and_eos(
            voice_id, model_name, language, audio_config, dual_stream_config
        )

        class SendTextTask(threading.Thread):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.event = threading.Event()
                self._done = False

            def cancel(self):
                self.event.set()

            def done(self):
                return self._done

            def run(self):
                if not self.event.is_set():
                    websocket.send(json.dumps(BOS))
                # It could be still blocked in the 'for' grammar if the text_iter is blocked
                for text in text_iter:
                    if self.event.is_set():
                        break
                    websocket.send(json.dumps({"content": TextChunk(text=text, is_end=False).dict()}))
                if not self.event.is_set():
                    websocket.send(json.dumps(EOS))
                self._done = True

        send_text_task = SendTextTask(daemon=True)
        send_text_task.start()

        return SynthesisResultGenerator(websocket, send_text_task)


    @classmethod
    async def astream(
        cls,
        text_iter: AsyncIterable[str],
        voice_id: str,
        model_name: str = DEFAULT_MODEL_NAME,
        language: str = DEFAULT_LANGUAGE,
        audio_config: AudioConfig = None,
        dual_stream_config: DualStreamConfig = None,
        api_key: str = None,
        api_base: str = None,
        api_version: str = None,
    ) -> AsyncIterable[AudioChunk]:
        """ Async version of stream()
        """
        parsed_api_key, parsed_api_base, parsed_api_version = cls.parse_settings(api_key, api_base, api_version)
        api_url = os.path.join(parsed_api_base['value'], parsed_api_version['value'], SYNTHESIS_API_NAME)
        try:
            websocket = await websockets.client.connect(
                api_url,
                extra_headers={
                    'X-API-KEY': parsed_api_key['value']
                }
            )
        except websockets.exceptions.WebSocketException as e:
            # Do not record the api key to avoid leakage. 
            # If the api key is provided but the request response is 403, 
            # it is likely that the api key or api version verification failed
            raise InvalidRequestError(
                f'{str(e)}\n\n[NoPause Settings] (Parsing Order: function_param > environment > nopause.env)'
                f'\n* API_BASE: {parsed_api_base}\n* API_VERSION: {parsed_api_version}\n* API_URL: {api_url}')
        except BaseException as e:
            raise e

        BOS, EOS = cls.prepare_bos_and_eos(
            voice_id, model_name, language, audio_config, dual_stream_config
        )

        async def send_text():
            try:
                await websocket.send(json.dumps(BOS))
                async for text in text_iter:
                    await websocket.send(json.dumps({"content": TextChunk(text=text, is_end=False).dict()}))
                await websocket.send(json.dumps(EOS))
            except asyncio.CancelledError:
                pass

        send_text_task = asyncio.create_task(send_text())

        return SynthesisResultGenerator(websocket, send_text_task)
