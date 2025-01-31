from os.path import abspath, join

from sic_framework.devices.desktop import Desktop
from sic_framework.services.nlu.bert_nlu import (
    NLU,
    InferenceRequest,
    InferenceResult,
    NLUConf,
)
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import (
    GetTranscript,
    SICWhisper,
)

"""
This demo shows how to create a simple pipeline (ASR + NLU) where Whisper transcribes your speech and
feeds it into the NLU component to run inference

IMPORTANT
The Whisper component and NLU component need to be running:

1. Install dependencies:
    pip install social-interaction-cloud[whisper-speech-to-text,nlu]
2. Run the components:
    One terminal: run-whisper
    The other terminal: run-nlu
"""


desktop = Desktop()

whisper = SICWhisper()

whisper.connect(desktop.mic)

ontology_path = abspath(join("..", "..", "conf", "nlu", "ontology.json"))
model_path = abspath(join("..", "..", "conf", "nlu", "model_checkpoint.pt"))
nlu_conf = NLUConf(ontology_path=ontology_path, model_path=model_path)
nlu = NLU(conf=nlu_conf)

for i in range(10):
    print("Talk now!")
    transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
    print("Transcript from whisper", transcript.transcript)
    # Feed the whisper transcript to the NLU model to run inference
    result = nlu.request(InferenceRequest(transcript.transcript))
    print("The predicted intent is:", result.intent)
    print("The predicted slots are:", result.slots)
print("done")
