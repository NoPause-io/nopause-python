""" NoPause dual-stream TTS synthesis Python SDK
"""

import os
import base64
import asyncio
import threading
import inspect
import websockets
import ujson as json
import ssl
from typing import Any, Iterable, AsyncIterable, Union
from asyncio.exceptions import CancelledError
from websockets.client import WebSocketClientProtocol
from websockets.sync.client import ClientConnection
from websockets.exceptions import WebSocketException, ConnectionClosed

import nopause
from nopause.core.audio import AudioChunk, TextChunk
from nopause.sdk.base import BaseAPI
from nopause.sdk.config import ModelConfig, AudioConfig, DualStreamConfig
from nopause.sdk.error import InvalidRequestError, NoPauseError

DEFAULT_MODEL_NAME = 'nopause-en-beta'
DEFAULT_VOICE_ID = 'Zoe'
DEFAULT_LANGUAGE = 'en'


class Synthesis(BaseAPI):
    """ A WebSocket client for NoPause TTS synthesis API.
    """
    name: str = 'tts/dual-stream'
    protocol: str = 'wss'

    def __init__(
        self,
        voice_id: str = DEFAULT_VOICE_ID,
        model_name: str = DEFAULT_MODEL_NAME,
        language: str = DEFAULT_LANGUAGE,
        audio_config: AudioConfig = None,
        dual_stream_config: DualStreamConfig = None,
        api_key: str = None,
        api_base: str = None,
        api_version: str = None,
        **kwargs,
        ):
        """
        Args:
            voice_id: Select the voice to use.
            model_name: Choose the NoPause model to use.
            language: Identify the language to use.
            dual_stream_config: This requires a DualStreamConfig object.
            audio_config: This pertains to an AudioConfig object.
            api_key: This refers to the NoPause API key.
            api_base: This is the base URL for the NoPause API.
            api_version: Determine the version of the NoPause API to use.

        Usage:
            (1) Do stream of synthesis after connection to save the time of connection
            The configurations must be assigned to the instance and are not required again for stream/astream calling.

            [sync]
                synthesizer = Synthesis(**config).connect()
                #- prepare other resources -#
                synthesizer.stream(text_iterator)

            [async]
                async_synthesizer = await Synthesis(**config).aconnect()
                #- prepare other resources -#
                await async_synthesizer.astream(text_iterator)

            (2) One-step synthesis (connect + synthesis) can be done by class method.
            The configurations are necessary for stream/astream calling.

            [sync]
                Synthesis.stream(text_iterator, **config)

            [async]
                await Synthesis.stream(text_iterator, **config)
        """

        self.voice_id = voice_id
        self.model_name = model_name
        self.language = language
        self.audio_config = audio_config if audio_config is not None else AudioConfig()
        self.dual_stream_config = dual_stream_config if dual_stream_config is not None else DualStreamConfig()

        self.parsed_api_key, self.parsed_api_base, self.parsed_api_version = self.parse_settings(api_key, api_base, api_version)
        self.protocol = os.environ.get('NO_PAUSE_WS_PROTOCOL', self.protocol)
        self.api_url = '{protocol}://{path}'.format(protocol=self.protocol, path=os.path.join(self.parsed_api_base['value'], self.parsed_api_version['value'], self.name))

        self.bos, self.eos = self.prepare_bos_and_eos(
            voice_id=self.voice_id,
            model_name=self.model_name,
            language=self.language,
            audio_config=self.audio_config,
            dual_stream_config=self.dual_stream_config
        )

        self.ws = None # websocket client, could be sync or async
        self._in_use = False

        # make sure that one instance processes one request only
        self.async_semaphore = asyncio.Semaphore(1)
        self.semaphore = threading.Semaphore(1)
        self.async_connect_semaphore = asyncio.Semaphore(1)
        self.connect_semaphore = threading.Semaphore(1)

    def in_use(self):
        with self.semaphore:
            return self._in_use

    async def ain_use(self):
        async with self.async_semaphore:
            return self._in_use
    
    async def set_used(self):
        with self.semaphore:
            if self._in_use:
                raise NoPauseError('More than one request of synthesis should not be conducted based on one websocket.')
            self._in_use = True

    async def aset_used(self):
        async with self.async_semaphore:
            if self._in_use:
                raise NoPauseError('More than one request of synthesis should not be conducted based on one websocket.')
            self._in_use = True

    async def free_used(self):
        with self.semaphore:
            self._in_use = False

    async def afree_used(self):
        async with self.async_semaphore:
            self._in_use = False

    @staticmethod
    def prepare_bos_and_eos(
        voice_id: str = DEFAULT_VOICE_ID,
        model_name: str = DEFAULT_MODEL_NAME,
        language: str = DEFAULT_LANGUAGE,
        audio_config: AudioConfig = None,
        dual_stream_config: DualStreamConfig = None
        ):
        if audio_config is None:
            audio_config = AudioConfig()

        if dual_stream_config is None:
            dual_stream_config = DualStreamConfig()

        BOS = {
            "config": ModelConfig(voice_id=voice_id, model_name=model_name, language=language, dual_stream=dual_stream_config).dict(),
            "audio_config": audio_config.dict(by_alias=True),
            }
        EOS = {"content": TextChunk(text='', is_end=True).dict()}
        return BOS, EOS
    
    def parse_result(self, data):
        if data['code'] != 0:
            raise NoPauseError(data['status'], code=data['code'])
    
    def check_alive(self):
        alive = True
        if self.ws is not None:
            try:
                self.ws.ping()
            except ConnectionClosed:
                alive = False
        else:
            alive = False
        return alive

    async def acheck_alive(self):
        alive = True
        if self.ws is not None:
            try:
                await self.ws.ping()
            except ConnectionClosed:
                alive = False
        else:
            alive = False
        return alive

    def connect(self):
        with self.semaphore:
            try:
                is_alive = self.check_alive()
                if is_alive: return self
                
                self.ws = websockets.sync.client.connect(
                    self.api_url,
                    additional_headers={
                        'X-API-KEY': self.parsed_api_key['value'],
                        'NOPAUSE_PYTHON_SDK_VERSION': nopause.__version__,
                    }
                )
                # make sure the config ready
                self.ws.send(json.dumps(self.bos))
            except (WebSocketException, TimeoutError, ssl.SSLError) as e:
                self.close()
                raise InvalidRequestError(self.display_parsed_settings(self.parsed_api_base, self.parsed_api_version, self.api_url, error=str(e)))
            except BaseException as e:
                raise e
        return self

    async def aconnect(self):
        async with self.async_connect_semaphore:
            try:
                is_alive = await self.acheck_alive()
                if is_alive: return self

                # init connection
                self.ws = await websockets.client.connect(
                    self.api_url,
                    extra_headers={
                        'X-API-KEY': self.parsed_api_key['value'],
                        'NOPAUSE_PYTHON_SDK_VERSION': nopause.__version__,
                    }
                )
                # make sure the config ready
                await self.ws.send(json.dumps(self.bos))
            except (WebSocketException, TimeoutError, ssl.SSLError) as e:
                await self.aclose()
                # The api key is not displayed to avoid leakage from log file. 
                # If the api key is provided but the request response is 403, 
                # it is likely that the api key or api version verification failed
                raise InvalidRequestError(self.display_parsed_settings(self.parsed_api_base, self.parsed_api_version, self.api_url, error=str(e)))
            except BaseException as e:
                raise e
        return self

    def __new__(cls, *args, **kwargs):
        """
        Sharing function names between class methods and instance methods, such as stream/atream.
        Here, the methods of stream/astream will be overridden by a instance method when new an instance.
        Note, it uses a new class which is not equal to the original class, so it will not influence the original Synthesis class.
        """
        new_cls = type(cls.__name__, (cls,), {})
        self = object.__new__(new_cls)
        # make sure the type(self) == cls (new_cls will be not needed to be accessed in anytime)
        self.__class__ = cls
        # overide the original classmethod
        self.stream = self._stream
        self.astream = self._astream
        return self
    
    def _stream(
        cls_or_self,
        text_iter: Iterable[str],
        *args,
        **kwargs,
    ) -> Iterable[AudioChunk]:
        if inspect.isclass(cls_or_self):
            # stream called as classmethod
            synthesizer = cls_or_self(*args, **kwargs).connect()
            synthesizer.set_used()
            terminate_always = True
        else:
            # stream called as instance method
            synthesizer = cls_or_self
            synthesizer.set_used()
            terminate_always = False
            synthesizer.connect()

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
                # It could be still blocked in the 'for' grammar if the text_iter is blocked
                for text in text_iter:
                    if self.event.is_set():
                        break
                    synthesizer.ws.send(json.dumps({"content": TextChunk(text=text, is_end=False).dict()}))
                if not self.event.is_set():
                    synthesizer.ws.send(json.dumps(synthesizer.eos))
                self._done = True

        send_text_task = SendTextTask(daemon=True)
        send_text_task.start()

        return SynthesisResultGenerator(synthesizer, send_text_task, terminate_always=terminate_always)
    
    async def _astream(
        cls_or_self,
        text_iter: AsyncIterable[str],
        *args,
        **kwargs,
    ) -> AsyncIterable[AudioChunk]:
        if inspect.isclass(cls_or_self):
            # stream called as classmethod
            synthesizer = await cls_or_self(*args, **kwargs).aconnect()
            await synthesizer.aset_used()
            terminate_always = True
        else:
            # stream called as instance method
            synthesizer = cls_or_self
            await synthesizer.aset_used()
            terminate_always = False
            await synthesizer.aconnect()

        async def send_text():
            try:
                async for text in text_iter:
                    await synthesizer.ws.send(json.dumps({"content": TextChunk(text=text, is_end=False).dict()}))
                await synthesizer.ws.send(json.dumps(synthesizer.eos))
            except CancelledError:
                pass

        send_text_task = asyncio.create_task(send_text())

        return SynthesisResultGenerator(synthesizer, send_text_task, terminate_always=terminate_always)

    @classmethod
    def stream(
        cls,
        text_iter: Iterable[str],
        *args,
        **kwargs,
    ) -> Iterable[AudioChunk]:
        """
        Create a dual-stream synthesis.
        It could be used as both classmethod and instance method, see the note of usage in the Synthesis.__init__.
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
        return cls._stream(cls, text_iter, **kwargs)

    @classmethod
    async def astream(
        cls,
        text_iter: AsyncIterable[str],
        *args,
        **kwargs,
    ) -> AsyncIterable[AudioChunk]:
        """
        Create an async dual-stream synthesis.
        It could be used as both classmethod and instance method, see the note of usage in the Synthesis.__init__.
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
            An async generator of AudioChunk objects.
        """
        return await cls._astream(cls, text_iter, *args, **kwargs)
    
    def close(self):
        if self.ws is not None:
            try:
                self.ws.close()
            except ConnectionClosed:
                pass
        self.ws = None
        self.free_used()

    async def aclose(self):
        if self.ws is not None:
            try:
                await self.ws.close()
            except ConnectionClosed:
                pass
        self.ws = None
        await self.afree_used()

    def interrupt(self):
        self.close()
        self.connect()

    async def ainterrupt(self):
        # drop the interrupted-request by closing the current websocket and create a new connection soon
        await self.aclose()
        await self.aconnect()


class SynthesisResultGenerator:
    """It is could be used as a generator or an async generator according to the websocket protocol.
    """
    def __init__(
        self,
        synthesizer: Synthesis,
        send_text_task: Union[asyncio.Task, threading.Thread],
        terminate_always: bool = True,
        ):
        self._synthesizer = synthesizer
        self.ws = self._synthesizer.ws # Union[WebSocketClientProtocol, ClientConnection]
        if isinstance(self.ws, WebSocketClientProtocol):
            self.use_async = True
        else:
            self.use_async = False

        self.send_text_task = send_text_task
        self.is_end = False # for receiving text
        self.terminated = False
        self.terminate_always = terminate_always

    def parse_result(self, data):
        if data['code'] != 0:
            raise NoPauseError(data['status'], code=data['code'])

        if data["audio_content"]:
            chunk = AudioChunk(
                data=base64.b64decode(data["audio_content"]),
                chunk_id=data['tts_response_chunk_meta']['chunk_id'],
                sample_rate=self._synthesizer.audio_config.sample_rate,
                channels=1, # default
                rtf=data['tts_response_chunk_meta']['rtf'],
                chunk_size_us=data['tts_response_chunk_meta']['chunk_size_us'],
                # is_last_chunk=data['is_end'],
            )
        else:
            chunk = None
        return chunk, data['is_end']

    def __next__(self):
        if self.terminated:
            raise StopIteration

        if self.is_end:
            if self.terminate_always:
                self.terminate()
            self._synthesizer.free_used()
            raise StopIteration
        try:
            data = json.loads(self.ws.recv())
            chunk, is_end = self.parse_result(data)
        except Exception as e:
            if not self.terminated:
                self.terminate()
            if isinstance(e, WebSocketException):
                raise InvalidRequestError(str(e))
            else:
                raise e

        if is_end:
            self.is_end = True
            if chunk is None:
                if self.terminate_always:
                    self.terminate()
                self._synthesizer.free_used()
                raise StopIteration # todo: return a empty chunk to return a is_end signal?
            else:
                return chunk
        elif chunk is None:
            # get empty chunk but not end: continue receive
            return next(self)
        else:
            return chunk

    async def __anext__(self):
        if self.terminated:
            raise StopAsyncIteration

        if self.is_end:
            if self.terminate_always:
                await self.aterminate()
            await self._synthesizer.afree_used()
            raise StopAsyncIteration
        try:
            data = json.loads(await self.ws.recv())
            chunk, is_end = self.parse_result(data)
        except Exception as e:
            if not self.terminated:
                await self.aterminate()
            if isinstance(e, WebSocketException):
                raise InvalidRequestError(str(e))
            else:
                raise e

        if is_end:
            self.is_end = True
            if chunk is None:
                if self.terminate_always: await self.aterminate()
                await self._synthesizer.afree_used()
                raise StopAsyncIteration # todo?: return a empty chunk to return a is_end signal?
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
    
    def close(self):
        assert not self.use_async
        self._synthesizer.close()

    async def aclose(self):
        assert self.use_async
        await self._synthesizer.aclose()

    def terminate(self):
        """terminate every thing
        """
        assert not self.use_async
        self.terminate_always = True
        if not self.send_text_task.done():
            self.send_text_task.cancel()
        self.close()

    async def aterminate(self):
        """terminate every thing
        """
        assert self.use_async
        self.terminate_always = True
        if not self.send_text_task.done():
            self.send_text_task.cancel()
            await self.send_text_task
        error = self.send_text_task.exception()
        if error: raise error
        await self.aclose()

    def interrupt(self):
        self.terminate()
        self._synthesizer.connect()

    async def ainterrupt(self):
        # drop the data by terminate the websocket and create a new connection soon
        await self.aterminate()
        await self._synthesizer.aconnect()
