from os.path import abspath, join

from droomrobot.core import Droomrobot, InteractionConf
from droomrobot.droomrobot_tts import GoogleTTSConf, ElevenLabsTTSConf, TTSConf


class TTSTest:
    def __init__(self, mini_ip, mini_id, mini_password, redis_ip,
                 google_keyfile_path, sample_rate_dialogflow_hertz=44100, dialogflow_language="nl",
                 dialogflow_timeout=None,
                 tts_conf: TTSConf = GoogleTTSConf(),
                 openai_key_path=None, computer_test_mode=False):
        self.mini_id = mini_id
        self.droomrobot = Droomrobot(mini_ip=mini_ip, mini_id=mini_id, mini_password=mini_password, redis_ip=redis_ip,
                                     google_keyfile_path=google_keyfile_path,
                                     sample_rate_dialogflow_hertz=sample_rate_dialogflow_hertz,
                                     dialogflow_language=dialogflow_language, dialogflow_timeout=dialogflow_timeout,
                                     tts_conf=tts_conf,
                                     env_path=openai_key_path,
                                     computer_test_mode=computer_test_mode)

    def test_amplification(self):
        self.droomrobot.say("Normaal")
        self.droomrobot.say("Hallo, ik ben de droomrobot.")

        self.droomrobot.set_interaction_conf(InteractionConf(amplified=True))
        self.droomrobot.say("Versterkt")
        self.droomrobot.say("Hallo, ik ben de droomrobot.")

    def speak(self):
        self.droomrobot.set_interaction_conf(InteractionConf(always_regenerate=False))
        self.droomrobot.say("Hallo, ik ben de droomrobot.")
        self.droomrobot.say("De nieuwsgierige robot, met glanzende metalen armen en vrolijk knipperende lichtjes, ontdekte dat hij het allerleukst vond om te spelen."
                            " hij rolde lachend met een bal door de werkplaats en bouwde torens van blokken."
                            "Ook genoot hij van spelletjes waarbij hij puzzels oploste alsof hij een kind was."
                            "En dat vond hij erg leuk.")
        # self.droomrobot.say("De nieuwsgierige robot, met glanzende metalen armen en vrolijk knipperende lichtjes, ontdekte dat hij het allerleukst vond om te spelen.")
        # self.droomrobot.say(" hij rolde lachend met een bal door de werkplaats en bouwde torens van blokken.")
        # self.droomrobot.say("Ook genoot hij van spelletjes waarbij hij puzzels oploste alsof hij een kind was.")
        # self.droomrobot.say("En dat vond hij erg leuk.")
        self.droomrobot.say("Nu weer korte zin twee.")
        self.droomrobot.say("En drie.")
        # self.droomrobot.ask_fake("Hoe heet jij?", 2)
        # self.droomrobot.say("Mike, wat een leuke naam!")
        # answer_1 = self.droomrobot.ask_open("Wat vind jij leuk om te doen?")
        # self.droomrobot.say("Dat klikt leuk zeg.")
        # if answer_1:
        #     response_1 = self.droomrobot.personalize('Wat vind je leuk om te doen?', 7, answer_1)
        #     self.droomrobot.say(response_1)
        # self.droomrobot.say('laten we verder gaan.')
        self.droomrobot.disconnect()


if __name__ == '__main__':
    # tts_conf = GoogleVoiceConf()
    tts_conf = ElevenLabsTTSConf()
    test = TTSTest(mini_ip="192.168.178.251", mini_id="00041", mini_password="mini", redis_ip="192.168.178.84",
                   google_keyfile_path=abspath(join("../../conf", "dialogflow", "google_keyfile.json")),
                   openai_key_path=abspath(join("../../conf", ".env")),
                   tts_conf=tts_conf,
                   computer_test_mode=False)
    test.speak()
