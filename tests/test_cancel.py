import time
import nopause

nopause.api_key = '<nopause-api-key>'

def text_stream():
    for char in "This is a test for cancelation":
        yield char
        time.sleep(0.01)

def main():
    synthesis_result_generator = nopause.Synthesis.stream(
        text_stream(),
        voice_id='Zoe',
    )

    for audio_chunk in synthesis_result_generator:
        print(audio_chunk.chunk_id, audio_chunk.duration)
        synthesis_result_generator.terminate()
        break
    print('Break Done.')


if __name__ == '__main__':
    main()