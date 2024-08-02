import asyncio
import subprocess
import psutil
import yaml
import logging
from simulated_blockchain import SimulatedBlockchain
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


class CommandCenter:
    def __init__(self):
        self.event_queue = EventQueue()
        self.blockchain = SimulatedBlockchain()
        self.scanner = SimulatedScanner(self.event_queue)
        self.discord_bot = SimulatedDiscordBot(self.event_queue)
        self.config = self.load_config()
        self.setup_logging()
        self.tasks = []

    def load_config(self):
        with open("config.yaml", "r") as file:
            return yaml.safe_load(file)

    def setup_logging(self):
        logging.basicConfig(
            filename="command_center.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    async def start_all(self):
        self.tasks.extend(
            [
                asyncio.create_task(self.scanner.scan()),
                asyncio.create_task(
                    self.discord_bot.start(self.config["discord_token"])
                ),
            ]
        )
        logging.info("All components started")

    async def stop_all(self):
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        await self.discord_bot.close()
        logging.info("All components stopped")

    def check_status(self):
        return {
            "blockchain": "Running",
            "scanner": "Running"
            if any(isinstance(t, asyncio.Task) and not t.done() for t in self.tasks)
            else "Stopped",
            "discord_bot": "Running" if self.discord_bot.is_ready() else "Stopped",
        }

    def update_config(self, key, value):
        self.config[key] = value
        with open("config.yaml", "w") as file:
            yaml.dump(self.config, file)
        logging.info(f"Updated config: {key} = {value}")

    async def run(self):
        print("Welcome to the Command Center!")
        print("Available commands: start, stop, status, config, exit")

        while True:
            command = input("Enter command: ").strip().lower()

            if command == "start":
                await self.start_all()
                print("All components started")

            elif command == "stop":
                await self.stop_all()
                print("All components stopped")

            elif command == "status":
                status = self.check_status()
                for component, state in status.items():
                    print(f"{component}: {state}")

            elif command.startswith("config"):
                parts = command.split()
                if len(parts) == 3:
                    _, key, value = parts
                    self.update_config(key, value)
                    print(f"Updated config: {key} = {value}")
                else:
                    print("Invalid config command. Use: config <key> <value>")

            elif command == "exit":
                await self.stop_all()
                break

            else:
                print("Unknown command")


async def main():
    command_center = CommandCenter()
    await command_center.run()


if __name__ == "__main__":
    asyncio.run(main())
