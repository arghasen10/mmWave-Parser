import math


class InputTransform:
    def __init__(self, conf):
        self.conf = conf
        self.isRR = conf["subprofile_type"] == "Best Range Resolution"
        self.isVR = conf["subprofile_type"] == "Best Velocity Resolution"
        self.isBestRange = conf["subprofile_type"] == "Best Range"

        def convertSensitivityLinearTodB(linear_value, platform, Num_Virt_Ant):
            dB_value = 6 * linear_value
            dB_value = (
                dB_value / 512
                if platform == "xWR14xx"
                else dB_value / (256 * Num_Virt_Ant)
            )
            return math.ceil(dB_value)

        def convertSensitivitydBToLinear(dB_value, platform, Num_Virt_Ant):
            linear_value = (
                512 * dB_value
                if platform == "xWR14xx"
                else (256 * Num_Virt_Ant * dB_value)
            )
            return math.ceil(linear_value / 6)

        def transform_conf(self):
            platform = self.conf["platform"]
            subprofile_type = self.conf["subprofile_type"]
            self.conf = self.conf.update(
                {
                    "L3 memory size": 640,
                    "CFAR memory size": 0,
                    "CFAR window memory size": 1024,
                    "ADCBuf memory size": 32768,
                    "max_sampling_rate": 6.25,
                    "min_sampling_rate": 2,
                    "max_num_of_rx": 4,
                    "max_num_of_tx": 2,
                    "ADC bits": 16,
                    "ADC samples type": 2,
                    "Bandwidth list": [0.5, 1, 1, 5, 2, 2.5, 3, 3.5, 4],
                    "min_allowable_bandwidth": 0.5,
                    "chirp_end_guard_time": 1,
                    "chirps_per_interrupt": 1,
                    "chirp_start_time": 7,
                    "min_interchirp_dur": 7,
                    "Doppler FFT list": [16, 32, 64, 128, 256],
                    "max_slope": 100,
                    "Maximum range list": [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
                    "Gr": 8,
                    "Gt": 8,
                    "Ld": 2,
                    "Ls": 1,
                    "Lim": 2,
                    "Pt": 12,
                    "SNR_det": 12,
                }
            )
            self.conf["num_of_rx"] = int(self.conf["antenna_conf"][0])
            self.conf["num_of_tx"] = int(self.conf["antenna_conf"][4])
            self.conf["frequency_band"] = int(self.conf["freq_band"][:2])
            N_fft2d_lo = self.conf["Doppler FFT list"][0]
            adc_samples_lo = 64

            if platform == "xWR14xx":
                self.conf["L3 Memory size"] = 256
                self.conf["CFAR memory size"] = 32768
                self.conf["ADCBuf memory size"] = 16384
                self.conf["max_num_of_tx"] = 3

            self.conf["num_virt_ant"] = self.conf["num_virt_ant"] or 8
            self.conf["Range Sensitivity"] = self.conf[
                "Range Sensitivity"
            ] or convertSensitivityLinearTodB(
                1200 if platform == "xWR14xx" else 5000,
                platform,
                self.conf["num_virt_ant"],
            )

            if platform == "xWR16xx":
                self.conf["Doppler Sensitivity"] = convertSensitivityLinearTodB(
                    5000,
                    platform,
                    self.conf["num_virt_ant"],
                )
                self.conf["chirps_per_interrupt"] = 0

            self.conf["num_virt_ant"] = self.conf["num_of_rx"] * self.conf["num_of_tx"]
            match self.conf["num_virt_ant"]:
                case 12:
                    self.conf["Lncoh"] = 3
                case 8:
                    self.conf["Lncoh"] = 2.2
                case 4:
                    self.conf["Lncoh"] = 1.5
                case 2:
                    self.conf["Lncoh"] = 0.7
                case 1:
                    self.conf["Lncoh"] = 0
                case _:
                    self.conf["Lncoh"] = 6

            self.conf["NF"] = 16 if self.conf["frequency_band"] == 77 else 15
            self.conf["loss_dB"] = (
                self.conf["Pt"]
                + self.conf["Gt"]
                + self.conf["Gr"]
                - self.conf["Lncoh"]
                - self.conf["Ld"]
                - self.conf["Ls"]
                - self.conf["Lim"]
                - self.conf["SNR_det"]
                - self.conf["NF"]
            )
            self.conf["loss_linear"] = 10 ** (self.conf["loss_dB"] / 10)
            self.conf["max_allowable_bandwidth"] = (
                4 if self.conf["frequency_band"] == 77 else 1
            )

            if subprofile_type == "Best Range Resolution":
                self.conf["Bandwidth"] = self.conf["max_allowable_bandwidth"]
                self.conf["total_bw"] = self.conf["Bandwidth"] * 1000
                self.conf["min_ramp_slope"] = 20 if platform == "xWR16xx" else 35
                self.conf["ramp_slope"] = (
                    self.conf["ramp_slope"] or self.conf["min_ramp_slope"]
                )
                self.conf["num_chirps"] = self.conf["num_chirps"] or 16
                self.conf["max_slope"] = min(
                    self.conf["max_slope"],
                    math.floor(
                        (
                            self.conf["max_allowable_bandwidth"]
                            * 1000
                            * self.conf["max_sampling_rate"]
                        )
                        / (
                            adc_samples_lo
                            + self.conf["max_sampling_rate"]
                            * (
                                self.conf["chirp_start_time"]
                                + self.conf["chirp_end_guard_time"]
                            )
                        )
                    ),
                )
                self.conf["max_slope"] = math.floor(self.conf["max_slope"] / 5) * 5
                # TODO: range_resolution_constraints
            elif subprofile_type == "Best Velocity Resolution":
                self.conf["Bandwidth"] = self.conf["Bandwidth"] or 0.5
                self.conf["Num_ADC_Samples"] = (
                    self.conf["Num_ADC_Samples"] or adc_samples_lo
                )
                self.conf["Doppler FFT size"] = (
                    self.conf["Doppler FFT size"] or N_fft2d_lo
                )
            elif subprofile_type == "Best Range":
                self.conf["num_chirps"] = self.conf["num_chirps"] or 16

            self.conf["frame_duration"] = round(1000 / self.conf["frame_rate"], 3)
            self.conf["max_ramp_slope"] = max(
                5,
                min(
                    self.conf["max_slope"],
                    math.floor(
                        (self.conf["Bandwidth"] * 1000)
                        / (
                            32 / self.conf["max_sampling_rate"]
                            + self.conf["chirp_start_time"]
                            + self.conf["chirp_end_guard_time"]
                        )
                    ),
                ),
            )

            if subprofile_type == "Best Velocity Resolution":
                self.conf["radial_velocity_resolution"] = (
                    math.ceil(
                        self.conf["lightspeed"]
                        * 100
                        / (self.conf["frequency_band"] * self.conf["frame_duration"])
                    )
                    / 100
                )
                self.conf["max_radial_velocity"] = round(
                    self.conf["radial_velocity_resolution"]
                    * self.conf["Doppler FFT size"]
                    / 2
                )
                self.conf["num_chirps"] = (
                    self.conf["Doppler FFT size"] * self.conf["num_of_tx"]
                )
                self.conf["min_ramp_slope"] = min(
                    self.conf["max_ramp_slope"],
                    round(
                        self.conf["Bandwidth"]
                        * 1000
                        / (
                            self.conf["frame_duration"] * 500 / self.conf["num_chirps"]
                            - self.conf["min_interchirp_dur"]
                        ),
                        3,
                    ),
                )
            self.conf.update(self.conf)
