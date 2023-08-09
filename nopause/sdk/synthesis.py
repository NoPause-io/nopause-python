""" NoPause dual-stream TTS synthesis Python SDK
"""
from typing import Iterable, AsyncIterable
from nopause.core.audio import AudioChunk
from nopause.sdk.config import AudioConfig, DualStreamConfig


class Synthesis:
    """ A WebSocket client for NoPause TTS synthesis API.
    """

    @classmethod
    def stream(
        cls,
        text_iter: Iterable[str],
        voice_id: str,
        model_name: str = 'nopause-en-beta',
        language: str = 'en',
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


    @classmethod
    async def astream(
        cls,
        text_iter: Iterable[str],
        voice_id: str,
        model_name: str = 'nopause-en-beta',
        language: str = 'en',
        audio_config: AudioConfig = None,
        dual_stream_config: DualStreamConfig = None,
        api_key: str = None,
        api_base: str = None,
        api_version: str = None,
    ) -> AsyncIterable[AudioChunk]:
        """ Async version of stream()
        """