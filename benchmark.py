import asyncio
import time
import httpx

async def make_request(client, text, idx):
    try:
        start = time.time()
        resp = await client.post("http://127.0.0.1:8000/format", data={"text": text, "filename": f"test_{idx}"})
        elapsed = time.time() - start
        return resp.status_code, elapsed
    except Exception as e:
        return str(e), 0

async def main():
    text = "Benchmark test\n\n" * 50
    # Warm up
    async with httpx.AsyncClient() as client:
        await make_request(client, text, 0)

    start_time = time.time()
    num_requests = 10

    async with httpx.AsyncClient() as client:
        tasks = [make_request(client, text, i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    print(f"Total time for {num_requests} concurrent requests: {total_time:.2f}s")
    for idx, (status, elapsed) in enumerate(results):
        print(f"Request {idx}: status={status}, time={elapsed:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
