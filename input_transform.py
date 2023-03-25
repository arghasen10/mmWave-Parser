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
            new_dict = {
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
            new_dict["num_of_rx"] = int(self.conf["antenna_conf"][0])
            new_dict["num_of_tx"] = int(self.conf["antenna_conf"][4])
            new_dict["frequency_band"] = int(self.conf["freq_band"][:2])
            N_fft2d_lo = new_dict["Doppler FFT list"][0]
            adc_samples_lo = 64

            if platform == "xWR14xx":
                new_dict["L3 Memory size"] = 256
                new_dict["CFAR memory size"] = 32768
                new_dict["ADCBuf memory size"] = 16384
                new_dict["max_num_of_tx"] = 3

            new_dict["num_virt_ant"] = self.conf["num_virt_ant"] or 8
            new_dict["Range Sensitivity"] = self.conf[
                "Range Sensitivity"
            ] or convertSensitivityLinearTodB(
                1200 if platform == "xWR14xx" else 5000,
                platform,
                new_dict["num_virt_ant"],
            )

            if platform == "xWR16xx":
                new_dict["Doppler Sensitivity"] = convertSensitivityLinearTodB(
                    5000,
                    platform,
                    new_dict["num_virt_ant"],
                )
                new_dict["chirps_per_interrupt"] = 0

            new_dict["num_virt_ant"] = new_dict["num_of_rx"] * new_dict["num_of_tx"]
            match new_dict["num_virt_ant"]:
                case 12:
                    new_dict["Lncoh"] = 3
                case 8:
                    new_dict["Lncoh"] = 2.2
                case 4:
                    new_dict["Lncoh"] = 1.5
                case 2:
                    new_dict["Lncoh"] = 0.7
                case 1:
                    new_dict["Lncoh"] = 0
                case _:
                    new_dict["Lncoh"] = 6

            new_dict["NF"] = 16 if new_dict["frequency_band"] == 77 else 15
            new_dict["loss_dB"] = (
                new_dict["Pt"]
                + new_dict["Gt"]
                + new_dict["Gr"]
                - new_dict["Lncoh"]
                - new_dict["Ld"]
                - new_dict["Ls"]
                - new_dict["Lim"]
                - new_dict["SNR_det"]
                - new_dict["NF"]
            )
            new_dict["loss_linear"] = 10 ** (new_dict["loss_dB"] / 10)
            new_dict["max_allowable_bandwidth"] = (
                4 if new_dict["frequency_band"] == 77 else 1
            )

            if subprofile_type == "Best Range Resolution":
                new_dict["Bandwidth"] = new_dict["max_allowable_bandwidth"]
                new_dict["total_bw"] = new_dict["Bandwidth"] * 1000
                new_dict["min_ramp_slope"] = 20 if platform == "xWR16xx" else 35
                new_dict["ramp_slope"] = (
                    self.conf["ramp_slope"] or new_dict["min_ramp_slope"]
                )
                new_dict["num_chirps"] = self.conf["num_chirps"] or 16
                new_dict["max_slope"] = min(
                    new_dict["max_slope"],
                    math.floor(
                        (
                            new_dict["max_allowable_bandwidth"]
                            * 1000
                            * new_dict["max_sampling_rate"]
                        )
                        / (
                            adc_samples_lo
                            + new_dict["max_sampling_rate"]
                            * (
                                new_dict["chirp_start_time"]
                                + new_dict["chirp_end_guard_time"]
                            )
                        )
                    ),
                )
                new_dict["max_slope"] = math.floor(new_dict["max_slope"] / 5) * 5
                # TODO: range_resolution_constraints
            elif subprofile_type == "Best Velocity Resolution":
                new_dict["Bandwidth"] = new_dict["Bandwidth"] or 0.5
                new_dict["Num_ADC_Samples"] = (
                    new_dict["Num_ADC_Samples"] or adc_samples_lo
                )
                new_dict["Doppler FFT size"] = (
                    new_dict["Doppler FFT size"] or N_fft2d_lo
                )
            elif subprofile_type == "Best Range":
                new_dict["num_chirps"] = new_dict["num_chirps"] or 16

            new_dict["frame_duration"] = round(1000 / new_dict["frame_rate"], 3)
            new_dict["max_ramp_slope"] = max(
                5,
                min(
                    new_dict["max_slope"],
                    math.floor(
                        (new_dict["Bandwidth"] * 1000)
                        / (
                            32 / new_dict["max_sampling_rate"]
                            + new_dict["chirp_start_time"]
                            + new_dict["chirp_end_guard_time"]
                        )
                    ),
                ),
            )

            if subprofile_type == "Best Velocity Resolution":
                new_dict["radial_velocity_resolution"] = (
                    math.ceil(
                        new_dict["lightspeed"]
                        * 100
                        / (new_dict["frequency_band"] * new_dict["frame_duration"])
                    )
                    / 100
                )
                new_dict["max_radial_velocity"] = round(
                    new_dict["radial_velocity_resolution"]
                    * new_dict["Doppler FFT size"]
                    / 2
                )
                new_dict["num_chirps"] = (
                    new_dict["Doppler FFT size"] * new_dict["num_of_tx"]
                )
                new_dict["min_ramp_slope"] = min(
                    new_dict["max_ramp_slope"],
                    round(
                        new_dict["Bandwidth"]
                        * 1000
                        / (
                            new_dict["frame_duration"] * 500 / new_dict["num_chirps"]
                            - new_dict["min_interchirp_dur"]
                        ),
                        3,
                    ),
                )
            self.conf.update(new_dict)
