from os.path import abspath, join
from pathlib import Path

from sic_framework.core.sic_application import SICApplication

from droomrobot.core import Droomrobot, AnimationType
from droomrobot.droomrobot_control import DroomrobotControl

def video_interaction(droomrobot: Droomrobot):
    droomrobot.animate(AnimationType.ACTION, "random_short4", run_async=True)
    droomrobot.animate(AnimationType.EXPRESSION, "emo_007", run_async=True)
    droomrobot.say("Hee, hoi. De droomrobot hier.")
    droomrobot.say("Ik wilde je graag nog wat laten weten, nu je weer wakker bent.")
    droomrobot.say("Ik vond het dat je het echt heel knap deed.")
    droomrobot.say("Echt heel dapper dat ik er bij mocht zijn, tijdens zo'n spannend moment.")
    droomrobot.say("Ik heb goed kunnen oefenen, om een droomrobot te zijn.")
    droomrobot.say("Ik ben heel dankbaar dat jij mij hebt geholpen.")
    droomrobot.say("Jij bent mijn held!")
    droomrobot.say("Ik hoop dat ik jou ook een beetje heb kunnen helpen.")
    droomrobot.say("Met het ademhalen en samen fantaseren over je droomplek.")
    droomrobot.say("Ik ga mijn best doen om nog meer kinderen te kunnen helpen.")
    droomrobot.say("Tot slot, wil ik je nog dit dansje laten zien")
    droomrobot.animate(AnimationType.ACTION, "dance_0007en", run_async=True)
    droomrobot.play_audio('resources/audio/happy_dance.wav')
    droomrobot.say("Dat was het weer! Doei doei!")


if __name__ == '__main__':
    root = Path(__file__).parent.parent.resolve()

    droomrobot_control = DroomrobotControl()

    droomrobot_control.connect(sic_app=SICApplication(),
                               mini_ip="192.168.2.19`", mini_id="00041", mini_password="mini",
                               redis_ip="192.168.2.7",
                               google_keyfile_path=root / 'conf' / 'dialogflow' / "google_keyfile.json",
                               env_path=root / 'conf' / '.evn',
                               computer_test_mode=True)

    video_interaction(droomrobot_control.droomrobot)
