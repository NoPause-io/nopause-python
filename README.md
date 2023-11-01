# NoPause Python SDK
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="/assets/logo-NoPause1.png">
  <source media="(prefers-color-scheme: light)" srcset="/assets/logo-NoPause2.png">
  <a href="https://nopause.io"> <img alt="NoPause.io logo" src="/assets/logo-NoPause2.png" style="width: 200px;" /> </a>
</picture>

Stream your LLM output in real-time through NoPause TTS API to produce seamless speech, putting an end to LLM latency woes.

## Installation

You can install the NoPause TTS library via pip:

```bash
pip install nopause
```

## Quick Start

To use NoPause SDK, you will need an API key. You could get one by signing up at [NoPause](https://nopause.io/).

### Stream Synthesizing Audio and Playback

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

### Try Synthesis with Chat Mode
You can also use the chat example to communicate with GPT or repeat a sentence to try the synthesis.

```
# install extra package
pip install python-dotenv readline

# prepare API key in the workdir based on .env file
echo "OPENAI_API_KEY=<your-openai-key>" >> .env
echo "NOPAUSE_API_KEY=<your-nopause-key>" >> .env

# run the example
python examples/chat.py
```

Note that there are several commands you can input in the chat mode:
`[done]`: ends the current conversation and prepares for a new one. It clears the memory of GPT.

`[exit]`: exit the chat mode and export a timestamp record to a file.

`[repeat] content` or `[r] content`: the assistant will repeat your content. It is used to test what you want to synthesize. The content is not added to the GPT memory.

For more examples, such as ```Asynchronous Streaming Audio Synthesis and Playing``` or ```Interrupting Synthesis```, see [examples/*.py](examples/) and [tests/*.py](tests/).

### Manage Voices
You can add, delete and list custom voices with the `Voice` class. Here's an example to add a custom voice:

```python
nopause.api_key = "your_nopause_api_key_here"

# show all available voices
print(nopause.Voice.get_voices())

# add a custom voice
audio_files = [
    "path/to/audio1.wav",
    "path/to/audio2.wav",
    "path/to/audio3.wav",
    "path/to/audio4.wav",
    "path/to/audio5.wav",
]
response = nopause.Voice.add(audio_files, voice_name="my_voice", language="en", description="my voice")
voice_id = response.voice_id
print(f'voice id is: {voice_id}')

# delete a custom voice
nopause.Voice.delete(voice_id)
```

## Integration
We have integrated the Python SDK into Vocode, see details at https://github.com/NoPause-io/vocode-python.
The example allows you to interact with LLM using the microphone and speaker on your local PC, you can experience it by executing the command below.

```bash
# Clone the the source code of vocode-python and select the `support_nopause_dual_stream` branch
git clone https://github.com/NoPause-io/vocode-python.git -b support_nopause_dual_stream
cd vocode-python

# If you have not installed poetry, install it first.
pip install poerty

# Install vocode from local
poerty install

# Create and configure the environments variables of ASR, LLM and TTS (NoPause) in the `.env` file in the workdir
# Such as:
#   AZURE_SPEECH_KEY = 
#   AZURE_SPEECH_REGION = "eastus"
#   OPENAI_API_KEY =
#   NO_PAUSE_API_KEY =

# Run this example
python quickstarts/dual_streaming_conversation_with_nopause_tts.py
```

Besides, you can also use `Vocode` + `NoPause` + `Twillio` to make phone calls. After you prepare all the servers according to [vocode document](https://docs.vocode.dev/open-source/telephony#overview), it is simple to use our synthesizer in a phone call. Here is an example of outbound call.

1. Similarly, prepare the environments variables of ASR, LLM and TTS (NoPause) in the .env file (assume that you have added `BASE_URL`, `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` variables)
2. Add `synthesizer_config` for `OutboundCall` object in the `apps/telephony_app/outbound_call.py` file

```python
outbound_call = OutboundCall(
        base_url=BASE_URL,
        to_phone="+15555555555",
        from_phone="+15555555555",
        config_manager=config_manager,
        transcriber_config=AzureTranscriberConfig.from_telephone_input_device(endpointing_config=PunctuationEndpointingConfig()),
        agent_config=ChatGPTAgentConfig(
                initial_message=BaseMessage(text="Hello, how can I help you today?"),
                prompt_preamble="""The AI is having a pleasant conversation about life""",
                dual_stream=True # Enable this to send text token by token
            ), # Instead of using original SpellerAgent, you can also chat with GPT
        synthesizer_config=NoPauseSynthesizerConfig.from_telephone_output_device() # Add NoPause synthesizer
    )
```

3. Fill the `to_phone` and `from_phone` and then run the `outbound_call.py` script

```bash
python apps/telephony_app/outbound_call.py
```

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

#### Stream with Pre-Connected Synthesizer
In addition to utilizing `Synthesis.stream(text_iterator, **config)` for one-step synthesis, you can connect beforehand to further decrease latency.
```
synthesizer = Synthesis(**config).connect()
#- prepare other resources -#
synthesizer.stream(text_iterator)
```
For more details, see the note of [synthesis.py](nopause/sdk/synthesis.py#L176) 

### `Class Voice`

The `Voice` class enables you to add or remove custom voices, as well as list all existing voices.

#### `Voice.add()`

This API can be utilized to replicate a new voice using multiple references.

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

- `voice_id`: The server generated voice ID for the target voice.
- `voice_name`: The name of target voice.
- `trace_id`: An ID used to track the current request. It can help locate reported issues.


#### `Voice.get_voices()`

This API is used to list available voices page by page.

##### Arguments

- `page`: The index of page to view. (1-based, default: `1`)
- `page_size`: The size of one page. (default: `100`)
- `api_key`: The API key of NoPause. (default: `None`).
- `api_base`: The base URL for the NoPause API (default: `None`).
- `api_version`: The version of the NoPause API to use (default: `None`).

##### Returns

`VoicesResponse`

- `voices`: A list of a series voice which contains the `voice_name: str`, `voice_id: str`, `voice_type: str`, `description: str` and `audios: list[audio_filename]`
- `total`: Total number of available voices, including prebuilt voices and custome built voices.
- `trace_id`: An ID used to track the current request. It can help locate reported issues.


#### `Voice.delete()`

This API could be used to delete a custom voice by voice ID.

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

