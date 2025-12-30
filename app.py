import asyncio

from gemini_flow import Gemini


async def main() -> None:
    ai = Gemini(model="gemini-3-pro-2")

    # stream = await ai.astream_chat("描述照片中的內容。", images=["./input/大為.png"])
    stream = await ai.astream_chat("講一個故事")
    async for chunk in stream:
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())