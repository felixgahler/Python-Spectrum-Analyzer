import pyaudio
import numpy as np
from scipy.signal import butter, lfilter
from scipy.fft import fft, ifft
from config import VOLUME_FACTOR, EQ_BANDS, EFFECTS, SCALES, KEYS

class AudioStream:
    def __init__(self, rate=44100, channels=1, buffer_size=2048):
        """
        Initialisiert den Audio-Stream mit grundlegenden Einstellungen
        """
        self.rate = rate
        self.channels = channels
        self.buffer_size = buffer_size
        self.audio = pyaudio.PyAudio()
        
        # Verfügbare Eingabegeräte ausgeben
        self.print_input_devices()
        
        # Audio-Stream mit Float32
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.buffer_size
        )
        self.window = np.hanning(self.buffer_size)
        self.eq_gains = [1.0] * len(EQ_BANDS)
        self._init_eq_filters()
        
        # Buffer für Effekte
        self.echo_buffer = np.zeros(int(rate * 1.0))
        self.reverb_buffer = np.zeros(int(rate * 2.0))
        self.effects = EFFECTS.copy()
        self.flanger_phase = 0
        self.flanger_buffer = np.zeros(rate)
        self.autotune_buffer = np.zeros(buffer_size * 2)
        self.sidechain_envelope = 0
        self.ducking_envelope = 0

    def _init_eq_filters(self):
        """
        Initialisiert die Equalizer-Filter für jedes Frequenzband
        """
        self.eq_filters = []
        for freq in EQ_BANDS:
            # Bandpass-Filter für jedes Frequenzband
            low = freq * 0.7  # Untere Grenzfrequenz
            high = freq * 1.3  # Obere Grenzfrequenz
            b1, a1 = self._create_bandpass(low, high, self.rate)
            self.eq_filters.append((b1, a1))

    def _create_bandpass(self, lowcut, highcut, fs, order=2):
        """
        Erstellt einen Bandpass-Filter
        """
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        return b, a

    def apply_eq(self, data):
        """
        Wendet den Equalizer auf die Audiodaten an
        """
        # Konvertierung zu float für die Verarbeitung
        float_data = data.astype(np.float32)
        
        # Separate gefilterte Signale für jedes Band
        filtered_signals = []
        for i, (b, a) in enumerate(self.eq_filters):
            if self.eq_gains[i] != 1.0:  # Nur filtern wenn Gain nicht neutral
                filtered = lfilter(b, a, float_data)
                filtered_signals.append(filtered * self.eq_gains[i])
            else:
                filtered_signals.append(float_data / len(self.eq_filters))
        
        # Kombiniere alle gefilterten Signale
        output = np.sum(filtered_signals, axis=0)
        
        return output

    def apply_echo(self, data):
        """
        Wendet einen Echo-Effekt auf die Audiodaten an
        """
        if not self.effects["Echo"]["enabled"]:
            return data
            
        delay_samples = int(self.rate * self.effects["Echo"]["delay"])
        feedback = self.effects["Echo"]["feedback"]
        
        # Schiebe alte Daten im Buffer
        self.echo_buffer[:-len(data)] = self.echo_buffer[len(data):]
        self.echo_buffer[-len(data):] = data
        
        # Addiere verzögertes Signal
        output = data + feedback * self.echo_buffer[:-delay_samples]
        return output

    def apply_reverb(self, data):
        """
        Wendet einen einfachen Reverb-Effekt an
        """
        if not self.effects["Reverb"]["enabled"]:
            return data
            
        room_size = self.effects["Reverb"]["room_size"]
        damping = self.effects["Reverb"]["damping"]
        wet_level = self.effects["Reverb"]["wet_level"]
        
        # Schiebe Buffer
        self.reverb_buffer[:-len(data)] = self.reverb_buffer[len(data):]
        self.reverb_buffer[-len(data):] = data
        
        # Erstelle Reverb durch mehrere verzögerte und gedämpfte Kopien
        reverb = np.zeros_like(data, dtype=np.float32)
        for i in range(4):  # 4 Reflexionen
            delay = int(self.rate * (0.02 + i * 0.01 * room_size))
            reverb += damping ** i * self.reverb_buffer[len(self.reverb_buffer)-delay-len(data):-delay]
        
        return (1 - wet_level) * data + wet_level * reverb

    def apply_flanger(self, data):
        """
        Wendet einen Flanger-Effekt an
        """
        if not self.effects["Flanger"]["enabled"]:
            return data
            
        depth = self.effects["Flanger"]["depth"]
        rate = self.effects["Flanger"]["rate"]
        feedback = self.effects["Flanger"]["feedback"]
        wet = self.effects["Flanger"]["wet"]
        
        # LFO für den Flanger
        lfo = depth * np.sin(2 * np.pi * rate * np.arange(len(data)) / self.rate + self.flanger_phase)
        self.flanger_phase += 2 * np.pi * rate * len(data) / self.rate
        
        # Delay-Line
        delayed = np.zeros_like(data, dtype=np.float32)
        for i in range(len(data)):
            delay_samples = int(lfo[i] * 100)  # Max 100 Samples Delay
            if i >= delay_samples:
                delayed[i] = data[i - delay_samples]
        
        output = data + wet * (delayed + feedback * self.flanger_buffer[-len(data):])
        self.flanger_buffer = np.roll(self.flanger_buffer, len(data))
        self.flanger_buffer[:len(data)] = data
        
        return output

    def apply_autotune(self, data):
        """
        Wendet Auto-Tune auf das Signal an
        """
        if not self.effects["AutoTune"]["enabled"]:
            return data
            
        # Pitch Detection
        fft_size = 2048
        window = np.hanning(fft_size)
        padded = np.pad(data, (0, fft_size - len(data)))
        spectrum = fft(padded * window)
        freqs = np.fft.fftfreq(fft_size, 1/self.rate)
        
        # Finde dominante Frequenz
        magnitude = np.abs(spectrum)
        peak_freq = freqs[np.argmax(magnitude)]
        
        if peak_freq > 0:
            # Konvertiere Frequenz zu MIDI-Note
            midi_note = 69 + 12 * np.log2(peak_freq / 440)
            
            # Finde nächste Note in der Skala
            scale = SCALES[self.effects["AutoTune"]["scale"]]
            key_offset = KEYS.index(self.effects["AutoTune"]["key"]) 
            
            note = round(midi_note)
            note_in_scale = (note - key_offset) % 12
            closest_scale_note = min(scale, key=lambda x: abs(x - note_in_scale))
            
            # Pitch Shifting
            pitch_shift = closest_scale_note - note_in_scale
            if abs(pitch_shift) > 0:
                strength = self.effects["AutoTune"]["strength"]
                shift_amount = np.exp2(pitch_shift / 12 * strength)
                
                # Phase Vocoder
                new_spectrum = np.zeros_like(spectrum)
                for i in range(len(spectrum)):
                    new_idx = int(i * shift_amount)
                    if new_idx < len(spectrum):
                        new_spectrum[new_idx] = spectrum[i]
                
                output = np.real(ifft(new_spectrum))[:len(data)]
                return output * window[:len(data)]
        
        return data

    def apply_sidechain(self, data):
        """
        Wendet Sidechain-Kompression an
        """
        if not self.effects["Sidechain"]["enabled"]:
            return data
            
        threshold = self.effects["Sidechain"]["threshold"]
        ratio = self.effects["Sidechain"]["ratio"]
        attack = self.effects["Sidechain"]["attack"]
        release = self.effects["Sidechain"]["release"]
        
        # RMS-Level berechnen
        rms = np.sqrt(np.mean(data**2))
        db = 20 * np.log10(max(rms, 1e-6))
        
        # Envelope Follower
        if db > threshold:
            target = 1 - (db - threshold) * (1 - 1/ratio)
            self.sidechain_envelope += (target - self.sidechain_envelope) * (1 - np.exp(-1/(attack * self.rate)))
        else:
            self.sidechain_envelope += (1 - self.sidechain_envelope) * (1 - np.exp(-1/(release * self.rate)))
        
        return data * self.sidechain_envelope

    def apply_ducking(self, data):
        """
        Wendet Ducking an
        """
        if not self.effects["Ducking"]["enabled"]:
            return data
            
        threshold = self.effects["Ducking"]["threshold"]
        reduction = self.effects["Ducking"]["reduction"]
        attack = self.effects["Ducking"]["attack"]
        release = self.effects["Ducking"]["release"]
        
        # RMS-Level berechnen
        rms = np.sqrt(np.mean(data**2))
        db = 20 * np.log10(max(rms, 1e-6))
        
        # Envelope Follower
        if db > threshold:
            target = 1 - reduction
            self.ducking_envelope += (target - self.ducking_envelope) * (1 - np.exp(-1/(attack * self.rate)))
        else:
            self.ducking_envelope += (1 - self.ducking_envelope) * (1 - np.exp(-1/(release * self.rate)))
        
        return data * self.ducking_envelope

    def print_input_devices(self):
        """
        Gibt alle verfügbaren Audio-Eingabegeräte aus
        """
        print("\nVerfügbare Audio-Eingabegeräte:")
        for i in range(self.audio.get_device_count()):
            dev_info = self.audio.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:  # Nur Eingabegeräte
                print(f"Device {i}: {dev_info['name']}")
                print(f"   Kanäle: {dev_info['maxInputChannels']}")
                print(f"   Sample Rate: {int(dev_info['defaultSampleRate'])}")
        print()

    def get_audio_data(self, volume_factor=VOLUME_FACTOR):
        """
        Liest und verarbeitet Audiodaten
        """
        try:
            # Rohdaten lesen
            data = self.stream.read(self.buffer_size, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.float32)
            
            # Einfache Lautstärkeanpassung
            audio_data = audio_data * volume_factor
            
            # Konvertierung zu int16 für die Visualisierung
            audio_data = np.clip(audio_data * 32768.0, -32768, 32767).astype(np.int16)
            
            return audio_data
            
        except Exception as e:
            print(f"Fehler bei der Audioaufnahme: {str(e)}")
            return np.zeros(self.buffer_size, dtype=np.int16)

    def set_eq_gain(self, band_index, gain):
        """
        Setzt den Gain für ein bestimmtes Frequenzband
        """
        if 0 <= band_index < len(self.eq_gains):
            self.eq_gains[band_index] = gain

    def stop(self):
        """
        Beendet den Audio-Stream und gibt Ressourcen frei
        """
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
