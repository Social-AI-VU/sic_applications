import pyaudio


class AvailableAudio():

    def __init__(self):
        self.p = pyaudio.PyAudio()

    def list_available_audio_device(self):
        self._available_microphones()
        self._available_speakers()
        self._terminate()

    def _available_microphones(self):
        print("Available Microphones")
        for i in range(self.p.get_device_count()):
            try:
                dev = self.p.get_device_info_by_index(i)
                if dev.get('maxInputChannels') > 0:
                    print(f"Input Device id {i} - {dev.get('name')}")
            except Exception:
                continue  # Skip problematic devices

    def _available_speakers(self):
        print("\nAvailable Speakers")
        for i in range(self.p.get_device_count()):
            try:
                dev = self.p.get_device_info_by_index(i)
                if dev.get('maxOutputChannels') > 0:
                    print(f"Output Device id {i} - {dev.get('name')}")
            except Exception:
                continue  # Skip problematic devices

    def _terminate(self):
        self.p.terminate()


if __name__ == '__main__':
    available_audio = AvailableAudio()
    available_audio.list_available_audio_device()