# Copyright 2023 NoPause IO

import asyncio
import pyaudio
import openai
import nopause

# insall sdk packages first:
#      pip install openai nopause

# for pyaudio (see https://pypi.org/project/PyAudio/):
#  * windows
#     python -m pip install pyaudio
#  * mac
#     brew install portaudio
#     pip install pyaudio

openai.api_key = "your_openai_api_key_here"
nopause.api_key = "your_nopause_api_key_here"

async def chatgpt_stream(prompt: str):
    responses = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": "You are a helpful assistant from NoPause IO."},
                {"role": "user", "content": prompt},
        ],
        stream=True,
    )
    print("[User]: {}".format(prompt))
    print("[Assistant]: ", end='')
    async for response in responses:
        content = response["choices"][0]["delta"].get("content", '')
        print(content, end='')
        yield content
    print('')

async def text_stream():
    sentence = "Hello, how are you?"
    print("[Text]: ")
    for char in sentence:
        print(char, end='')
        yield char
        await asyncio.sleep(0.001)
    print('')

async def main():
    # Note: openai key is needed for chatgpt
    text_stream_type = 'chatgpt' # chatgpt | text

    if text_stream_type == 'chatgpt':
        text_agenerator = await chatgpt_stream("Hello, who are you?")
    else:
        text_agenerator = await text_stream()

    audio_chunks = await nopause.Synthesis.astream(text_agenerator, voice_id="Zoe")

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=24000,
        output=True,
    )

    async for chunk in audio_chunks:
        stream.write(chunk.data)

    await asyncio.sleep(1)

    stream.close()
    p.terminate()

if __name__ == '__main__':
    asyncio.run(main())
