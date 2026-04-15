from droomrobot.bloedafname4 import Bloedafname4
from droomrobot.bloedafname6 import Bloedafname6
from droomrobot.bloedafname9 import Bloedafname9
from droomrobot.core import Droomrobot, AnimationType
from droomrobot.droomrobot_script import InteractionContext, InteractionSession
from droomrobot.droomrobot_tts import GoogleTTSConf
from droomrobot.kapinductie4 import Kapinductie4
from droomrobot.kapinductie6 import Kapinductie6
from droomrobot.sonde4 import Sonde4
from droomrobot.sonde6 import Sonde6
from droomrobot.sonde9 import Sonde9
from droomrobot.kapinductie9 import Kapinductie9


class DroomrobotControl:

    def __init__(self):
        self.droomrobot = None
        self.interaction_script = None

    def connect(self, sic_app, mini_ip, mini_id, mini_password, redis_ip,
                google_keyfile_path, sample_rate_dialogflow_hertz=44100, dialogflow_language="nl",
                dialogflow_timeout=None,
                tts_conf=GoogleTTSConf(),
                env_path=None,
                computer_test_mode=False):

        self.droomrobot = Droomrobot(sic_app=sic_app, mini_ip=mini_ip, mini_id=mini_id, mini_password=mini_password, redis_ip=redis_ip,
                                     google_keyfile_path=google_keyfile_path, sample_rate_dialogflow_hertz=sample_rate_dialogflow_hertz,
                                     dialogflow_language=dialogflow_language, dialogflow_timeout=dialogflow_timeout,
                                     tts_conf=tts_conf,
                                     env_path=env_path,
                                     computer_test_mode=computer_test_mode)

    def disconnect(self):
        if self.droomrobot:
            self.droomrobot.disconnect()

    def start(self, participant_id: str,
              interaction_context: InteractionContext,
              session: InteractionSession,
              user_model: dict,
              audio_amplified: bool,
              always_regenerate: bool):
        # Select class based on script_id and child_age
        script_class_map = {
            InteractionContext.SONDE: [Sonde4, Sonde6, Sonde9],
            InteractionContext.KAPINDUCTIE: [Kapinductie4, Kapinductie6, Kapinductie9],
            InteractionContext.BLOEDAFNAME: [Bloedafname4, Bloedafname6, Bloedafname9],
        }

        def select_age_index(age):
            if age <= 6:
                return 0
            elif 6 < age <= 9:
                return 1
            else:
                return 2

        if interaction_context not in script_class_map:
            print(f"[Error] Unsupported script_id: {interaction_context}")
            return

        age_index = select_age_index(user_model['child_age'])
        script_class = script_class_map[interaction_context][age_index]

        # Instantiate the appropriate script
        self.interaction_script = script_class(self.droomrobot)

        try:
            self.interaction_script.prepare(participant_id=participant_id, session=session,
                                            user_model_addendum=user_model, audio_amplified=audio_amplified,
                                            always_regenerate=always_regenerate)
            self.droomrobot.start_logging(participant_id, {
                'participant_id': participant_id,
                'context': interaction_context.name,
                'session': session,
                'child_age': user_model['child_age']
            })
            self.interaction_script.run()
            self.droomrobot.stop_logging()
        except KeyboardInterrupt:
            print("[Interrupted] Interaction is stopped manually")
        except Exception as e:
            print(f"[Error] Exception while running script: {e}")
        finally:
            self.stop()

    def pause(self):
        if self.interaction_script:
            self.interaction_script.pause()

    def resume(self):
        if self.interaction_script:
            self.interaction_script.resume()

    def stop(self):
        if self.interaction_script:
            self.interaction_script.stop()

    def dance(self):
        if self.droomrobot:
            self.droomrobot.say("Laten we dansen.")
            self.droomrobot.animate(AnimationType.ACTION, "dance_0007en", run_async=True)
            self.droomrobot.play_audio('resources/audio/happy_dance.wav')

    def say(self, text: str):
        if self.droomrobot:
            self.droomrobot.say(text, animated=False)

# if __name__ == '__main__':
#     droomrobot_control = DroomrobotControl()
#
#     droomrobot_control.connect(mini_ip="192.168.178.111", mini_id="00167", mini_password="alphago",
#                                redis_ip="192.168.178.84",
#                                google_keyfile_path=abspath(
#                                    join("../conf", "dialogflow", "google_keyfile.json")),
#                                openai_key_path=abspath(join("../conf", ".env")),
#                                default_speaking_rate=0.8, computer_test_mode=False)
#
#     droomrobot_control.start(participant_id='996',
#                              interaction_context=InteractionContext.SONDE,
#                              session=InteractionSession.INTRODUCTION,
#                              user_model={
#                                  'child_name': 'Bas',
#                                  'child_age': 10})
