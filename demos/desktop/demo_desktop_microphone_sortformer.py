from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.devices.common_desktop.desktop_microphone import MicrophoneConf
from sic_framework.devices.desktop import Desktop
from sic_framework.services.streaming_sortformer import (
    GetDiarizationRequest,
    STMSortformer,
    STMSortformerConf,
    STMSortformerUtils,
)


class STMSortformerDemo(SICApplication):
    def __init__(self):
        super(STMSortformerDemo, self).__init__()

        # Demo-specific initialization
        self.desktop = None
        self.desktop_mic = None
        self.sortformer = None
        self.utils = None
        # Configure logging
        self.set_log_level(sic_logging.INFO)
        self.setup()

    def setup(self):
        """Initialize and configure Streaming Sortformer."""
        self.logger.info("Setting up Streaming Sortformer...")

        self.utils = STMSortformerUtils()

        # initialize the desktop device to get the microphone
        mic_conf = MicrophoneConf(sample_rate=16000, device_index=0)
        self.desktop = Desktop(mic_conf=mic_conf)
        self.desktop_mic = self.desktop.mic

        # initialize the sortformer component
        sortformer_conf = STMSortformerConf()
        self.sortformer = STMSortformer(
            conf=sortformer_conf, input_source=self.desktop_mic
        )

    def run(self):
        """Main application loop."""
        self.logger.info("Starting Sortformer Demo")
        print(" -- Starting Demo -- ")

        try:
            while not self.shutdown_event.is_set():
                result = self.sortformer.request(GetDiarizationRequest())
                print(self.utils.show_diar_df(result.speaker_timestamps))
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = STMSortformerDemo()
    demo.run()
