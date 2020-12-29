from SMO.buffer import Buffer
from SMO.device import DeviceController, Status
from SMO.source import SourceController

import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import colorsys
import random
from datetime import datetime


def hsv2rgb2hex(h, s, v):
    r, g, b = tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h / 360, s / 100, v / 100))
    return '#%02x%02x%02x' % (int(r), int(g), int(b))


class System:
    def __init__(self, ss, bs, ds):
        self.sc = SourceController(ss)
        self.b = Buffer(bs)
        self.dc = DeviceController(ds)
        self.seed = datetime.now()
        random.seed(self.seed)
        self.timings = {
            self.sc: (self.sc.sources[0], 0.0),
            self.dc: (self.dc.devices[0], 0.0)
        }
        self.t = 0
        self.limit = 0
        self.running = False
        self.backlog = []
        self.backlog_bounds = None

    def reset(self, limit):
        self.limit = limit
        self.running = True

        self.t = 0
        self.backlog = []
        self.backlog_bounds = None
        random.seed(self.seed)

        self.sc.reset()
        self.b.reset()
        self.dc.reset()

        self.timings = {
            self.sc: (self.sc.sources[0], 0.0),
            self.dc: (self.dc.devices[0], 0.0)
        }

    def save(self, caller, event):
        self.backlog += [(caller, self.t, event)]

    def print(self):
        with open('out.txt', 'w') as file:
            for log in self.backlog:
                file.write("%s | %.4f | %s\n" % log)

    def graph_device(self, x, start=0, end=None):
        if end is None:
            end = self.backlog[-1][1]

        devices = [[] for _ in range(len(self.dc.devices))]
        status = [False for _ in range(len(self.dc.devices))]

        bound = 0
        if not self.backlog_bounds:
            if len(self.backlog) > 0:
                self.backlog_bounds = [0, len(self.backlog)]
            else:
                return

        i = self.backlog_bounds[0]
        while i < self.backlog_bounds[1]:
            if (self.backlog[i][1] < start - 5) or (self.backlog[i][1] > end):
                if self.backlog[i][1] < max(0, start - 5):
                    bound = i
                i += 1
                continue
            self.backlog_bounds = [bound, len(self.backlog)]

            if self.backlog[i][0][0] == 'D':
                num = int(self.backlog[i][2][0])
                src = int(self.backlog[i][0][1:])
                if (self.backlog[i][2][1] == "Busy.") and not status[num]:
                    devices[num] += [[self.backlog[i][1], self.t, src]]
                    status[num] = True
                if self.backlog[i][2][1] == "Ready." and status[num]:
                    devices[num][-1][1] = self.backlog[i][1]
                    status[num] = False

            i += 1

        cats = range(1, len(self.dc.devices) + 1)
        colors = [[], []]
        colors[0] = [hsv2rgb2hex(i * 360 / len(self.sc.sources), 70, 75) for i in range(len(self.sc.sources))]
        colors[1] = [hsv2rgb2hex(i * 360 / len(self.sc.sources), 70, 65) for i in range(len(self.sc.sources))]
        colormap = []
        ci = [False for _ in cats]
        verts = []

        for i in range(len(devices)):
            for d in devices[i]:
                v = [
                    (d[0], cats[i] - .4),
                    (d[0], cats[i] + .4),
                    (d[1], cats[i] + .4),
                    (d[1], cats[i] - .4),
                    (d[0], cats[i] - .4),
                ]
                verts += [v]
                colormap += [colors[ci[i]][d[2]]]
                ci[i] = not ci[i]

        bars = PolyCollection(verts, facecolors=colormap)
        x.add_collection(bars)

        x.set_title("Активность устройств")
        x.set_yticks([i + 1 for i in range(len(self.dc.devices))])
        x.set_yticklabels([i + 1 for i in range(len(self.dc.devices))])
        x.set_ylim(0.5, len(self.dc.devices) + 0.5)
        x.set_xlim(start, end)

        return colors[0]

    def graph_buffer(self, x, start=0, end=None):
        if end is None:
            end = self.backlog[-1][1]

        accepted = ([], [])
        changed = ([], [])
        dropped = ([], [])
        process_start = ([], [])
        process_end = ([], [])

        bound = 0
        if not self.backlog_bounds:
            if len(self.backlog) > 0:
                self.backlog_bounds = [0, len(self.backlog)]
            else:
                return

        i = self.backlog_bounds[0]
        while i < self.backlog_bounds[1]:
            if (self.backlog[i][1] < start - 5) or (self.backlog[i][1] > end):
                if self.backlog[i][1] < max(0, start - 5):
                    bound = i
                i += 1
                continue
            self.backlog_bounds = [bound, len(self.backlog)]

            num = int(self.backlog[i][0][1:]) + 1
            if self.backlog[i][0][0] == 'B':
                if self.backlog[i][2] == "Placed package.":
                    accepted[0].append(self.backlog[i][1])
                    accepted[1].append([num])
                if self.backlog[i][2] == "Changed package.":
                    changed[0].append(self.backlog[i][1])
                    changed[1].append([num])
                if self.backlog[i][2] == "Dropped package.":
                    dropped[0].append(self.backlog[i][1])
                    dropped[1].append([num])
            if self.backlog[i][0][0] == 'D':
                if self.backlog[i][2][1] == "Busy.":
                    process_start[0].append(self.backlog[i][1])
                    process_start[1].append([num])
                if self.backlog[i][2][1] == "Ready.":
                    process_end[0].append(self.backlog[i][1])
                    process_end[1].append([num])

            i += 1

        x.scatter(*process_end, color='b', marker='v')
        x.scatter(*process_start, color='b', marker='>')
        x.scatter(*accepted, color='g', marker='o')
        x.scatter(*dropped, color='r', marker='x')
        x.scatter(*changed, color='y', marker='.')

        x.set_title("События источников")
        x.set_yticks([i + 1 for i in range(len(self.sc.sources))])
        x.set_yticklabels([i + 1 for i in range(len(self.sc.sources))])
        x.set_ylim(0.5, len(self.sc.sources) + 0.5)
        x.set_xlim(start, end)

    def graph_queue(self, x, start=0, end=None):
        if end is None:
            end = self.backlog[-1][1]

        a = ([], [])

        bound = 0
        if not self.backlog_bounds:
            if len(self.backlog) > 0:
                self.backlog_bounds = [0, len(self.backlog)]
            else:
                return

        i = self.backlog_bounds[0]
        while i < self.backlog_bounds[1]:
            if (self.backlog[i][1] < start - 5) or (self.backlog[i][1] > end):
                if self.backlog[i][1] < max(0, start - 5):
                    bound = i
                i += 1
                continue
            self.backlog_bounds = [bound, len(self.backlog)]

            if self.backlog[i][0][0] == "Q":
                a[0].append(self.backlog[i][1])
                a[1].append(self.backlog[i][2])

            i += 1

        x.plot(*a)

        x.set_title("Размер очереди по времени")
        x.set_yticks([i + 1 for i in range(self.b.size)])
        x.set_yticklabels([i + 1 for i in range(self.b.size)])
        x.set_xlim(start, end)
        x.set_ylim(0, self.b.size)

    def matplotlib(self):
        fig = plt.figure()
        fig.clf()
        x = fig.add_subplot(111)
        self.graph_device(x)
        fig.show()
        self.graph_buffer(x)
        fig.show()

    def source_before_device(self):
        return (not self.timings[self.dc][0]) or (self.timings[self.sc][1] < self.timings[self.dc][1])

    def push_to_device(self, device):
        package = self.b.pick(self.t)
        self.save("Q0", len(self.b.queue))
        device.t = self.t
        if package:
            device.process(package)
            self.timings[self.dc] = next(self.dc)
            self.save("D%s" % package[0].id, [device.id, "Busy."])
        else:
            device.status = Status.HALT
            self.timings[self.dc] = next(self.dc)

    def tick(self):
        if (self.sc.count() == self.limit) and not self.dc.list_working():
            self.running = False

        if not self.running:
            return

        if self.source_before_device() and self.sc.count() < self.limit:
            s, self.t = self.timings[self.sc]
            self.save("S%s" % s.id, "Generating.")

            drop, i = self.b.add(self.timings[self.sc])
            if drop:
                self.save("B%s" % s.id, "Placed package.")
            else:
                if i == -1:
                    self.save("B%s" % s.id, "Dropped package.")
                else:
                    self.save("B%s" % i, "Dropped package.")
                    self.save("B%s" % s.id, "Changed package.")
            device = self.dc.select_free_device()
            if device:
                self.push_to_device(device)
            self.timings[self.sc] = next(self.sc)
        else:
            device, nt = self.timings[self.dc]
            if nt > self.t:
                self.t = nt
            else:
                device.t = self.t
            if device.status == Status.BUSY:
                package = device.package
                device.end()
                self.save("D%s" % package[0].id, [device.id, "Ready."])
            self.push_to_device(device)

    def acceptance_rate(self):
        return self.b.accepted / self.b.packages

    def drop_rate(self):
        return self.b.dropped / self.b.packages if self.b.packages > 0 else 0

    def processing_rate(self):
        return self.dc.processed() / self.b.packages
