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

```python
import openai
import nopause
import pyaudio

openai.api_key = "your_openai_api_key_here"
nopause.api_key = "your_nopause_api_key_here"

def chatgpt_stream(prompt: str):
    responses = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
        ],
        stream=True,
    )
    for response in responses:
        yield response["choices"][0]["delta"].get("content", '')

audio_chunks = nopause.Synthesis.stream(
    chatgpt_stream("How to make a cake?"),
    voice_id="david",
)

p = pyaudio.PyAudio()

stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=24000,
    output=True,
)

for chunk in audio_chunks:
    stream.write(chunk.data)

stream.close()
p.terminate()
```

## API Reference

### `class Synthesis`

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

Creates a dual-stream synthesis (asynchronous version).