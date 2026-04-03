from sic_framework.services.llm import GPTRequest

from droomrobot.core import AnimationType, InteractionConf
from droomrobot.droomrobot_script import DroomrobotScript, InteractionContext, InteractionSession, InterventionPhase, \
    InteractionChoice, InteractionChoiceCondition
from droomrobot.introduction_factory import IntroductionFactory


class Bloedafname6(DroomrobotScript):

    def __init__(self, *args, **kwargs):
        super(Bloedafname6, self).__init__(*args, **kwargs, interaction_context=InteractionContext.BLOEDAFNAME)

    def prepare(self, participant_id: str, session: InteractionSession, user_model_addendum: dict,
                audio_amplified: bool = False, always_regenerate: bool = False):
        super().prepare(participant_id, session, user_model_addendum, audio_amplified, always_regenerate)
        if session == InteractionSession.INTRODUCTION:
            self._introduction()
        elif session == InteractionSession.INTERVENTION:
            self._intervention()
        elif session == InteractionSession.GOODBYE:
            self._goodbye()
        else:
            print("Interaction part not recognized")

    def _introduction(self):
        # Introductie uitleg robot + dier
        interaction_conf = InteractionConf(amplified=self.audio_amplified, always_regenerate=self.always_regenerate)
        self.add_move(self.droomrobot.set_interaction_conf, interaction_conf)
        intro_moves = IntroductionFactory.age6_9(droomrobot=self.droomrobot,
                                                   interaction_context=self.interaction_context,
                                                   user_model=self.user_model)
        self.add_moves(intro_moves)
        
        # Personalisatie droomplek keuze (her-vraag als nodig) 
        self.add_move(
            self.droomrobot.ask_open,
            'Wat is een plek waar jij je fijn voelt?',
            user_model_key='droomplek_raw_answer'
        )
        self.add_choice(self.build_interaction_choice_droomplek())

        # Opslaan van de gegenereerde personalisatie (plek + motivatie) in het user model
        self.add_moves([self.build_imagery_store_move()])

        # Gepersonaliseerde overgang van plek&motivatie vragen naar het oefenen van de droomreis + checken positie kind
        interaction_conf = InteractionConf(speaking_rate=0.75, sleep_time=0.5, animated=False, amplified=self.audio_amplified, always_regenerate=self.always_regenerate)
        self.add_move(self.droomrobot.set_interaction_conf, interaction_conf)
        self.add_move(self.droomrobot.say, lambda: self.user_model['transition_sentence'])
        self.add_choice(self._build_interaction_choice_comfortable_position())

        # Personalisatie oefenen droomreis
        self.add_move(
            self.droomrobot.say,
            lambda: self.user_model['guided_imagery_seed']
        )
        
        # Oefenen van de ademhaling + personalisatie van het lichtje
        self.add_move(self.droomrobot.say, 'Adem diep in door je neus.')
        self.add_move(self.droomrobot.play_audio, 'resources/audio/breath_in.wav')
        self.add_move(self.droomrobot.say, 'en blaas langzaam uit door je mond.')
        self.add_move(self.droomrobot.play_audio, 'resources/audio/breath_out.wav')
        self.add_move(self.droomrobot.say, lambda: f'Goed zo dat gaat al heel goed {self.user_model['child_name']}.')
        self.add_move(self.droomrobot.say,
                      lambda: f'En terwijl je zo goed aan het ademen bent, stel je voor dat er een klein, warm lichtje op je {self.user_model['priklocatie']} verschijnt.')
        self.add_move(self.droomrobot.say, 'Dat lichtje is magisch en laadt jouw kracht op.')
        self.add_move(self.droomrobot.say, 'Stel je eens voor hoe dat lichtje eruit ziet.')
        self.add_move(self.droomrobot.say, 'Is het geel, blauw of misschien jouw lievelingskleur?')
        
        self.add_move(self.droomrobot.ask_entity_llm, 'Welke kleur heeft jouw lichtje?', strict=True,
                      user_model_key='kleur')
        
        kleur_choice = InteractionChoice('kleur', InteractionChoiceCondition.HASVALUE)
        kleur_choice.add_move('success', self.droomrobot.say, lambda: f'{self.user_model['kleur']}, wat goed, die heb je goed gekozen, {self.user_model['child_name']}.')
        kleur_choice.add_move('fail', self.droomrobot.say, 'Sorry, dat verstond ik even niet goed. Weet je wat? Ik vind groen een mooie kleur. Laten we het lichtje groen maken.')
        kleur_choice.add_move('fail', lambda: self.set_user_model_variable('kleur', 'groen'))
        self.add_choice(kleur_choice)
        self.add_move(self.droomrobot.get_adjective, lambda: self.user_model['kleur'], user_model_key='kleur_adjective')
        self.add_move(self.droomrobot.say, lambda: f'Merk maar eens hoe dat {self.user_model['kleur_adjective']} lichtje je een heel fijn, krachtig gevoel geeft.')
        self.add_move(self.droomrobot.say,
                      'En iedere keer als je het nodig hebt, kun je zoals je nu geleerd hebt, een paar keer diep in en uit ademen.')
        self.add_move(self.droomrobot.say,
                      'Hartstikke goed, ik ben benieuwd hoe goed het lichtje je zometeen gaat helpen.')
        self.add_move(self.droomrobot.say,
                      'Als je je ogen lekker dicht had mag je ze nu weer open doen',
                      sleep_time=2)

        # Goodbye introductie
        interaction_conf = InteractionConf(amplified=self.audio_amplified, always_regenerate=self.always_regenerate)
        self.add_move(self.droomrobot.set_interaction_conf, interaction_conf)

        self.add_move(self.droomrobot.say, 'Gelukkig wordt het steeds makkelijker als je het vaker oefent.')
        self.add_move(self.droomrobot.say, 'Ik ben benieuwd hoe goed het zometeen gaat.')
        self.add_move(self.droomrobot.say, 'Je zult zien dat dit je gaat helpen.')
        self.add_move(self.droomrobot.say,
                      'Als je zometeen aan de beurt bent, ga ik je helpen om het lichtje weer samen aan te zetten, zodat je weer die superheld bent.')

        self.add_move(self.droomrobot.animate, AnimationType.ACTION, "random_short4", run_async=True) ## Wave right hand
        self.add_move(self.droomrobot.animate, AnimationType.EXPRESSION, "emo_007", run_async=True) ## Smile
        self.add_move(self.droomrobot.say, 'Tot straks, doei!')

    def _intervention(self):
        self.phases = [
            InterventionPhase.PREPARATION.name,
            InterventionPhase.PROCEDURE.name,
            InterventionPhase.WRAPUP.name
        ]
        self.phase_moves_build = InteractionChoice('Bloedafname6', InteractionChoiceCondition.PHASE)
        self.phase_moves_build = self._intervention_preparation(self.phase_moves_build)
        self.phase_moves_build = self._intervention_procedure(self.phase_moves_build)
        self.phase_moves = self._intervention_wrapup(self.phase_moves_build)

    def _intervention_preparation(self, phase_moves: InteractionChoice) -> InteractionChoice:
        interaction_conf = InteractionConf(speaking_rate=0.75, sleep_time=0.5, animated=False, amplified=self.audio_amplified, always_regenerate=self.always_regenerate)
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.set_interaction_conf, interaction_conf)
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.animate, AnimationType.ACTION,
                             "random_short4", run_async=True)
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.animate, AnimationType.EXPRESSION,
                             "emo_007", run_async=True)
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.say,
                             lambda: f'Wat fijn dat ik je weer mag helpen, we gaan weer samen een droomreis naar {self.user_model["droomplek_lidwoord"]} {self.user_model["droomplek"]} maken.')
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.say,
                             'Omdat je net al zo goed hebt geoefend, zul je zien dat het nu nog beter, en makkelijker gaat.')
        position_choice = InteractionChoice('positie', InteractionChoiceCondition.MATCHVALUE)
        position_choice.add_move('zittend', self.droomrobot.say,
                             'Je mag weer goed gaan zitten, en als je wilt je ogen dicht doen zodat deze droomreis nog beter voor jou werkt.', sleep_time=1)
        position_choice.add_move('liggend', self.droomrobot.say,
                                 'Je mag weer goed gaan liggen, en als je wilt je ogen dicht doen zodat deze droomreis nog beter voor jou werkt.',
                                 sleep_time=1)
        position_choice.add_move('other', self.droomrobot.say,
                                 'Je mag weer lekker voelen dat je in deze kamer bent, en als je wilt je ogen dicht doen, zodat deze droomreis nog beter voor jou werkt',
                                 sleep_time=1)
        phase_moves.add_choice(InterventionPhase.PREPARATION.name, position_choice)
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.say,
                             'Luister maar weer goed naar mijn stem, en merk maar dat andere geluiden in het ziekenhuis veel stiller worden.')
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.say,
                             'Ga maar rustig ademen, zoals je dat gewend bent.')
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.say, 'Adem rustig in.')
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.play_audio,
                             'resources/audio/breath_in_amplified.wav')
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.say, 'en rustig uit.')
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.play_audio,
                             'resources/audio/breath_out_amplified.wav')
        # Personalisatie van droomreis in voorbereiding op procedure
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.say,
                             lambda: f'Stel je maar voor dat je bij {self.user_model["droomplek_lidwoord"]} {self.user_model["droomplek"]} bent.')
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.droomrobot.say,
                             lambda: self.user_model['guided_imagery_seed_2'])
        phase_moves.add_move(InterventionPhase.PREPARATION.name, self.repeat_sentences,
                             lambda: self.user_model['intervention_preparation_sentences'])
        return phase_moves

    def _intervention_procedure(self, phase_moves: InteractionChoice) -> InteractionChoice:
        interaction_conf = InteractionConf(speaking_rate=0.75, sleep_time=0.5, animated=False, amplified=self.audio_amplified, always_regenerate=self.always_regenerate)
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.set_interaction_conf, interaction_conf)

        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say,
                             'Nu gaan we je lichtje weer activeren zoals je dat geleerd hebt.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say, 'Adem in via je neus.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.play_audio,
                             'resources/audio/breath_in_amplified.wav')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say, 'en blaas rustig uit via je mond.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.play_audio,
                             'resources/audio/breath_out_amplified.wav')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say,
                             lambda: f'En kijk maar hoe je krachtige {self.user_model['kleur_adjective']} lichtje weer op je {self.user_model['priklocatie']} verschijnt, in precies de goede kleur die je nodig hebt.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say,
                             'Zie het lichtje steeds sterker en krachtiger worden.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say,
                             'Zodat jij weer een superheld wordt en jij jezelf kan helpen.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say,
                             lambda: f'En als je het nodig hebt, stel je voor dat je {self.user_model['kleur_adjective']} lichtje nog helderder gaat schijnen.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say,
                             'Dat betekent dat jouw kracht helemaal wordt opgeladen.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say,
                             'Als het nodig is, kan je de kracht nog groter maken door met je tenen te wiebelen.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say,
                             'Het geeft een veilige en zachte gloed om je te helpen.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say,
                             lambda: f'Als je iets voelt op je {self.user_model['priklocatie']}, dan is dat een teken dat je lichtje volledig werkt.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say, 'Adem diep in.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.play_audio,
                             'resources/audio/breath_in_amplified.wav')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say, 'en blaas uit.')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.play_audio,
                             'resources/audio/breath_out_amplified.wav')
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.droomrobot.say,
                             'Merk maar hoe goed jij jezelf kan helpen, je bent echt een superheld.')
        # Personalisatie van de procedure
        phase_moves.add_move(InterventionPhase.PROCEDURE.name, self.repeat_sentences,
                             lambda: self.user_model['intervention_procedure_sentences'])
        return phase_moves

    def _intervention_wrapup(self, phase_moves: InteractionChoice) -> InteractionChoice:
        interaction_conf = InteractionConf(amplified=self.audio_amplified, always_regenerate=self.always_regenerate)
        phase_moves.add_move(InterventionPhase.WRAPUP.name, self.droomrobot.set_interaction_conf, interaction_conf)
        phase_moves.add_move(InterventionPhase.WRAPUP.name, self.droomrobot.say, 'Dat was het weer.')
        phase_moves.add_move(InterventionPhase.WRAPUP.name, self.droomrobot.say, 'Bedankt dat ik je mocht helpen vandaag.')
        phase_moves.add_move(InterventionPhase.WRAPUP.name, self.droomrobot.say, 'Je hebt jezelf heel goed geholpen!.')
        phase_moves.add_move(InterventionPhase.WRAPUP.name, self.droomrobot.animate, AnimationType.ACTION, "random_short4", run_async=True) ## Wave right hand
        phase_moves.add_move(InterventionPhase.WRAPUP.name, self.droomrobot.animate, AnimationType.EXPRESSION, "emo_007", run_async=True) ## Smile
        phase_moves.add_move(InterventionPhase.WRAPUP.name, self.droomrobot.say, lambda: f'Doei doei {self.user_model['child_name']}', animated=False)
        return phase_moves

    def _goodbye(self):
        pass


    # OLD: _build_interaction_choice_droomplek — replaced by build_interaction_choice_droomplek in droomrobot_script.py

    def _build_interaction_choice_comfortable_position(self) -> InteractionChoice:
        position_choice = InteractionChoice('positie', InteractionChoiceCondition.MATCHVALUE)

        # Zittend
        position_choice.add_move('zittend', self.droomrobot.say, 'Ga even lekker zitten zoals jij dat fijn vindt.', sleep_time=1)
        position_choice.add_move('zittend', self.droomrobot.ask_yesno, "Zit je zo goed?", user_model_key='zit_goed')

        zit_goed_choice = InteractionChoice('zit_goed', InteractionChoiceCondition.MATCHVALUE)
        zit_goed_choice.add_move('yes', self.droomrobot.say, 'En nu je lekker bent gaan zitten.')
        zit_goed_choice.add_move(['other', 'fail'], self.droomrobot.say,
                                 'Het zit vaak het lekkerste als je stevig gaat zitten.')
        zit_goed_choice.add_move(['other', 'fail'], self.droomrobot.say, 'Ga maar eens kijken hoe goed dat zit.',
                                 sleep_time=1)
        zit_goed_choice.add_move(['other', 'fail'], self.droomrobot.say, 'Als je goed zit.')
        position_choice.add_choice('zittend', zit_goed_choice)
        position_choice.add_move('zittend', self.droomrobot.say, 'mag je als je wilt je ogen dicht doen.')
        position_choice.add_move('zittend', self.droomrobot.say, 'dan werkt het truukje het beste.', sleep_time=1)

        # Liggend
        position_choice.add_move('liggend', self.droomrobot.say, 'Ga even lekker liggen zoals jij dat fijn vindt.', sleep_time=1)
        position_choice.add_move('liggend', self.droomrobot.ask_yesno, "Lig je zo goed?", user_model_key='zit_goed')

        zit_goed_choice = InteractionChoice('zit_goed', InteractionChoiceCondition.MATCHVALUE)
        zit_goed_choice.add_move('yes', self.droomrobot.say, 'En nu je lekker bent gaan liggen.')
        zit_goed_choice.add_move(['other', 'fail'], self.droomrobot.say, 'Het ligt vaak het lekkerste als je je lichaam zwaar maakt, ga maar eens kijken hoe goed dat ligt')
        zit_goed_choice.add_move(['other', 'fail'], self.droomrobot.say, 'Als je goed ligt.')
        position_choice.add_choice('liggend', zit_goed_choice)
        position_choice.add_move('liggend', self.droomrobot.say, 'mag je als je wilt je ogen dicht doen.')
        position_choice.add_move('liggend', self.droomrobot.say, 'dan werkt het truukje het beste.', sleep_time=1)

        # NVT
        position_choice.add_move('other', self.droomrobot.say, 'Terwijl je hier zo in de kamer bent mag je je ogen dicht doen als je wilt,')
        position_choice.add_move('other', self.droomrobot.say, 'dan werkt het truukje het beste.', sleep_time=1)

        return position_choice
