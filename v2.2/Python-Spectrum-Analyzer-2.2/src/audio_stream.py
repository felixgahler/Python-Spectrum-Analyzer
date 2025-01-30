import pyaudio
import numpy as np
from scipy.signal import butter, lfilter
from config import VOLUME_FACTOR

class AudioStream:
    def __init__(self, rate=44100, channels=1, buffer_size=1024, filter_cutoff=2500, filter_order=2):
        """
        inits audio stream with specified settings, including sample rate, channels, buffer size, and high-pass filter
        """
        self.rate = rate
        self.channels = channels
        self.buffer_size = buffer_size
        self.filter_cutoff = filter_cutoff
        self.filter_order = filter_order
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.buffer_size
        )
        self.window = np.hanning(self.buffer_size)

    def butter_highpass(self, cutoff, fs, order=5):
        """
        creates coefficients for a high-pass filter with the specified cutoff frequency and order

        :param cutoff: Cutoff frequency of the filter in Hz.
        :param fs: Sampling frequency in Hz.
        :param order: Order of the filter.
        :return: Filter coefficients (b, a).
        """
        nyquist = 0.5 * fs
        normal_cutoff = cutoff / nyquist
        b, a = butter(order, normal_cutoff, btype='high', analog=False)
        return b, a

    def highpass_filter(self, data, cutoff, fs, order=5):
        """
        Applies a high-pass filter to the provided audio data.

        :param data: Audio data to filter.
        :param cutoff: Cutoff frequency in Hz.
        :param fs: Sampling frequency in Hz.
        :param order: Order of the filter.
        :return: Filtered audio data.
        """
        b, a = self.butter_highpass(cutoff, fs, order=order)
        return lfilter(b, a, data)

    def get_audio_data(self, volume_factor=VOLUME_FACTOR, normalize=False):
        """
        Reads audio data from the stream, applies filtering and volume adjustment,
        and optionally normalizes the data.

        :param volume_factor: Factor to adjust the volume of the audio data.
        :param normalize: Whether to normalize the audio data.
        :return: Processed audio data as a NumPy array.
        """
        data = self.stream.read(self.buffer_size, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)
        audio_data = self.highpass_filter(audio_data, cutoff=self.filter_cutoff, fs=self.rate, order=self.filter_order)
        audio_data = audio_data * self.window
        audio_data = audio_data * volume_factor

        if normalize:
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val * 32767

        audio_data = np.clip(audio_data, -32768, 32767)
        return audio_data.astype(np.int16)

    def stop(self):
        """
        Stops the audio stream and releases resources.
        """
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
