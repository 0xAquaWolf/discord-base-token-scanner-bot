import asyncio
from simulated_scanner import SimulatedScanner
from simulated_discord_bot import SimulatedDiscordBot
from collections import deque


class EventQueue:
    def __init__(self):
        self.queue = deque()

    def add_event(self, event):
        self.queue.append(event)

    def get_event(self):
        return self.queue.popleft() if self.queue else None


async def main():
    event_queue = EventQueue()
    scanner = SimulatedScanner(event_queue)
    bot = SimulatedDiscordBot(event_queue)

    scanner_task = asyncio.create_task(scanner.scan())

    try:
        await bot.start("YOUR_BOT_TOKEN_HERE")
    finally:
        scanner_task.cancel()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
