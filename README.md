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
import threading
import queue
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

q = queue.Queue()
event = threading.Event()
input_done = False

def callback(outdata, frames, time, status):
    global input_done
    if q.empty():
        outdata[:] = b'\x00' * len(outdata)
        if input_done:
            event.set()
        return
    chunk_data = q.get()
    # single channel
    outdata[:len(chunk_data)] = chunk_data
    if len(chunk_data) < len(outdata):
        outdata[len(chunk_data):] = b'\x00' * (len(outdata) - len(chunk_data))
    if input_done and q.empty():
        event.set()

samplerate = 24000
blocksize = 4800
stream = sd.RawOutputStream(
    samplerate=samplerate, blocksize=blocksize,
    device=sd.query_devices(kind="output")['index'],
    channels=1, dtype='int16',
    callback=callback)

with stream:
    for chunk in audio_chunks:
        # Note, a block of int16 (blocksize*1 16-bit) = two blocks of bytes (blocksize*2 8-bit)
        for i in range(0, len(chunk.data), blocksize*2):
            q.put_nowait(chunk.data[i:i+blocksize*2])
    input_done = True

    event.wait()
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
import threading
import queue
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
    for response in responses:
        content = response["choices"][0]["delta"].get("content", '')
        print(content, end='')
        yield content
    print()


text_generator = chatgpt_stream('Hello, who are you?')
audio_chunks = nopause.Synthesis.stream(text_generator, voice_id="Zoe")

q = queue.Queue()
event = threading.Event()
input_done = False

def callback(outdata, frames, time, status):
    global input_done
    if q.empty():
        outdata[:] = b'\x00' * len(outdata)
        if input_done:
            event.set()
        return
    chunk_data = q.get()
    # single channel
    outdata[:len(chunk_data)] = chunk_data
    if len(chunk_data) < len(outdata):
        outdata[len(chunk_data):] = b'\x00' * (len(outdata) - len(chunk_data))
    if input_done and q.empty():
        event.set()

samplerate = 24000
blocksize = 4800
stream = sd.RawOutputStream(
    samplerate=samplerate, blocksize=blocksize,
    device=sd.query_devices(kind="output")['index'],
    channels=1, dtype='int16',
    callback=callback)

with stream:
    for chunk in audio_chunks:
        # Note, a block of int16 (blocksize*1 16-bit) = two blocks of bytes (blocksize*2 8-bit)
        for i in range(0, len(chunk.data), blocksize*2):
            q.put_nowait(chunk.data[i:i+blocksize*2])
    input_done = True

    event.wait()
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
- `api_base`: The base URL for the NoPause API (default: `None`).
- `api_version`: The version of the NoPause API to use (default: `None`).

##### Returns

- A generator of `AudioChunk` objects.

#### `Synthesis.astream()`

Creates a dual-stream synthesis (asynchronous version). It will return a agenerator of `AudioChunk` objects.
