import sys


class Buffer:
    def __init__(self, size):
        self.size = size
        self.queue = []
        self.data = [None for _ in range(size)]
        self.pointer = 0
        self.min = sys.maxsize
        self.max = -1
        self.packages = 0
        self.accepted = 0
        self.dropped = 0

    def reset(self):
        self.queue = []
        self.data = [None for _ in range(self.size)]
        self.pointer = 0
        self.min = sys.maxsize
        self.max = -1
        self.packages = 0
        self.accepted = 0
        self.dropped = 0

    def select_min(self):
        r = []
        for i in range(self.size):
            if self.data[i]:
                if self.data[i][1]:
                    if self.data[i][0][0].id == self.min:
                        r += [True]
                    else:
                        r += [False]
                else:
                    r += [False]
            else:
                r += [False]
        return r

    def select_max(self):
        r = []
        for i in range(self.size):
            if self.data[i]:
                if self.data[i][1]:
                    if self.data[i][0][0].id == self.max:
                        r += [True]
                    else:
                        r += [False]
                else:
                    r += [False]
            else:
                r += [False]
        return r

    def add(self, package):
        self.packages += 1
        self.accepted += 1

        def insert(index):
            self.data[index] = [package, True]
            self.update_minmax()

        for i in range(self.size):
            if not self.data[i]:
                insert(i)
                return True, package[0].id

        end = self.pointer
        is_min = self.select_min()
        self.dropped += 1
        while True:
            if is_min[self.pointer]:
                id = self.data[self.pointer][0][0].id
                dt = package[1] - self.data[self.pointer][0][1]
                self.data[self.pointer][0][0].add_buffer_time(dt)
                self.data[self.pointer][0][0].add_system_time(dt)
                self.data[self.pointer][0][0].dropped += 1

                insert(self.pointer)
                return False, id

            self.pointer += 1
            if self.pointer == self.size:
                self.pointer = 0

            if self.pointer == end:
                package[0].dropped += 1
                self.accepted -= 1
                return False, -1

    def pick(self, t):
        def pick_queue():
            i = self.queue[0]
            self.queue = self.queue[1:]

            r = self.data[i][0]
            self.data[i] = None
            self.update_minmax()

            r[0].add_buffer_time(t - r[1])
            return r

        if self.queue:
            return pick_queue()

        is_max = self.select_max()
        for i in range(self.size):
            if is_max[i]:
                self.queue += [i]
                self.data[i][1] = False

        if not self.queue:
            return None

        return pick_queue()

    def update_minmax(self):
        self.min = sys.maxsize
        self.max = -1

        for i in range(self.size):
            if self.data[i]:
                self.min = min(self.min, self.data[i][0][0].id)
                self.max = max(self.min, self.data[i][0][0].id)
