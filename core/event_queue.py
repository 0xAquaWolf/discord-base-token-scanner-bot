from collections import deque


class EventQueue:
    def __init__(self):
        self.queue = deque()

    def add_event(self, event):
        self.queue.append(event)

    def get_event(self):
        return self.queue.popleft() if self.queue else None
