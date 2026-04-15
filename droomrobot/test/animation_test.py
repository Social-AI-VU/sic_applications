from itertools import chain
from os.path import abspath, join
from time import sleep

from droomrobot.core import Droomrobot, AnimationType
from droomrobot.droomrobot_tts import GoogleTTSConf, TTSConf

"""
Demo: Animation with alphamini.

"""


class AnimationTest:
    def __init__(self, mini_ip, mini_id, mini_password, redis_ip,
                 google_keyfile_path, sample_rate_dialogflow_hertz=44100, dialogflow_language="nl",
                 dialogflow_timeout=None,
                 voice_conf: TTSConf = GoogleTTSConf(),
                 openai_key_path=None, computer_test_mode=False):
        self.mini_id = mini_id
        self.droomrobot = Droomrobot(mini_ip=mini_ip, mini_id=mini_id, mini_password=mini_password, redis_ip=redis_ip,
                                     google_keyfile_path=google_keyfile_path,
                                     sample_rate_dialogflow_hertz=sample_rate_dialogflow_hertz,
                                     dialogflow_language=dialogflow_language, dialogflow_timeout=dialogflow_timeout,
                                     tts_conf=voice_conf,
                                     env_path=openai_key_path,
                                     computer_test_mode=computer_test_mode)

    def speaking_gestures(self):
        speaking_acts = [
            "speakingAct1",
            "speakingAct2",
            "speakingAct3",
            "speakingAct4",
            "speakingAct5",
            "speakingAct6",
            "speakingAct7",
            "speakingAct8",
            "speakingAct9",
            "speakingAct10",
            "speakingAct11",
            "speakingAct12",
            "speakingAct13",
            "speakingAct14",
            "speakingAct15",
            "speakingAct16",
            "speakingAct17"
        ]

        for animation in speaking_acts:
            try:
                self.droomrobot.say(f"Volgende is {animation}")
                self.droomrobot.animate(AnimationType.ACTION, animation)
                sleep(1)
            except Exception as e:
                print(e)

        self.droomrobot.say('Klaar')

    def dance(self):
        self.droomrobot.say("Laten we dansen.")
        self.droomrobot.animate(AnimationType.ACTION, "dance_0007en", run_async=True)
        self.droomrobot.play_audio('../resources/audio/happy_dance.wav')
        self.droomrobot.say('Klaar')

    def expressions(self, expression_type="all"):
        speaking_expressions = {
            "codemao": [
                "codemao1", "codemao2", "codemao3", "codemao4", "codemao5",
                "codemao6", "codemao7", "codemao8", "codemao9", "codemao10",
                "codemao11", "codemao12", "codemao13", "codemao14", "codemao15",
                "codemao16", "codemao17", "codemao18", "codemao19", "codemao20"],

            "basic": ["w_basic_0003_1", "w_basic_0005_1", "w_basic_0010_1", "w_basic_0011_1", "w_basic_0012_1"],

            "emo": ["emo_007", "emo_008", "emo_009", "emo_010", "emo_011",
                    "emo_013", "emo_014", "emo_015", "emo_016", "emo_019",
                    "emo_020", "emo_022", "emo_023", "emo_026", "emo_028"]
        }

        try:
            if expression_type == "all":
                expression_list = list(chain.from_iterable(speaking_expressions.values()))
            else:
                expression_list = list(speaking_expressions[expression_type])
            for expression in expression_list:

                self.droomrobot.say(f"Volgende is {expression}", animated=False)
                self.droomrobot.animate(AnimationType.EXPRESSION, expression)
                sleep(1)
        except Exception as e:
            print(e)

        self.droomrobot.say('Klaar', animated=False)


if __name__ == '__main__':
    droomrobot = AnimationTest(mini_ip="192.168.178.111", mini_id="00167", mini_password="alphago",
                               redis_ip="192.168.178.84",
                               google_keyfile_path=abspath(join("../../conf", "dialogflow", "google_keyfile.json")),
                               openai_key_path=abspath(join("../../conf", ".env")),
                               computer_test_mode=False)
    droomrobot.expressions('codemao')
