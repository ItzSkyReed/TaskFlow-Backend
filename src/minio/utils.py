class S3Stream:
    def __init__(self, stream, chunk_size=8192):
        self.stream = stream
        self.chunk_size = chunk_size

    async def __aiter__(self):
        while True:
            chunk = await self.stream.read(self.chunk_size)
            if not chunk:
                break
            yield chunk
        await self.stream.close()
