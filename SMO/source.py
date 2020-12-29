import random


def iterative_dispersion(s, s2, n):
    if n < 2:
        return 0
    else:
        return (s2 - (s**2) / n)/(n - 1)


class Source:
    def __init__(self, id):
        self.id = id
        #self.dt = 0.3 + 0.5 * random.random()
        self.dt = 0.25

        self.count = 0
        self.dropped = 0
        self.t = 0.0

        self.tb = [0, 0.0, 0.0, 0.0]
        self.tp = [0, 0.0, 0.0, 0.0]
        self.ts = [0, 0.0, 0.0, 0.0]

    def __iter__(self):
        return self

    def __next__(self):
        self.count += 1
        self.t += self.dt
        return self.t

    def reset(self):
        self.count = 0
        self.dropped = 0
        self.t = 0.0

        self.tb = [0, 0.0, 0.0, 0.0]
        self.tp = [0, 0.0, 0.0, 0.0]
        self.ts = [0, 0.0, 0.0, 0.0]

    def add_buffer_time(self, x):
        self.tb[0] += 1
        self.tb[1] += (x - self.tb[1]) / self.tb[0]
        self.tb[2] += x
        self.tb[3] += x ** 2

    def buffer_time_dispersion(self):
        return iterative_dispersion(self.tb[2], self.tb[3], self.tb[0])

    def add_processing_time(self, x):
        self.tp[0] += 1
        self.tp[1] += (x - self.tp[1]) / self.tp[0]
        self.tp[2] += x
        self.tp[3] += x ** 2

    def processing_time_dispersion(self):
        return iterative_dispersion(self.tp[2], self.tp[3], self.tp[0])

    def add_system_time(self, x):
        self.ts[0] += 1
        self.ts[1] += (x - self.ts[1]) / self.ts[0]
        self.ts[2] += x
        self.ts[3] += x ** 2

    def system_time_dispersion(self):
        return iterative_dispersion(self.ts[2], self.ts[3], self.ts[0])


class SourceController:
    def __init__(self, size):
        self.sources = [Source(i) for i in range(size)]
        self.t = 0.0

    def reset(self):
        self.t = 0.0
        for s in self.sources:
            s.reset()

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.sources)

    def min(self):
        timings = {}
        for s in self.sources:
            timings[s] = s.t
        return min(timings, key=timings.get)

    def count(self):
        return sum((s.count for s in self.sources))

    def dropped(self):
        return sum((s.dropped for s in self.sources))

    def list_count(self):
        return [s.count for s in self.sources]

    def dropped_rate(self):
        return (self.dropped() / self.count()) if (self.count() > 0) else 0

    def list_dropped_rate(self):
        return [(s.dropped / s.count) if (s.count > 0) else 0 for s in self.sources]

    def list_buffer_time(self):
        return [s.tb[1] for s in self.sources]

    def list_buffer_time_dispersion(self):
        return [s.buffer_time_dispersion() for s in self.sources]

    def list_processing_time(self):
        return [s.tp[1] for s in self.sources]

    def list_processing_time_dispersion(self):
        return [s.processing_time_dispersion() for s in self.sources]

    def list_system_time(self):
        return [s.ts[1] for s in self.sources]

    def list_system_time_dispersion(self):
        return [s.system_time_dispersion() for s in self.sources]

    def __next__(self):
        m = self.min()
        next(m)
        m = self.min()
        r = (m, m.t)
        self.t = r[1]
        return r

