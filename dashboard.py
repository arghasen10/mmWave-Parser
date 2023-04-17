import time
import tkinter as tk
from threading import Event, Thread
from tkinter import ttk

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from msgspec import Struct
from msgspec.json import decode
from ttkthemes import ThemedTk


class Schema(Struct):
    x_coord: list[float]
    y_coord: list[float]
    rp_y: list[float]
    noiserp_y: list[float]
    doppz: list[list[int]]


data = Schema([], [], [], [], [[]])


def read_json(pause):
    global data
    with open("dataset/CCW_A_1.json", "rb") as f:
        while not pause.is_set():
            line = f.readline()
            if not line:
                break
            data = decode(line, type=Schema)
            time.sleep(0.4)


# Graph for position
fig_pos, ax_pos = plt.subplots(figsize=(5, 5))
ax_pos.set_xlim([-11, 11])
ax_pos.set_ylim([-1, 21])
ax_pos.set_title("Position")
ax_pos.set_xlabel("X-Axis")
ax_pos.set_ylabel("Y-Axis")
(obj_pos,) = ax_pos.plot([], [], "o", lw=3)


def animate_pos(_):
    if not pause.is_set():
        obj_pos.set_data(data.x_coord, data.y_coord)
    return (obj_pos,)


# Graph for doppler
fig_dop, ax_dop = plt.subplots(figsize=(8, 6))

im = ax_dop.imshow(data.doppz, aspect="auto", interpolation="gaussian", animated=True)
ax_dop.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)


def animate_dop(_):
    if not pause.is_set:
        im.set_array(data.doppz)
    return (im,)


# Graph for noise profile
fig_noise, ax_noise = plt.subplots(figsize=(8, 6))
ax_noise.set_xlim([1, 256])
ax_noise.set_ylim([0, 150])
ax_noise.set_title("Noise")
ax_noise.set_xlabel("X-Axis")
ax_noise.set_ylabel("dB")
(obj_rp,) = ax_noise.plot([], [])
(obj_noiserp,) = ax_noise.plot([], [])
ax_noise.legend([obj_rp, obj_noiserp], ["rp_y", "noiserp_y"])

x_axis = np.arange(256) + 1


def animate_noise(_):
    if not pause.is_set:
        obj_rp.set_data(x_axis, data.rp_y)
        obj_noiserp.set_data(x_axis, data.noiserp_y)
    return (obj_rp, obj_noiserp)


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
            command=lambda _: _cur_fps_val.configure(
                text=f"{self._frame_rate.get():02}"
            ),
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
        global pause, anim_pos, anim_dop, anim_noise
        pause.set()
        # send config to device, not implemented
        # set axes range here
        # time.sleep(2)  # this is to simulate awaiting for response, not needed otherwise
        pause.clear()


class PlotFrame(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        canvas_pos = FigureCanvasTkAgg(fig_pos, self)
        canvas_pos.draw()
        toolbar_pos = NavigationToolbar2Tk(canvas_pos, self, pack_toolbar=False)
        toolbar_pos.update()

        toolbar_pos.grid(row=1, column=0, sticky=tk.EW)
        canvas_pos.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)

        canvas_dop = FigureCanvasTkAgg(fig_noise, self)
        canvas_dop.draw()
        toolbar_dop = NavigationToolbar2Tk(canvas_dop, self, pack_toolbar=False)
        toolbar_dop.update()

        toolbar_dop.grid(row=1, column=1, sticky=tk.EW)
        canvas_dop.get_tk_widget().grid(row=0, column=1, sticky=tk.NSEW)


class App(ThemedTk):
    def __init__(self):
        super().__init__()

        self.title("mmWave Visualizer")
        # self.wm_iconphoto(False, tk.PhotoImage(file="assets/ubinetlogo.png"))
        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()
        self.geometry(f"{width}x{height}")
        self.set_theme("arc")

        style = ttk.Style()
        style.configure(
            "TNotebook.Tab", font=("Noto Sans Mono", 15, "bold"), padding=[10, 10]
        )
        style.configure("TLabelframe.Label", font=("Noto Sans Mono", 12, "bold"))

        notebook = ttk.Notebook(self, width=width, height=height)
        notebook.pack(padx=5, pady=10, expand=True)

        frameconf = ConfigureFrame(notebook)
        frameplt = PlotFrame(notebook)

        frameconf.pack(fill="both", expand=True)
        frameplt.pack(fill="both", expand=True)

        notebook.add(frameconf, text="Configure")
        notebook.add(frameplt, text="Plots")


if __name__ == "__main__":
    app = App()
    pause = Event()
    pause.set()
    th = Thread(
        target=read_json, args=(pause,), daemon=True, name="Json Schema Reading Daemon"
    )
    th.start()
    anim_pos = FuncAnimation(
        fig_pos, animate_pos, interval=400, blit=True, cache_frame_data=False
    )
    anim_dop = FuncAnimation(
        fig_dop, animate_dop, interval=400, blit=True, cache_frame_data=False
    )
    anim_noise = FuncAnimation(
        fig_noise, animate_noise, interval=400, blit=True, cache_frame_data=False
    )
    app.mainloop()
