# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import the service(s) we will be using
from sic_framework.services.nlu.bert_nlu import (
    NLU,
    InferenceRequest,
    InferenceResult,
    NLUConf,
)
from sic_framework.services.openai_whisper_stt.whisper_stt import (
    GetTranscript,
    SICWhisper,
)

# Import libraries necessary for the demo
from os.path import abspath, join


class ASRNLUDemo(SICApplication):
    """
    ASR + NLU pipeline demo application.
    Demonstrates how to create a simple pipeline where Whisper transcribes your speech and
    feeds it into the NLU component to run inference.

    IMPORTANT:
    The Whisper component and NLU component need to be running:
    1. Install dependencies:
        pip install social-interaction-cloud[whisper-speech-to-text,nlu]
    2. Run the components:
        One terminal: run-whisper
        The other terminal: run-nlu
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(ASRNLUDemo, self).__init__()
        
        # Demo-specific initialization
        self.ontology_path = "conf/nlu/ontology.json"
        self.model_path = "conf/nlu/model_checkpoint.pt"
        self.num_turns = 10
        self.desktop = None
        self.whisper = None
        self.nlu = None
        
        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure Desktop, Whisper, and NLU."""
        self.logger.info("Setting up ASR + NLU pipeline...")
        
        # Initialize desktop
        self.desktop = Desktop()
        
        # Initialize Whisper
        self.whisper = SICWhisper(input_source=self.desktop.mic)
        
        # Initialize NLU
        nlu_conf = NLUConf(ontology_path=self.ontology_path, model_path=self.model_path)
        self.nlu = NLU(conf=nlu_conf)
    
    def run(self):
        """Main application loop."""
        self.logger.info("Starting ASR + NLU Demo")
        
        try:
            for i in range(self.num_turns):
                print("Talk now!")
                transcript = self.whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
                print("Transcript from whisper:", transcript.transcript)
                
                # Feed the whisper transcript to the NLU model to run inference
                result = self.nlu.request(InferenceRequest(transcript.transcript))
                print("The predicted intent is:", result.intent)
                print("The predicted slots are:", result.slots)
            
            print("Done")
            self.logger.info("ASR + NLU demo completed")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = ASRNLUDemo()
    demo.run()
