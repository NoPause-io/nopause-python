# Copyright 2023 NoPause

import os
import asyncio
import readline
import sounddevice as sd

import openai
import nopause

from nopause import AudioConfig
from nopause.utils.timestamp import time_stamp

# Install sdk packages first:
#      pip install openai nopause

# Install sounddevice (see https://pypi.org/project/sounddevice/)
#      pip install sounddevice

# config api key
## give the api key directly
# openai.api_key = "your_openai_api_key_here"
# nopause.api_key = "your_nopause_api_key_here"

## or use dotenv to load the api key from .env file
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.environ['OPENAI_API_KEY']

DEFAULT_PROMPT = "You are a helpful assistant from NoPause IO."
DEFAULT_MODEL = "gpt-3.5-turbo-0613"
DEFAULT_VOICE_ID = 'Zoe'
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_TIMESTAMP_OUTPUT = 'chat_timestamp.json'

class ChatPlayGround():
    def __init__(self, prompt: str = DEFAULT_PROMPT, voice_id: str = DEFAULT_VOICE_ID, sample_rate: int = DEFAULT_SAMPLE_RATE) -> None:
        self.prompt = prompt
        self.memory = []

        self.reset()

        self.voice_id = voice_id
        self.sample_rate = sample_rate
        self.synthesizer = nopause.Synthesis(voice_id=self.voice_id, audio_config=AudioConfig(sample_rate=self.sample_rate))
        time_stamp.add(group='TTS', event='init', use_point=True)

        self.play_device = sd.RawOutputStream(
            samplerate=DEFAULT_SAMPLE_RATE, blocksize=int(DEFAULT_SAMPLE_RATE*0.02),
            device=sd.query_devices(kind="output")['index'],
            channels=1, dtype='int16',
        )
        time_stamp.add(group='Device', event='init', use_point=True)

    def add_message(self, role, content):
        self.memory.append(dict(role=role, content=content))

    def reset(self):
        self.memory.clear()
        self.add_message(role='system', content=self.prompt)

    async def play_audio(self, audio_chunks):
        self.play_device.start()
        async for chunk in audio_chunks:
            time_stamp.add(group='Device', event='receive', use_point=True)
            self.play_device.write(chunk.data)
        await asyncio.sleep(0.5)
        self.play_device.stop()

    async def assistant(self, content: str):
        self.add_message(role='user', content=content)
        time_stamp.point()
        responses = await openai.ChatCompletion.acreate(
            model=DEFAULT_MODEL,
            messages=self.memory,
            stream=True,
        )
        time_stamp.add(group='GPT', event='connect', use_point=True)
        print('[assistant]: ', end='', flush=True)
        async def agenerator():
            content = ''
            async for response in responses:
                delta = response["choices"][0]["delta"].get("content", '')
                time_stamp.add(group='GPT', event='receive', content=delta, use_point=True)
                print(delta, end='', flush=True)
                content += delta
                yield delta
            self.add_message(role='assistant', content=content)
        time_stamp.point()
        audio_chunks = await self.synthesizer.astream(agenerator())
        time_stamp.add(group='TTS', event='start stream', use_point=True)
        await self.play_audio(audio_chunks)
        print()

    async def repeat_assistant(self, content: str):
        time_stamp.add(group='Repeat', event='repeat', content=content)
        print('[assistant]: ', end='', flush=True)
        async def agenerator():
            for c in content:
                print(c, end='', flush=True)
                yield c
        time_stamp.point()
        audio_chunks = await self.synthesizer.astream(agenerator())
        time_stamp.add(group='TTS', event='start stream', use_point=True)
        await self.play_audio(audio_chunks)
        print()

    async def user(self):
        time_stamp.point()
        content = input('[user]: ')
        time_stamp.add(group='user', event='input', content=content, use_point=True)

        if content.lower() == '[done]':
            return dict(cmd='done')
        elif content.lower() == '[exit]':
            return dict(cmd='exit')
        elif content.lower().strip().startswith('[repeat]') or content.lower().strip().startswith('[r]'):
            content = content.split(']', 1)[-1].strip()
            return dict(cmd='repeat', content=content)
        else:
            return dict(cmd='gpt', content=content)

    async def chat(self):
        print('Connect synthesizer...', end='')
        time_stamp.point()
        await self.synthesizer.aconnect()
        time_stamp.add(group='TTS', event='connect', use_point=True)
        print('done')
        print('------ new conversation ------')
        while True:
            info = await self.user()

            if info.get('cmd') == 'done':
                self.reset()
                print('------ new conversation ------')
                continue
            elif info.get('cmd') == 'exit':
                await self.synthesizer.aclose()
                break
            elif info.get('cmd') == 'repeat':
                await self.repeat_assistant(info.get('content', ''))
            elif info.get('cmd') == 'gpt':
                await self.assistant(info.get('content', ''))
            else:
                raise ValueError('{} is not supported.'.format(info))

async def main():
    time_stamp.add(group='base', event='start')
    print('Init chat playground...', end='')
    chat = ChatPlayGround()
    print('done')
    await chat.chat()
    time_stamp.add(group='base', event='end')
    time_stamp.export(DEFAULT_TIMESTAMP_OUTPUT)
    print('All done.')

if __name__ == '__main__':
    asyncio.run(main())
