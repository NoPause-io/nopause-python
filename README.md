# NoPause Python SDK

Stream your LLM output in real-time through NoPause TTS API to produce seamless speech, putting an end to LLM latency woes.

## Installation

You can install the NoPause TTS library via pip:

```bash
pip install nopause
```

## Quick Start

To use NoPause SDK, you will need an API key. You could get one by signing up at [NoPause](https://nopause.io/).

### Stream Synthetic Audio and Playback

Here's an example to synthesize audio using NoPause and stream play the audio:

(1) Install [SoundDevice](https://pypi.org/project/sounddevice/) to play audio locally.
```bash
pip install sounddevice
```

(2) Fill in the API key of NoPause, then run this example:

```python
import time
import sounddevice as sd
import nopause

nopause.api_key = "your_nopause_api_key_here"

def text_stream():
    sentence = "Hello! I am a helpful assistant from NoPause IO. I'm here to assist you with any questions or tasks you might have. How can I help you today?"
    for char in sentence:
        time.sleep(0.01) # simulate streaming text. It could be also removed.
        yield char
        print(char, end='', flush=True)
    print()

text_generator = text_stream()
audio_chunks = nopause.Synthesis.stream(text_generator, voice_id="Zoe")

stream = sd.RawOutputStream(
        samplerate=24000, blocksize=4800,
        device=sd.query_devices(kind="output")['index'],
        channels=1, dtype='int16',
        )

with stream:
    for chunk in audio_chunks:
        stream.write(chunk.data)
    time.sleep(1)

print('Play done.')
```
Alternatively, you could play audio with [PyAudio](https://pypi.org/project/PyAudio/). For more details, see [pyaudio example](examples/stream_play_with_chatgpt_pyaudio.py).

### Streaming Audio Playback Generated from ChatGPT Output
Here's an example of using NoPause TTS along with OpenAI's ChatGPT API:

(1) Install [OpenAI](https://github.com/openai/openai-python) SDK to access ChatGPT:
```bash
pip install openai
```
Note, the API key of ChatGPT should be applied from OpenAI first.

(2) Fill in the API keys for both OpenAI and NoPause, then run this example:

```python
import time
import sounddevice as sd
import openai
import nopause

openai.api_key = "your_openai_api_key_here"
nopause.api_key = "your_nopause_api_key_here"

def chatgpt_stream(prompt: str):
    responses = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": "You are a helpful assistant from NoPause IO."},
                {"role": "user", "content": prompt},
        ],
        stream=True,
    )
    print("[User]: {}".format(prompt))
    print("[Assistant]: ", end='')

    def generator():
        for response in responses:
            content = response["choices"][0]["delta"].get("content", '')
            print(content, end='')
            yield content
        print()
    return generator

text_generator = chatgpt_stream('Hello, who are you?')
audio_chunks = nopause.Synthesis.stream(text_generator, voice_id="Zoe")

stream = sd.RawOutputStream(
        samplerate=24000, blocksize=4800,
        device=sd.query_devices(kind="output")['index'],
        channels=1, dtype='int16',
        )

with stream:
    for chunk in audio_chunks:
        stream.write(chunk.data)
    time.sleep(1)

print('Play done.')
```

For more examples, such as ```Asynchronous Streaming Audio Synthesis and Playing``` or ```Interrupting Synthesis```, see [examples/*.py](examples/) and [tests/*.py](tests/).

## API Reference

### `Class Synthesis`

A WebSocket client for NoPause TTS synthesis API.

#### `Synthesis.stream()`

Creates a dual-stream synthesis.

##### Arguments

- `text_iter`: An iterable of strings to be synthesized.
- `api_key`: NoPause API key.
- `voice_id`: Which voice to use.
- `model_name`: Which NoPause model to use (default: `'nopause-en-beta'`).
- `language`: Which language to use (default: `'en'`).
- `dual_stream_config`: A `DualStreamConfig` object (default: `None`).
- `audio_config`: An `AudioConfig` object (default: `None`).
- `api_key`: The API key of NoPause. (default: `None`).
- `api_base`: The base URL for the NoPause API (default: `None`).
- `api_version`: The version of the NoPause API to use (default: `None`).

##### Returns

- A generator of `AudioChunk` objects.

#### `Synthesis.astream()`

Creates a dual-stream synthesis (asynchronous version). The arguments are the same as `Synthesis.stream()`, except that the `text_iter` should be an asynchronous generator. And it returns an asynchronous generator of `AudioChunk` objects.


### `Class Voice`

The voice APIs provides the addition and deletion of custom voice, and can also list all current voices.

#### `Voice.add()`

This API could be used to add a new voice with custom audios.

##### Arguments

- `audio_files`: A list of local file path of audios to create a custom voice. All auidos should be sampled from the same person. (max number of files: `10`)
- `voice_name`: Custom voice name. if not provided, it will be randomly generated. (default: `None`)
- `language`: The language of target voice. (default: `en`)
- `description`: The description of target voice. (default: `None`)
- `gender`: The gender of target voice. (default: `None`)
- `api_key`: The API key of NoPause. (default: `None`).
- `api_base`: The base URL for the NoPause API (default: `None`).
- `api_version`: The version of the NoPause API to use (default: `None`).

##### Returns

`AddVoiceResponse`

- `voice_id`: The generated voice ID for the target voice.
- `voice_name`: The name of target voice.
- `trace_id`: An ID used to track the current request. It can help locate reported issues.


#### `Voice.get_voices()`

This API is used to list available voices page by page.

##### Arguments

- `page`: The index of page to view. (1-based, default: `1`)
- `page_size`: The size of one page. (default: `10`)
- `api_key`: The API key of NoPause. (default: `None`).
- `api_base`: The base URL for the NoPause API (default: `None`).
- `api_version`: The version of the NoPause API to use (default: `None`).

##### Returns

`VoicesResponse`

- `voices`: A list of a series voice which contains the `voice_name: str`, `voice_id: str`, `voice_type: str`, `description: str` and `audios: list[audio_filename]`
- `total`: Total numbers of avaiable voices rather than the number of returned voices of current page.
- `trace_id`: An ID used to track the current request. It can help locate reported issues.


#### `Voice.delete()`

This API could be used to delte a custom voice by voice ID.

##### Arguments

- `voice_id`: The voice ID of target voice to delete.
- `api_key`: The API key of NoPause. (default: `None`).
- `api_base`: The base URL for the NoPause API (default: `None`).
- `api_version`: The version of the NoPause API to use (default: `None`).

##### Returns

`DeleteVoiceResponse`

- `voice_id`: The unique voice ID of target voice.
- `voice_name`: The name of target voice.
- `trace_id`: An ID used to track the current request. It can help locate reported issues.

