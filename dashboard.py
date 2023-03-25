import time
import tkinter as tk
from tkinter import ttk

import numpy as np
import seaborn as sns
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from ttkthemes import ThemedTk

sns.set_theme(palette="viridis")

rng1 = np.random.default_rng()
rng2 = np.random.default_rng()

fig1 = Figure(figsize=(5, 5), dpi=96)
ax1 = fig1.add_subplot(111, xlim=(-11, 11), ylim=(-1, 21))
ax1.set_title("Plot Positions")
ax1.set_xlabel("X-Axis")
ax1.set_ylabel("Y-Axis")
(obj1,) = ax1.plot([], [], "o", lw=3)

fig2 = Figure(figsize=(5, 5), dpi=96)
ax2 = fig2.add_subplot(111, xlim=(-11, 11), ylim=(-1, 21))
ax2.set_title("Plot Positions")
ax2.set_xlabel("X-Axis")
ax2.set_ylabel("Y-Axis")
(obj2,) = ax2.plot([], [], "o", lw=3)


def init1():
    obj1.set_data([], [])
    return (obj1,)


def animate1(i):
    if not paused:
        n_obj = rng1.integers(21)
        x = rng1.uniform(-10, 10, n_obj)
        y = rng1.uniform(0, 20, n_obj)
        obj1.set_data(x, y)
    return (obj1,)


def init2():
    obj2.set_data([], [])
    return (obj2,)


def animate2(i):
    if not paused:
        n_obj = rng2.integers(21)
        x = rng2.uniform(-10, 10, n_obj)
        y = rng2.uniform(0, 20, n_obj)
        obj2.set_data(x, y)
    return (obj2,)


class ConfigureFrame(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)

        self.columnconfigure(0, weight=1)

        setup = ttk.LabelFrame(self, text="Setup Details")
        setup.grid(column=0, row=0, padx=10, pady=10, sticky=tk.NSEW)

        scene = ttk.LabelFrame(self, text="Scene selection")
        scene.grid(column=0, row=1, padx=10, pady=10, sticky=tk.NSEW)

        plot = ttk.LabelFrame(self, text="Plot selection")
        plot.grid(column=0, row=2, padx=10, pady=10, sticky=tk.NSEW)

        send_btn = ttk.Button(
            self, text="SEND CONFIG TO MMWAVE DEVICE", command=self.send_config
        )
        send_btn.grid(column=0, row=4, padx=10, pady=10, sticky=tk.E)

        setup.columnconfigure(0, weight=1)
        setup.columnconfigure(1, weight=2)

        ttk.Label(setup, text="Platform").grid(row=0, column=0, sticky=tk.W)
        self._platform = tk.StringVar(value="xWR16xx")
        ttk.Combobox(
            setup,
            textvariable=self._platform,
            values=("xWR14xx", "xWR16xx"),
            state="readonly",
        ).grid(row=0, column=1, sticky=tk.EW)

        ttk.Label(setup, text="SDK Version").grid(row=1, column=0, sticky=tk.W)
        self._sdk_version = tk.DoubleVar(value=2.1)
        ttk.Combobox(
            setup,
            textvariable=self._sdk_version,
            values=(1.2, 2.0, 2.1),
            state="readonly",
        ).grid(row=1, column=1, sticky=tk.EW)

        ttk.Label(setup, text="Antenna Config (Azimuth Res-deg)").grid(
            row=2, column=0, sticky=tk.W
        )
        self._antenna_conf = tk.StringVar(value="4Rx,2Tx(15 deg)")
        ttk.Combobox(
            setup,
            textvariable=self._antenna_conf,
            values=(
                "4Rx,3Tx(15 deg + Elevation)",
                "4Rx,2Tx(15 deg)",
                "4Rx,1Tx(30 deg)",
                "2Rx,1Tx(60 deg)",
                "1Rx,1Tx(None)",
            ),
            state="readonly",
        ).grid(row=2, column=1, sticky=tk.EW)

        ttk.Label(setup, text="Desirable Configuration").grid(
            row=3, column=0, sticky=tk.W
        )
        self._subprofile_type = tk.StringVar(value="Best Range Resolution")
        ttk.Combobox(
            setup,
            textvariable=self._subprofile_type,
            values=("Best Range Resolution", "Best Velocity Resolution", "Best Range"),
            state="readonly",
        ).grid(row=3, column=1, sticky=tk.EW)

        ttk.Label(setup, text="Frequency Band (GHz)").grid(row=4, column=0, sticky=tk.W)
        self._freq_band = tk.StringVar(value="77-81")
        ttk.Combobox(
            setup,
            textvariable=self._freq_band,
            values=("76-77", "77-81"),
            state="readonly",
        ).grid(row=4, column=1, sticky=tk.EW)

        for widget in setup.winfo_children():
            widget.grid(padx=5, pady=5)

        scene.columnconfigure(0, weight=1)
        scene.columnconfigure(1, weight=2)
        scene.columnconfigure(2, weight=1)

        ttk.Label(scene, text="Frame Rate (fps)").grid(row=0, column=0, sticky=tk.W)
        self._frame_rate = tk.IntVar(value=10)
        _cur_fps_val = ttk.Label(scene, text=f"{self._frame_rate.get():02}")
        _cur_fps_val.grid(row=0, column=2)
        ttk.Scale(
            scene,
            from_=1,
            to=30,
            variable=self._frame_rate,
            command=lambda _: _cur_fps_val.configure(text=f"{self._frame_rate.get():02}"),
        ).grid(row=0, column=1, sticky=tk.EW)

        ttk.Label(scene, text="Range resolution (m)").grid(row=1, column=0, sticky=tk.W)
        self._range_res = tk.DoubleVar(value=0.044)
        _cur_range_res = ttk.Label(scene, text=f"{self._range_res.get():.3f}")
        _cur_range_res.grid(row=1, column=2)
        ttk.Scale(
            scene,
            from_=0.039,
            to=0.047,
            variable=self._range_res,
            command=lambda _: _cur_range_res.configure(
                text=f"{self._range_res.get():.3f}"
            ),
        ).grid(row=1, column=1, sticky=tk.EW)

        ttk.Label(scene, text="Maximum Unambiguous Range (m)").grid(
            row=2, column=0, sticky=tk.W
        )
        self._max_range = tk.DoubleVar(value=9.02)
        _cur_max_range = ttk.Label(scene, text=f"{self._max_range.get():.2f}")
        _cur_max_range.grid(row=2, column=2)
        ttk.Scale(
            scene,
            from_=3.95,
            to=10.8,
            variable=self._max_range,
            command=lambda _: _cur_max_range.configure(
                text=f"{self._max_range.get():.2f}"
            ),
        ).grid(row=2, column=1, sticky=tk.EW)

        ttk.Label(scene, text="Maximum Radial Velocity (m/s)").grid(
            row=3, column=0, sticky=tk.W
        )
        self._max_rad_vel = tk.DoubleVar(value=1)
        _cur_max_rad_vel = ttk.Label(scene, text=f"{self._max_rad_vel.get():.2f}")
        _cur_max_rad_vel.grid(row=3, column=2)
        ttk.Scale(
            scene,
            from_=0.32,
            to=7.59,
            variable=self._max_rad_vel,
            command=lambda _: _cur_max_rad_vel.configure(
                text=f"{self._max_rad_vel.get():.2f}"
            ),
        ).grid(row=3, column=1, sticky=tk.EW)

        ttk.Label(scene, text="Radial Velocity Resolution (m/s)").grid(
            row=4, column=0, sticky=tk.W
        )
        self._rad_vel_res = tk.DoubleVar(value=0.13)
        _sel_rad_vel = ttk.Label(scene, text=self._rad_vel_res.get())
        _sel_rad_vel.grid(row=4, column=2)
        _rad_vel_cb = ttk.Combobox(
            scene,
            textvariable=self._rad_vel_res,
            values=(0.07, 0.13),
            state="readonly",
        )
        _rad_vel_cb.bind(
            "<<ComboboxSelected>>",
            lambda _: _sel_rad_vel.configure(text=self._rad_vel_res.get()),
        )
        _rad_vel_cb.grid(row=4, column=1, sticky=tk.EW)

        for widget in scene.winfo_children():
            widget.grid(padx=5, pady=5)

        # Start of the Plot Selection Section
        plot.columnconfigure(0, weight=1)
        plot.columnconfigure(1, weight=1)

        self._scatter_plot = tk.BooleanVar(value=True)
        ttk.Checkbutton(plot, text="Scatter Plot", variable=self._scatter_plot).grid(
            row=0, column=0, sticky=tk.W
        )
        self._range_profile = tk.BooleanVar(value=True)
        ttk.Checkbutton(plot, text="Range Profile", variable=self._range_profile).grid(
            row=1, column=0, sticky=tk.W
        )
        self._noise_profile = tk.BooleanVar()
        ttk.Checkbutton(plot, text="Noise Profile", variable=self._noise_profile).grid(
            row=2, column=0, sticky=tk.W
        )
        self._range_azimuth_heat_map = tk.BooleanVar()
        ttk.Checkbutton(
            plot, text="Range Azimuth Heat Map", variable=self._range_azimuth_heat_map
        ).grid(row=0, column=1, sticky=tk.W)
        self._range_doppler_heat_map = tk.BooleanVar()
        ttk.Checkbutton(
            plot, text="Range Doppler Heat Map", variable=self._range_doppler_heat_map
        ).grid(row=1, column=1, sticky=tk.W)
        self._statistics = tk.BooleanVar(value=True)
        ttk.Checkbutton(plot, text="Statistics", variable=self._statistics).grid(
            row=2, column=1, sticky=tk.W
        )

        for widget in plot.winfo_children():
            widget.grid(padx=5, pady=5)

    def send_config(*args, **kwargs):
        global paused
        paused = True
        # send config to device, not implemented
        # set axes range here
        # time.sleep(2)  # this is to simulate awaiting for response, not needed otherwise
        paused = False


class PlotFrame(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        canvas1 = FigureCanvasTkAgg(fig1, self)
        canvas1.draw()
        toolbar1 = NavigationToolbar2Tk(canvas1, self, pack_toolbar=False)
        toolbar1.update()

        toolbar1.grid(row=1, column=0, sticky=tk.EW)
        canvas1.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)

        canvas2 = FigureCanvasTkAgg(fig2, self)
        canvas2.draw()
        toolbar2 = NavigationToolbar2Tk(canvas2, self, pack_toolbar=False)
        toolbar2.update()

        toolbar2.grid(row=1, column=1, sticky=tk.EW)
        canvas2.get_tk_widget().grid(row=0, column=1, sticky=tk.NSEW)


class App(ThemedTk):
    def __init__(self):
        super().__init__()

        self.title("mmWave Visualizer")
        self.geometry("900x700")
        self.resizable(False, False)
        self.set_theme("arc")

        style = ttk.Style()
        style.configure(
            "TNotebook.Tab", font=("Noto Sans Mono", 15, "bold"), padding=[10, 10]
        )
        style.configure("TLabelframe.Label", font=("Noto Sans Mono", 12, "bold"))

        notebook = ttk.Notebook(self, width=900, height=700)
        notebook.pack(padx=5, pady=10, expand=True)

        frameconf = ConfigureFrame(notebook)
        frameplt = PlotFrame(notebook)

        frameconf.pack(fill="both", expand=True)
        frameplt.pack(fill="both", expand=True)

        notebook.add(frameconf, text="Configure")
        notebook.add(frameplt, text="Plots")


if __name__ == "__main__":
    app = App()
    paused = True
    anim1 = FuncAnimation(fig1, animate1, init_func=init1, interval=1000, blit=True)
    anim2 = FuncAnimation(fig2, animate2, init_func=init2, interval=500, blit=True)
    app.mainloop()
