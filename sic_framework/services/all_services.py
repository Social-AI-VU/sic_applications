from sic_framework import SICComponentManager
from sic_framework.services.face_detection_dnn.face_detection_dnn import DNNFaceDetectionComponent
from sic_framework.services.openai_gpt.gpt import GPTComponent
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import WhisperComponent

if __name__ == '__main__':

    SICComponentManager([WhisperComponent, GPTComponent, DNNFaceDetectionComponent])