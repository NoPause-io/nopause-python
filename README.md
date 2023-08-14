# NoPause Python SDK

NoPause TTS seamlessly tracks your LLM streaming output, while producing speech simultaneously -  putting an end to any LLM voice latency woes.

## Installation

You can install the NoPause TTS library via pip:

```bash
pip install nopause
```

## Usage

To use NoPause SDK, you will need an API key. You could get one by signing up at [NoPause](https://nopause.io/).

Here's an example of using NoPause TTS along with OpenAI's ChatGPT API:

(1) Install [OpenAI](https://github.com/openai/openai-python) SDK to access ChatGPT
```
pip install openai
```
(2) Install [PyAudio](https://pypi.org/project/PyAudio/) to play audio locally
```
# Windows
python -m pip install pyaudio

# Mac
brew install portaudio
pip install pyaudio
```

(3) Fill in the API keys for both OpenAI and NoPause, then run this example

```python
import time
import pyaudio
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
    print('')

text_generator = chatgpt_stream("Hello, who are you?")
audio_chunks = nopause.Synthesis.stream(text_generator, voice_id="Zoe")

p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=24000,
    output=True,
)

for chunk in audio_chunks:
    stream.write(chunk.data)

time.sleep(1)

stream.close()
p.terminate()
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
