from enum import Enum
import random
from numpy import exp

device_status_string = (
    "Busy",
    "Ready",
    "Halt"
)


class Status(Enum):
    HALT = 2
    READY = 1
    BUSY = 0


class Device:
    def __init__(self, id):
        self.id = id
        self.c = 0
        self.t = 0.0
        self.dt = 0.0
        self.tt = 0.0
        self.eta = 0.0
        self.package = None
        self.status = Status.READY

    def reset(self):
        self.c = 0
        self.t = 0.0
        self.dt = 0.0
        self.tt = 0.0
        self.eta = 0.0
        self.package = None
        self.status = Status.READY

    def process(self, package):
        #self.dt = exp(random.random())
        self.dt = exp(random.random() * 0.25 + 1.0)
        self.eta = self.t + self.dt
        self.package = package
        self.status = Status.BUSY

    def end(self):
        self.c += 1
        self.t = self.eta
        self.tt += self.dt
        self.package[0].add_processing_time(self.dt)
        self.package[0].add_system_time(self.t - self.package[1])
        self.package = None
        self.status = Status.READY

    def usage_rate(self):
        return self.tt / self.t


class DeviceController:
    def __init__(self, size):
        self.devices = [Device(i) for i in range(size)]
        self.t = 0.0
        self.pointer = 0

    def reset(self):
        self.t = 0.0
        self.pointer = 0
        for d in self.devices:
            d.reset()

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.devices)

    def select_free_device(self):
        start = self.pointer
        while True:
            r = self.devices[self.pointer]
            if r.status != Status.BUSY:
                self.t = r.t
                return r

            self.pointer += 1
            if self.pointer == len(self.devices):
                self.pointer = 0

            if self.pointer == start:
                return None

    def min(self):
        timings = {}
        for d in self.devices:
            if d.status == Status.BUSY:
                timings[d] = d.eta
            if d.status == Status.READY:
                timings[d] = d.t
        if not timings:
            return None
        return min(timings, key=timings.get)

    def list_work_time(self):
        return [d.tt for d in self.devices]

    def list_work_rate(self):
        return [(d.tt / d.t) if (d.t > 0) else 0.0 for d in self.devices]

    def sum_work_time(self):
        return sum((d.tt for d in self.devices))

    def list_working(self):
        return [d for d in self.devices if d.status == Status.BUSY]

    def list_status(self):
        return [device_status_string[d.status.value] for d in self.devices]

    def list_proceeded(self):
        return [d.c for d in self.devices]

    def processed(self):
        return sum((d.c for d in self.devices))

    def list_pointer(self):
        return ['o' if i == self.pointer else '' for i in range(len(self.devices))]

    def __next__(self):
        m = self.min()
        if m:
            if m.status == Status.BUSY:
                r = (m, m.eta)
            else:
                r = (m, m.t)
        else:
            r = (None, self.t)
        self.t = r[1]
        return r
