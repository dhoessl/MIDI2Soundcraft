from scipy.interpolate import interp1d


class ConfigVars:
    def __init__(self) -> None:
        self.mix = {
            "50": interp1d([0.527044025, 1], [-10, 10]),
            "37": interp1d([0.372327044, 0.527044025], [-20, -10]),
            "18": interp1d([0.181132075, 0.372327044], [-40, -20]),
            "5": interp1d([0.056603773, 0.181132075], [-60, -40]),
            "0": interp1d([0, 0.181132075], [-90, -60])
        }
        self.map_values = {
            "100": interp1d([0, 1], [0, 100]),
            "200": interp1d([0, 1], [0, 200]),
            "100pm": interp1d([0, 1], [-100, 100])
        }
        self.lpf_rev = [
            interp1d([0, .1], [400, 597]),
            interp1d([.1, .2], [597, 891]),
            interp1d([.2, .3], [891, 1330]),
            interp1d([.3, .4], [1330, 1980]),
            interp1d([.4, .5], [1980, 2960]),
            interp1d([.5, .6], [2960, 4430]),
            interp1d([.6, .7], [4430, 6620]),
            interp1d([.7, .8], [6620, 9890]),
            interp1d([.8, .9], [9890, 14700]),
            interp1d([.9, 1], [14700, 22000]),
        ]
        self.time_rev = [
            interp1d([0, .1], [300, 416]),
            interp1d([.1, .2], [416, 578]),
            interp1d([.2, .3], [578, 803]),
            interp1d([.3, .4], [803, 1115]),
            interp1d([.4, .5], [1115, 1549]),
            interp1d([.5, .6], [1549, 2151]),
            interp1d([.6, .7], [2151, 2987]),
            interp1d([.7, .8], [2987, 4148]),
            interp1d([.8, .9], [4148, 5760]),
            interp1d([.9, 1], [5760, 8000])
        ]
        self.hpf_rev = [
            interp1d([0, .1], [20, 34]),
            interp1d([.1, .2], [34, 60]),
            interp1d([.2, .3], [60, 104]),
            interp1d([.3, .4], [104, 182]),
            interp1d([.4, .5], [182, 316]),
            interp1d([.5, .6], [316, 549]),
            interp1d([.6, .7], [549, 954]),
            interp1d([.7, .8], [954, 1650]),
            interp1d([.8, .9], [1650, 2870]),
            interp1d([.9, 1], [2870, 5000])
        ]
        self.time_delay = [
            interp1d([0, .1], [0, 154]),
            interp1d([.1, .2], [154, 229]),
            interp1d([.2, .3], [229, 323]),
            interp1d([.3, .4], [323, 436]),
            interp1d([.4, .5], [436, 562]),
            interp1d([.5, .6], [562, 691]),
            interp1d([.6, .7], [691, 812]),
            interp1d([.7, .8], [812, 912]),
            interp1d([.8, .9], [912, 977]),
            interp1d([.9, 1], [977, 1000])
        ]
        self.lpf_delay = [
            interp1d([0, .1], [20, 40]),
            interp1d([.1, .2], [40, 81]),
            interp1d([.2, .3], [81, 163]),
            interp1d([.3, .4], [163, 329]),
            interp1d([.4, .5], [329, 664]),
            interp1d([.5, .6], [664, 1330]),
            interp1d([.6, .7], [1330, 2690]),
            interp1d([.7, .8], [2690, 5430]),
            interp1d([.8, .9], [5430, 10900]),
            interp1d([.9, 1], [10900, 22000]),
        ]
        self.time_room = [
            interp1d([0, .1], [100, 125]),
            interp1d([.1, .2], [125, 158]),
            interp1d([.2, .3], [158, 199]),
            interp1d([.3, .4], [199, 251]),
            interp1d([.4, .5], [251, 316]),
            interp1d([.5, .6], [316, 398]),
            interp1d([.6, .7], [398, 501]),
            interp1d([.7, .8], [501, 630]),
            interp1d([.8, .9], [630, 794]),
            interp1d([.9, 1], [794, 1000]),
        ]
        # Reverb (0) and Room (3) use the same parnames
        self.map_parname = {
            0: {
                1: "Time",
                2: "HF Damping",
                3: "Bass Gain",
                4: "LPF",
                5: "HPF",
            },
            1: {
                1: "Length",
                2: "Division",
                3: "Feedback",
                4: "LPF"
            },
            2: {
                1: "Detune",
                2: "Density",
                3: "LPF"
            },
            "special":
            {
                "m": "BPM",
                "x": "Mix",
                "e": "Mute"
            }
        }
        self.map_fxname = {
            0: "Reverb",
            1: "Delay",
            2: "Chorus",
            3: "Room"
        }
        self.map_color = {
            0: "blue",
            1: "orange",
            2: "magenta",
            3: "green"
        }

    def midi_to_soundcraft(self, val: float | int) -> float:
        """ Format a value given by midi to use it for soundcraft.
            Midi Values: 0 - 127
            Soundcraft:  0 - 1
        """
        return val / 127

    def soundcraft_to_midi(self, val: float | int) -> int:
        """ Format a value given by Soundcraft to use for midi display.
            Midi Display:   0 - 7
            Soundcraft:     0 - 1
        """
        return round(8 * float(val))

    def midi_grid_to_soundcraft(self, val: int) -> float:
        """ Format a value given by midi grid to use it for soundcraft.
            Use Mute for 0
            Midi Values: 0(+1) - 7(+1)
            Soundcraft:  0 - 1
        """
        return (val + 1) / 8



class OutputFormatter:
    def __init__(self):
        self.vars = ConfigVars()

    def fx_name(self, num) -> str:
        return self.vars.map_fxname(int(num))

    def mix(self, val) -> str:
        if float(val) >= self.vars.mix["50"].x[0]:
            out = round(float(self.vars.mix["50"](val)), 1)
        elif float(val) >= self.vars.mix["37"].x[0]:
            out = round(float(self.vars.mix["37"](val)), 1)
        elif float(val) >= self.vars.mix["18"].x[0]:
            out = round(float(self.vars.mix["18"](val)), 1)
        elif float(val) >= self.vars.mix["5"].x[0]:
            out = round(float(self.vars.mix["5"](val)), 1)
        else:
            out = round(float(self.vars.mix["0"](val)), 1)
        return f"{out} dB"

    def fx_parname(self, fx, par) -> str:
        fx = 0 if int(fx) == 3 else int(fx)
        try:
            return self.vars.map_parname[fx][int(par[-1:])]
        except (KeyError, ValueError):
            return self.vars.map_parname["special"][par[-1:]]

    def fx_parval(self, fx, par, val, fx1par1=1) -> str:
        fx = int(fx)
        fx_val = float(val)
        sel = 9 if fx_val == 1 else int(fx_val * 10 // 1)
        if par == "bpm":
            return f"{int(fx_val)}"
        if par == "mute":
            return "On" if fx_val == 1 else "Off"
        if par == "mix":
            return self.mix(fx_val)
        if fx == 0:
            if par == "par1":
                return f"{int(self.vars.time_rev[sel](fx_val))} ms"
            elif par == "par2" or par == "par3":
                return f"{int(self.vars.map['100'](fx_val))}%"
            elif par == "par4":
                val = int(self.vars.lpf_rev[sel](fx_val))
                if val >= 10e3:
                    return f"{round(val/1000, 1)} kHz"
                elif val >= 10e2:
                    return f"{round(val/1000, 2)} kHz"
                else:
                    return f"{val} Hz"
            elif par == "par5":
                val = int(self.vars.hpf_rev[sel](fx_val))
                if val >= 10e2:
                    return f"{round(val/1000, 2)} kHz"
                else:
                    return f"{val} Hz"
        elif fx == 1:
            if par == "par1":
                if fx_val == 0:
                    return "SUB DIV MODE"
                else:
                    return f"{int(self.vars.time_delay[sel](fx_val))} ms"
            elif par == "par2":
                if fx1par1 > 0:
                    return "TIME MODE"
                else:
                    return f"{round(float(self.vars.map['200'](fx_val)), 1)}%"
            elif par == "par3":
                return f"{int(self.vars.map['100'](fx_val))}%"
            elif par == "par4":
                val = int(self.vars.lpf_delay[sel](fx_val))
                if val >= 10e3:
                    return f"{round(val / 1000, 1)} kHz"
                elif val >= 10e2:
                    return f"{round(val / 1000, 2)} kHz"
                else:
                    return f"{val} Hz"
        elif fx == 2:
            if par == "par1":
                return f"{int(self.vars.map['100pm'](fx_val))}c"
            elif par == "par2":
                return f"{int(self.vars.map['100'](fx_val))}%"
            elif par == "par3":
                val = int(self.vars.lpf_rev[sel](fx_val))
                if val >= 10e3:
                    return f"{round(val / 1000, 1)} kHz"
                elif val >= 10e2:
                    return f"{round(val / 1000, 2)} kHz"
                else:
                    return f"{val} Hz"
        elif fx == 3:
            if par == "par1":
                return f"{int(self.vars.time_room[sel](fx_val))} ms"
            elif par == "par2":
                return f"{int(self.vars.map['100'](fx_val))}%"
            elif par == "par3":
                return f"{int(self.vars.map['100'](fx_val))}%"
            elif par == "par4":
                val = int(self.vars.lpf_rev[sel](fx_val))
                if val >= 10e3:
                    return f"{round(val / 1000, 1)} kHz"
                elif val >= 10e2:
                    return f"{round(val / 1000, 2)} kHz"
                else:
                    return f"{val} Hz"
            elif par == "par5":
                val = int(self.vars.hpf_rev[sel](fx_val))
                print(f"{val}")
                if val >= 10e2:
                    return f"{round(val / 1000, 2)} kHz"
                else:
                    return f"{val} Hz"
