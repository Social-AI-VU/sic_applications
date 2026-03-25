from os.path import abspath, join

from sic_framework.core.sic_application import SICApplication

from droomrobot.core import AnimationType, Droomrobot, InteractionConf
from droomrobot.droomrobot_script import DroomrobotScript, InteractionContext, InteractionSession
from droomrobot.droomrobot_tts import GoogleTTSConf, ElevenLabsTTSConf


class ScriptTest(DroomrobotScript):

    def __init__(self, droomrobot: Droomrobot, interaction_context=InteractionContext.BLOEDAFNAME) -> None:
        super(ScriptTest, self).__init__(droomrobot=droomrobot, interaction_context=interaction_context)

    def prepare(self, participant_id: str, session: InteractionSession, user_model_addendum: dict,
                audio_amplified: bool = False, always_regenerate: bool = False):
        super().prepare(participant_id, session, user_model_addendum, audio_amplified)
        self._test()

    def _test(self):
        interaction_conf = InteractionConf(speaking_rate=0.75, sleep_time=1.0, animated=True,
                                           amplified=self.audio_amplified, always_regenerate=self.always_regenerate)
        self.add_move(self.droomrobot.set_interaction_conf, interaction_conf)

        self.add_move(self.droomrobot.animate, AnimationType.ACTION, "random_short4", run_async=True)
        self.add_move(self.droomrobot.animate, AnimationType.EXPRESSION, "emo_007", run_async=True)
        self.add_move(self.droomrobot.say, 'Stel je je maar weer voor dat je in het waterpretpark bent.')
        self.add_move(self.droomrobot.say, lambda: f'Je gaat weer de trap op van jouw {self.user_model['kleur']} glijbaan, die je net al zo goed geoefend hebt.')
        self.add_move(self.droomrobot.say, 'Bij iedere stap voel je weer dat je lichaam zich goed voelt en je er kracht van krijgt.')
        self.add_move(self.droomrobot.say, 'Hoor het geluid van het water maar.')
        self.add_move(self.droomrobot.play_audio, 'resources/audio/splashing_water.wav')

        self.add_move(self.droomrobot.say, 'Boven aan ga je weer zitten en adem je weer rustig in.')
        self.add_move(self.droomrobot.play_audio, 'resources/audio/breath_in.wav')
        self.add_move(self.droomrobot.say, 'En uit.')
        self.add_move(self.droomrobot.play_audio, 'resources/audio/breath_out.wav')
        self.add_move(self.droomrobot.say, 'Je plaatst je handen naast je, je ademt diep in, en klaar voor de start!')
        self.add_move(self.droomrobot.say, 'Daar ga je! Je duwt jezelf zachtjes af, en voelt hoe je begint te glijden.')
        self.add_move(self.droomrobot.say, 'Eerst heel langzaam.')
        self.add_move(self.droomrobot.say, 'En dan iets sneller.')
        self.add_move(self.droomrobot.say, 'Precies zoals jij dat fijn vindt!')
        self.add_move(self.droomrobot.say, 'Je voelt het water langs je glijden, net als een zachte golf, die je meevoert.')
        self.add_move(self.droomrobot.say, 'Misschien voel je dat je soms tegen de zijkant aan komt, dat is gewoon een bocht in de glijbaan! Heel normaal!')
        self.add_move(self.droomrobot.say, 'Misschien heeft het water in je glijbaan wel een speciale kleur, en glitters, zodat het je extra kan helpen.')
        self.add_move(self.droomrobot.say, 'Je blijft lekker glijden, met het water dat je moeiteloos omlaag laat gaan. Soms gaat het even iets sneller, dan weer iets rustiger.')
        self.add_move(self.droomrobot.say, 'Misschien voel je een klein raar kriebeltje, alsof een waterstraaltje even tegen je neus spat.')
        self.add_move(self.droomrobot.say, 'Maar dat is oké, want jij weet dat je bijna beneden bent.')
        self.add_move(self.droomrobot.say, 'Je ademt rustig in en uit, net als de zachte golfjes om je heen.')
        self.add_move(self.droomrobot.say, 'Je komt lager en lager.')
        self.add_move(self.droomrobot.say, 'En nog een bocht.')
        self.add_move(self.droomrobot.say, 'De verpleegkundige vertelt je wanneer je bij de laatste bocht bent.')
        self.add_move(self.droomrobot.say, 'Je voelt jezelf soepel door de tunnel van de glijbaan glijden.')
        # self.add_move(self.droomrobot.say, 'Hallo, ik ben de droomrobot!')
        # self.add_move(self.droomrobot.ask_open, "Kun je wat zeggen?")
        # self.add_move(self.droomrobot.ask_fake, "Hoe heet jij?", 2)
        # self.add_move(self.droomrobot.say, "Mike, wat een leuke naam!")
        # self.add_move(self.droomrobot.ask_open, "Wat vind jij leuk om te doen?")
        # self.add_move(self.droomrobot.say, "Dat klikt leuk zeg.")


if __name__ == '__main__':
    sic_app = SICApplication()
    droomrobot = Droomrobot(mini_ip="10.0.0.155", mini_id="00268", mini_password="alphago",
                            redis_ip="10.0.0.204",
                            google_keyfile_path=abspath(join("../../conf", "dialogflow", "google_keyfile.json")),
                            env_path=abspath(join("../../conf", "openai", ".openai_env")),
                            sample_rate_dialogflow_hertz=44100, dialogflow_language="nl",
                            dialogflow_timeout=10.0,
                            tts_conf=ElevenLabsTTSConf(),
                            sic_app=sic_app,
                            computer_test_mode=False)

    script_test = ScriptTest(droomrobot)
    script_test.prepare(participant_id='999', session=InteractionSession.INTRODUCTION, user_model_addendum={
        'kleur': 'paarse'
    })
    script_test.run()
    droomrobot.disconnect()
