import asyncio
import nopause

nopause.api_key = '<nopause-api-key>'

async def text_stream():
    for char in "This is a test for cancelation":
        yield char
        await asyncio.sleep(0.01)

async def main():
    synthesis_result_generator = await nopause.Synthesis.astream(
        text_stream(),
        voice_id='Zoe',
    )

    async for audio_chunk in synthesis_result_generator:
        print(audio_chunk.chunk_id, audio_chunk.duration)
        await synthesis_result_generator.aterminate()
        break # otherwise it will raise an websockets.exceptions.ConnectionClosed because the ws client has been closed
    print('Break Done.')

if __name__ == '__main__':
    asyncio.run(main())