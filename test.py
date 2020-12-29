import tkinter as tk
import tkinter.ttk
import numpy as np
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from SMO.system import System


class SMO(tk.Tk):
    title = "SMO 2.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        super().wm_title(self.title)
        super().geometry('900x900')
        super().resizable(width=False, height=False)

        self.container = tk.Frame(self)
        self.container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frame = None
        self.create_frame()

    def create_frame(self):
        self.frame = SMOMainFrame(self.container, self)
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.tkraise()


class SMOMainFrame(tk.Frame):
    graph_t = 0.0
    graph_w = 10
    graph_step = 2
    graph_fps = 60

    loop_active = False
    loop_paused = True

    graph_page = 0
    graph_drawer = None

    system_sources = 5
    system_buffer = 10
    system_devices = 56
    system_limit = 0

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.system = None

        self.shooting = ([None, 100], [None, None])
        self.shooting_perc = 0

        # MATPLOTLIB CONTROLS
        frame = tk.Frame(self)
        frame.pack(side=tk.TOP, fill=tk.Y)

        self.btn_start = tk.Button(self, text='Старт', width=10, command=self.btn_start_action)
        self.btn_start.pack(in_=frame, side=tk.LEFT, padx=10, pady=10)

        self.btn_pause = tk.Button(self, text='Пауза', width=10, command=self.btn_pause_action, state=tk.DISABLED)
        self.btn_pause.pack(in_=frame, side=tk.LEFT, padx=10, pady=10)

        self.btn_step = tk.Button(self, text='Шаг', width=10, command=self.btn_step_action)
        self.btn_step.pack(in_=frame, side=tk.LEFT, padx=10, pady=10)

        self.btn_reset = tk.Button(self, text='Сброс', width=10, command=self.btn_reset_action)
        self.btn_reset.pack(in_=frame, side=tk.LEFT, padx=(10, 30), pady=10)

        self.btn_devices = tk.Button(
            self, text='Устройства', width=15, command=lambda: self.change_page(0), state=tk.DISABLED
        )
        self.btn_devices.pack(in_=frame, side=tk.LEFT, padx=10, pady=10)

        self.btn_sources = tk.Button(
            self, text='Источники', width=15, command=lambda: self.change_page(1), state=tk.DISABLED
        )
        self.btn_sources.pack(in_=frame, side=tk.LEFT, padx=10, pady=10)

        self.btn_queue = tk.Button(
            self, text='Очередь', width=15, command=lambda: self.change_page(2), state=tk.DISABLED
        )
        self.btn_queue.pack(in_=frame, side=tk.LEFT, padx=10, pady=10)

        # MATPLOTLIB
        self.f = Figure(figsize=(10, 5), dpi=100)
        self.f_canvas = FigureCanvasTkAgg(self.f, self)
        self.f_canvas.get_tk_widget().pack(side=tk.TOP)

        # SOURCES TREE VIEW
        frame = tk.Frame(self, height=150)
        frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
        frame.pack_propagate(False)

        self.tree_sources = tk.ttk.Treeview(self, selectmode="none")
        self.tree_sources["columns"] = (
            "Generated", "DropRate", "AvgSystem",
            "AvgBuffer", "AvgBufferDispersion",
            "AvgProcessing", "AvgProcessingDispersion"
        )
        vsb = tk.ttk.Scrollbar(self, orient="vertical", command=self.tree_sources.yview)
        vsb.pack(in_=frame, side=tk.RIGHT, fill=tk.Y)
        column_width = math.floor((900 - 60) / len(self.tree_sources["columns"]))

        self.tree_sources.column("#0", width=50, minwidth=50, stretch=tk.NO)
        self.tree_sources.heading("#0", text="ID", anchor=tk.CENTER)
        self.tree_sources.column("Generated", width=column_width, minwidth=column_width, stretch=tk.NO)
        self.tree_sources.heading("Generated", text="Пакетов", anchor=tk.CENTER)
        self.tree_sources.column("DropRate", width=column_width, minwidth=column_width, stretch=tk.NO)
        self.tree_sources.heading("DropRate", text="% отказа", anchor=tk.CENTER)
        self.tree_sources.column("AvgSystem", width=column_width, minwidth=column_width, stretch=tk.NO)
        self.tree_sources.heading("AvgSystem", text="Ср. t в системе", anchor=tk.CENTER)
        self.tree_sources.column("AvgBuffer", width=column_width, minwidth=column_width, stretch=tk.NO)
        self.tree_sources.heading("AvgBuffer", text="Ср. t в буффере", anchor=tk.CENTER)
        self.tree_sources.column("AvgBufferDispersion", width=column_width, minwidth=column_width, stretch=tk.NO)
        self.tree_sources.heading("AvgBufferDispersion", text="s^2 t в буффере", anchor=tk.CENTER)
        self.tree_sources.column("AvgProcessing", width=column_width, minwidth=column_width, stretch=tk.NO)
        self.tree_sources.heading("AvgProcessing", text="Ср. t обработки", anchor=tk.CENTER)
        self.tree_sources.column("AvgProcessingDispersion", width=column_width, minwidth=column_width, stretch=tk.NO)
        self.tree_sources.heading("AvgProcessingDispersion", text="s^2 t обработки", anchor=tk.CENTER)

        self.tree_sources.configure(yscrollcommand=vsb.set)
        self.tree_sources.pack(in_=frame, side=tk.LEFT, expand=True, fill=tk.BOTH)

        # DEVICES TREE VIEW
        frame = tk.Frame(self, height=150)
        frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
        frame.pack_propagate(False)

        self.tree_devices = tk.ttk.Treeview(self, selectmode="none")
        self.tree_devices["columns"] = (
            "Proceeded", "Pointer", "Status", "UsageRate"
        )
        vsb = tk.ttk.Scrollbar(self, orient="vertical", command=self.tree_devices.yview)
        vsb.pack(in_=frame, side=tk.RIGHT, fill=tk.Y)
        column_width = math.floor((900 - 110) / (len(self.tree_devices["columns"]) - 1))

        self.tree_devices.column("#0", width=50, minwidth=50, stretch=tk.NO)
        self.tree_devices.heading("#0", text="ID", anchor=tk.CENTER)
        self.tree_devices.column("Proceeded", width=column_width, minwidth=column_width, stretch=tk.NO)
        self.tree_devices.heading("Proceeded", text="Обработано", anchor=tk.CENTER)
        self.tree_devices.column("Pointer", width=50, minwidth=50, stretch=tk.NO)
        self.tree_devices.heading("Pointer", text="PTR", anchor=tk.CENTER)
        self.tree_devices.column("Status", width=column_width, minwidth=column_width, stretch=tk.NO)
        self.tree_devices.heading("Status", text="Статус", anchor=tk.CENTER)
        self.tree_devices.column("UsageRate", width=column_width, minwidth=column_width, stretch=tk.NO)
        self.tree_devices.heading("UsageRate", text="Коэфф. использования", anchor=tk.CENTER)

        self.tree_devices.configure(yscrollcommand=vsb.set)
        self.tree_devices.pack(in_=frame, side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.prepare_system()

    def change_page(self, i):
        self.graph_page = i

        if self.graph_page == 0:
            self.graph_drawer = self.system.graph_device
        if self.graph_page == 1:
            self.graph_drawer = self.system.graph_buffer
        if self.graph_page == 2:
            self.graph_drawer = self.system.graph_queue

        self.graph_draw(True)

    def prepare_system(self):
        self.btn_devices["state"] = tk.NORMAL
        self.btn_sources["state"] = tk.NORMAL
        self.btn_queue["state"] = tk.NORMAL

        self.graph_t = 0.0
        self.system = System(self.system_sources, self.system_buffer, self.system_devices)
        self.system.reset(100)
        self.change_page(self.graph_page)

    def reset(self):
        self.graph_t = 0.0
        self.system.reset(self.shooting[0][1])
        self.controller.wm_title("%s | Target: %s (%.2f%%)" % (
            self.controller.title,
            self.shooting[0][1],
            self.shooting_perc
        ))


    def update_tree(self):
        generated = self.system.sc.list_count()
        generated = [sum(generated)] + generated
        drop_rate = self.system.sc.list_dropped_rate()
        drop_rate = [sum(drop_rate) / self.system_sources] + drop_rate
        avg_system = self.system.sc.list_system_time()
        avg_system = [sum(avg_system) / self.system_sources] + avg_system
        avg_buffer = self.system.sc.list_buffer_time()
        avg_buffer = [sum(avg_buffer) / self.system_sources] + avg_buffer
        sig_buffer = self.system.sc.list_buffer_time_dispersion()
        sig_buffer = [sum(sig_buffer) / self.system_sources] + sig_buffer
        avg_processing = self.system.sc.list_processing_time()
        avg_processing = [sum(avg_processing) / self.system_sources] + avg_processing
        sig_processing = self.system.sc.list_processing_time_dispersion()
        sig_processing = [sum(sig_processing) / self.system_sources] + sig_processing

        self.tree_sources.delete(*self.tree_sources.get_children())
        for i in range(self.system_sources + 1):
            values = (
                generated[i],
                "%.5f%%" % (drop_rate[i] * 100),
                "%.5f" % avg_system[i],
                "%.5f" % avg_buffer[i],
                "%.5f" % sig_buffer[i],
                "%.5f" % avg_processing[i],
                "%.5f" % sig_processing[i]
            )
            self.tree_sources.insert('', 'end', 'source%s' % i, text=(i if i > 0 else "A"), values=values)

        proceeded = self.system.dc.list_proceeded()
        proceeded = [sum(proceeded)] + proceeded
        pointer = [''] + self.system.dc.list_pointer()
        status = [''] + self.system.dc.list_status()
        usage_rate = self.system.dc.list_work_rate()
        usage_rate = [sum(usage_rate) / self.system_devices] + usage_rate

        self.tree_devices.delete(*self.tree_devices.get_children())
        for i in range(self.system_devices + 1):
            values = (
                proceeded[i],
                pointer[i],
                status[i],
                "%.5f%%" % (usage_rate[i] * 100)
            )
            self.tree_devices.insert('', 'end', 'device%s' % i, text=(i if i > 0 else "A"), values=values)

    def btn_start_action(self):
        self.btn_start["state"] = tk.DISABLED
        self.btn_pause["state"] = tk.NORMAL
        self.btn_step["state"] = tk.DISABLED
        self.btn_reset["state"] = tk.DISABLED
        self.loop_active = True
        self.loop_paused = False
        self.loops_kickstart()

    def btn_pause_action(self):
        self.loop_paused = not self.loop_paused
        self.btn_step["state"] = tk.NORMAL if self.loop_paused else tk.DISABLED
        self.btn_reset["state"] = tk.NORMAL if self.loop_paused else tk.DISABLED
        if not self.loop_paused:
            self.loops_kickstart()

    def btn_step_action(self):
        self.system_tick()
        self.graph_t = self.system.t
        self.graph_draw()

    def btn_reset_action(self):
        self.controller.create_frame()
        self.pack_forget()

    def loops_kickstart(self):
        self.after(0, self.system_loop)
        self.after(0, self.graph_draw)

    def system_tick(self):
        self.system.tick()
        self.update_tree()

    def system_loop(self):
        if not self.loop_active:
            return

        while self.system.running:
            self.system_tick()
            if self.system.t < (self.graph_t + self.graph_step):
                continue
            self.graph_t += self.graph_step
            break

        self.loop_active = self.system.running
        if not self.loop_active:
            self.shooting[1][1] = self.system.sc.dropped_rate()
            if not self.shooting[1][0] is None:
                delta = math.fabs(self.shooting[1][1] - self.shooting[1][0])
                self.shooting_perc = delta / self.shooting[1][0] * 100 if self.shooting[1][0] > 0 else 0
                print(self.shooting_perc, self.shooting[1])
                if self.shooting_perc > 10.0:
                    self.loop_active = True
                else:
                    self.controller.wm_title("%s | Result: %s (%.2f%%)" % (
                        self.controller.title,
                        min(self.shooting[0]),
                        self.shooting_perc
                    ))
            else:
                self.loop_active = True

            self.shooting[1][0] = self.shooting[1][1]
            self.shooting[0][0] = self.shooting[0][1]
            self.shooting[0][1] = math.ceil((1.645**2 * (1 - self.shooting[1][0]))/(self.shooting[1][0] * 0.01)) if self.shooting[1][0] > 0 else 0
            if self.loop_active and self.shooting[0][1] != 0:
                self.reset()

            self.btn_pause["state"] = tk.NORMAL if self.loop_active else tk.DISABLED
            self.btn_reset["state"] = tk.DISABLED if self.loop_active else tk.NORMAL

        if self.loop_active and not self.loop_paused:
            self.after(10, self.system_loop)

    def graph_draw(self, refresh=False):
        start = max(0.0, self.graph_t - self.graph_w)
        self.f.clf()
        x = self.f.add_subplot(111)
        self.graph_drawer(x, start=start, end=(start + self.graph_w))
        self.f_canvas.draw()
        if self.loop_active and not self.loop_paused and not refresh:
            self.after(math.floor(1000 / self.graph_fps), self.graph_draw)


app = SMO()
app.mainloop()
