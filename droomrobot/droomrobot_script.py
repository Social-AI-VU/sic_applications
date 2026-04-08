import abc
import threading
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from threading import Event
from time import sleep

from droomrobot.core import Droomrobot


class InteractionChoiceNotAvailable(Exception):
    """Raised when the list of move branches does not have a certain choice option available"""
    pass


class InteractionContext(Enum):
    SONDE = 1
    KAPINDUCTIE = 2
    BLOEDAFNAME = 3


class InteractionSession(Enum):
    INTRODUCTION = 1
    INTERVENTION = 2
    GOODBYE = 3


class InterventionPhase(Enum):
    PREPARATION = 1
    PROCEDURE = 2
    WRAPUP = 3


class InteractionChoiceCondition(Enum):
    HASVALUE = 1
    MATCHVALUE = 2
    PHASE = 3


class InteractionMove:
    def __init__(self, func, *args, user_model_key=None, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.user_model_key = user_model_key

    def resolve(self, value):
        return value() if callable(value) else value

    def execute(self):
        func_name = self.func.__name__ if hasattr(self.func, '__name__') else str(self.func)
        print(f"[MOVE] Resolving arguments for {func_name}")
        try:
            if callable(self.func) and not self.args and not self.kwargs:
                # lambda or fully-wrapped func
                print(f"[MOVE] Calling {func_name} with no args")
                return self.func()
            else:
                print(f"[MOVE] Resolving {len(self.args)} args and {len(self.kwargs)} kwargs for {func_name}")
                resolved_args = [self.resolve(arg) for arg in self.args]
                resolved_kwargs = {k: self.resolve(v) for k, v in self.kwargs.items()}
                print(f"[MOVE] Calling {func_name} with {len(resolved_args)} args")
                return self.func(*resolved_args, **resolved_kwargs)
        except Exception as e:
            print(f"[MOVE ERROR] {func_name} failed: {e}")
            raise


class InteractionChoice:

    def __init__(self, target: str, condition: InteractionChoiceCondition):
        self.target = target
        self.condition = condition
        self.moves = {}

    def execute(self, data: dict | str):
        try:
            if self.condition == InteractionChoiceCondition.HASVALUE:
                print(f"[CHOICE] HASVALUE condition: target='{self.target}'")
                print(f"[CHOICE] Available moves: {list(self.moves.keys())}")
                if self.target in data:
                    value = data[self.target]
                    print(f"[CHOICE] Target found in data: {repr(value)[:100]}")
                    if isinstance(data, dict) and data[self.target] is None:
                        print(f"[CHOICE] Target value is None, returning 'fail' moves ({len(self.moves.get('fail', []))} moves)")
                        return self.moves['fail']
                    print(f"[CHOICE] Target value is not None, returning 'success' moves ({len(self.moves.get('success', []))} moves)")
                    return self.moves['success']
                else:
                    print(f"[CHOICE] Target not found in data, returning 'fail' moves ({len(self.moves.get('fail', []))} moves)")
                    return self.moves['fail']
            elif self.condition == InteractionChoiceCondition.MATCHVALUE:
                print(f"[CHOICE] MATCHVALUE condition: target='{self.target}', data={repr(data)[:100]}")
                if self.target in data:
                    if data[self.target] is not None:
                        if data[self.target] in self.moves:
                            print(f"[CHOICE] Returning moves for value '{data[self.target]}'")
                            return self.moves[data[self.target]]
                        else:
                            print(f"[CHOICE] Value not in moves, returning 'other' moves")
                            return self.moves['other']
                print(f"[CHOICE] Target not found or None, returning 'fail' moves")
                return self.moves['fail']
            elif self.condition == InteractionChoiceCondition.PHASE:
                if data in self.moves:
                    return self.moves[data]
                else:
                    raise InteractionChoiceNotAvailable(f"{data} is not available.")
            else:
                raise InteractionChoiceNotAvailable(f"{self.condition} is not available as a condition")
        except KeyError as e:
            print(f"[CHOICE ERROR] KeyError: {e}")
            raise InteractionChoiceNotAvailable(f"{e} is not available.")

    def add_move(self, option: str | list, func, *args, **kwargs):
        options = [option] if isinstance(option, str) else option
        for item in options:
            self.moves.setdefault(item, []).append(InteractionMove(func, *args, **kwargs))

    def add_choice(self, option: str, choice: "InteractionChoice"):
        if option not in self.moves:
            self.moves[option] = []
        self.moves[option].append(choice)


class DroomrobotScript:

    def __init__(self, droomrobot: Droomrobot, interaction_context: InteractionContext):

        # Droomrobot
        self.droomrobot = droomrobot
        self.audio_amplified = False
        self.always_regenerate = False

        # Interaction information
        self.participant_id = None
        self.session = None
        self.interaction_context = interaction_context
        self.user_model = {}

        # Script management
        self.interaction_moves = []
        self.script_idx = 0

        self.is_running = True
        self.pause_event = Event()
        self.pause_event.set()

        self.phases = []
        self.current_phase = 0
        self.phase_moves = None
        self._requested_phase = None

    @abc.abstractmethod
    def prepare(self, participant_id: str, session: InteractionSession, user_model_addendum: dict,
                audio_amplified: bool = False, always_regenerate: bool = False):
        self.participant_id = participant_id
        self.session = session
        self.user_model = self.droomrobot.load_user_model(participant_id=self.participant_id)
        self.user_model.update(user_model_addendum)
        self.audio_amplified = audio_amplified
        self.always_regenerate = always_regenerate

        # Improvement 8 — Skip GPT if article/adjective already stored from a previous session.
        # get_article() and get_adjective() each cost ~1-3s; if the user model already has
        # these values (e.g. from the introduction session), there is no need to ask GPT again.
        needs_article = 'droomplek' in self.user_model and 'droomplek_lidwoord' not in self.user_model
        needs_adjective = 'kleur' in self.user_model and 'kleur_adjective' not in self.user_model

        if needs_article and needs_adjective:
            # Improvement 2 — Both calls are fully independent, run them in parallel.
            # Without this they run sequentially, costing 2-6s total. In parallel
            # the combined cost equals the slower of the two (~1-3s).
            print("[PREPARE] Running get_article and get_adjective in parallel...")
            with ThreadPoolExecutor(max_workers=2) as executor:
                article_future = executor.submit(self.droomrobot.get_article, self.user_model['droomplek'])
                adjective_future = executor.submit(self.droomrobot.get_adjective, self.user_model['kleur'])
                self.user_model['droomplek_lidwoord'] = article_future.result()
                self.user_model['kleur_adjective'] = adjective_future.result()
        elif needs_article:
            self.user_model['droomplek_lidwoord'] = self.droomrobot.get_article(self.user_model['droomplek'])
        elif needs_adjective:
            self.user_model['kleur_adjective'] = self.droomrobot.get_adjective(self.user_model['kleur'])

    def add_move(self, func, *args, **kwargs):
        self.interaction_moves.append(InteractionMove(func, *args, **kwargs))

    def add_choice(self, interaction_choice: InteractionChoice):
        self.interaction_moves.append(interaction_choice)

    def add_moves(self, moves: list):
        self.interaction_moves.extend(moves)

    def _prefetch_next_static_say(self):
        """
        Improvement 5 — Script-level look-ahead TTS pre-fetch.

        After a move completes, scan the upcoming moves for the next say() call whose
        text is a plain static string (not a lambda). If found, kick off TTS synthesis
        in a daemon thread so the audio is cached before that line actually runs.

        This is most effective at transitions between moves where the current move takes
        some time (e.g. dialogflow recognition, GPT call) — the next say() arrives to
        a warm cache with no extra wait.

        Only pre-fetches the immediate next static say() to avoid excessive background
        network calls. Stops scanning at the first InteractionChoice since the branch
        taken is unknown until runtime.
        """
        for i in range(self.script_idx, min(self.script_idx + 5, len(self.interaction_moves))):
            move = self.interaction_moves[i]
            if not isinstance(move, InteractionMove):
                break  # stop at a choice — can't predict which branch will be taken
            if move.func == self.droomrobot.say and move.args and isinstance(move.args[0], str):
                text = move.args[0]
                # Warm cache in a daemon thread so it never blocks the main script
                threading.Thread(
                    target=self.droomrobot.warm_tts_cache,
                    args=([text],),
                    daemon=True,
                    name=f"tts-prefetch-{i}"
                ).start()
                return  # only pre-fetch one line at a time

    def run(self):
        if self.phases and self.phase_moves:
            self.interaction_moves = self.phase_moves.execute(self.phases[self.current_phase])

        self.script_idx = 0
        while self.script_idx < len(self.interaction_moves) and self.is_running:
            self.pause_event.wait()

            # Handle phase switch request BEFORE executing next move
            if self._requested_phase:
                self._switch_to_requested_phase()

            move = self.interaction_moves[self.script_idx]

            if isinstance(move, InteractionMove):
                try:
                    print(f"[SCRIPT] Executing InteractionMove {self.script_idx}: {move.func.__name__ if hasattr(move.func, '__name__') else move.func}")
                    result = move.execute()
                    if move.user_model_key:
                        print(f"[SCRIPT] Storing result in user_model['{move.user_model_key}'] = {repr(result)[:100]}")
                        self.user_model[move.user_model_key] = result
                        self.droomrobot.save_user_model(self.participant_id, self.user_model)
                    self.script_idx += 1
                    # Improvement 5 — pre-fetch TTS for the next static say() in the background
                    self._prefetch_next_static_say()
                except Exception as e:
                    print(f"[SCRIPT ERROR] Move {self.script_idx} failed: {e}")
                    import traceback
                    traceback.print_exc()
                    raise

            elif isinstance(move, InteractionChoice):
                try:
                    print(f"[SCRIPT] Executing InteractionChoice {self.script_idx}: target='{move.target}', condition={move.condition}")
                    print(f"[SCRIPT] Current user_model keys: {list(self.user_model.keys())}")
                    moves = move.execute(self.user_model)
                    print(f"[SCRIPT] InteractionChoice resolved to {len(moves)} moves")
                    self.interaction_moves[self.script_idx:self.script_idx + 1] = moves
                    # Improvement 5 — after resolving a choice, pre-fetch the first static say()
                    # in the newly inserted branch
                    self._prefetch_next_static_say()
                except Exception as e:
                    print(f"[SCRIPT ERROR] Choice {self.script_idx} failed: {e}")
                    import traceback
                    traceback.print_exc()
                    raise

        self.is_running = False
        if self._requested_phase:
            self._switch_to_requested_phase()

    def stop(self):
        self.is_running = False

    def pause(self):
        self.pause_event.clear()

    def resume(self):
        self.pause_event.set()

    def next_phase(self, phase: str):
        if not self.phases or not self.phase_moves:
            raise InteractionChoiceNotAvailable("No phases available.")

        if phase not in self.phases:
            raise InteractionChoiceNotAvailable(f"{phase} is not available.")

        if self.is_running:
            # Request the phase switch
            self._requested_phase = phase
        else:  # restart if not is running anymore
            self.current_phase = self.phases.index(phase)
            self.is_running = True
            self.run()

    def _switch_to_requested_phase(self):
        phase = self._requested_phase
        self._requested_phase = None

        self.interaction_moves = self.phase_moves.execute(phase)
        self.current_phase = self.phases.index(phase)
        self.script_idx = 0

        if not self.is_running:
            self.is_running = True
            self.run()

    def repeat_sentences(self, sentences: list):
        sentence_idx = 0
        while not self._requested_phase and self.is_running:
            total_wait = 5
            interval = 0.1
            waited = 0
            while waited < total_wait:
                if self._requested_phase or not self.is_running:
                    return
                sleep(interval)
                waited += interval
            if not self._requested_phase:
                self.droomrobot.say(sentences[sentence_idx])
                if sentence_idx < len(sentences) - 1:
                    sentence_idx += 1
                else:
                    sentence_idx = 0

    #def set_user_model_variable(self, key: str, value):
    #    self.user_model[key] = value
    
    # Added method to set user model variable and immediately save it to the Droomrobot database    
    def set_user_model_variable(self, key: str, value):
        self.user_model[key] = value
        self.droomrobot.save_user_model(self.participant_id, self.user_model)

    def set_user_model_variables(self, updates: dict):
        self.user_model.update(updates)
        self.droomrobot.save_user_model(self.participant_id, self.user_model)
        
    # Personalisation
    def build_interaction_choice_droomplek(self) -> InteractionChoice:
        interaction_choice = InteractionChoice('droomplek_raw_answer', InteractionChoiceCondition.HASVALUE)

        def _store_first_payload():
            payload = self.droomrobot.generate_droomplek_payload(
                child_name=self.user_model['child_name'],
                child_age=self.user_model['child_age'],
                child_answer=self.user_model['droomplek_raw_answer']
            )
            self.set_user_model_variables({
                'droomplek_speech_text': payload['speech_text'],
                'droomplek_candidate': payload['dream_place_final'],
                'droomplek_candidate_lidwoord': payload['dream_place_article'],
                'place_decided': payload['place_decided'],
            })

        interaction_choice.add_move('success', _store_first_payload)

        first_decision_choice = InteractionChoice('place_decided', InteractionChoiceCondition.MATCHVALUE)

        # CASE 1: first answer is a valid place -> promote and ask for motivation
        def _promote_first_payload():
            self.set_user_model_variables({
                'droomplek': self.user_model['droomplek_candidate'],
                'droomplek_lidwoord': self.user_model['droomplek_candidate_lidwoord'],
            })

        first_decision_choice.add_move([True], _promote_first_payload)
        first_decision_choice.add_move(
            [True],
            self.droomrobot.ask_open,
            lambda: self.user_model['droomplek_speech_text'],
            user_model_key='droomplek_motivatie'
        )

        # CASE 2: first answer vague/inappropriate -> ask once more
        first_decision_choice.add_move(
            [False],
            self.droomrobot.ask_open,
            lambda: self.user_model['droomplek_speech_text'],
            user_model_key='droomplek_second_answer'
        )

        second_answer_choice = InteractionChoice('droomplek_second_answer', InteractionChoiceCondition.HASVALUE)

        def _store_second_payload():
            payload = self.droomrobot.generate_droomplek_payload(
                child_name=self.user_model['child_name'],
                child_age=self.user_model['child_age'],
                child_answer=self.user_model['droomplek_second_answer']
            )
            self.set_user_model_variables({
                'droomplek_speech_text_second': payload['speech_text'],
                'droomplek_candidate_second': payload['dream_place_final'],
                'droomplek_candidate_lidwoord_second': payload['dream_place_article'],
                'place_decided_second': payload['place_decided'],
            })

        second_answer_choice.add_move('success', _store_second_payload)

        second_decision_choice = InteractionChoice('place_decided_second', InteractionChoiceCondition.MATCHVALUE)

        # CASE 2A: second answer is valid -> promote and ask for motivation
        def _promote_second_payload():
            self.set_user_model_variables({
                'droomplek': self.user_model['droomplek_candidate_second'],
                'droomplek_lidwoord': self.user_model['droomplek_candidate_lidwoord_second'],
            })

        second_decision_choice.add_move([True], _promote_second_payload)
        second_decision_choice.add_move(
            [True],
            self.droomrobot.ask_open,
            lambda: self.user_model['droomplek_speech_text_second'],
            user_model_key='droomplek_motivatie'
        )

        # CASE 2B: second answer still not valid -> fallback to strand
        def _store_strand_fallback():
            self.set_user_model_variables({
                'droomplek': 'strand',
                'droomplek_lidwoord': 'het',
                'droomplek_speech_text_final': (
                    'Zullen we anders naar het strand? Ik vind dat altijd zo een fijne plek. '
                    'Ik kan de golven bijna horen en het zand onder mijn voeten voelen. '
                    'Weet je wat ik daar graag doe? Een zandkasteel bouwen met een vlag er op. '
                    f"Wat zou jij op het strand willen doen {self.user_model['child_name']}?"
                ),
                'place_decided': True,
                'place_decided_second': True,
            })

        second_decision_choice.add_move([False], _store_strand_fallback)
        second_decision_choice.add_move(
            [False],
            self.droomrobot.ask_open,
            lambda: self.user_model['droomplek_speech_text_final'],
            user_model_key='droomplek_motivatie'
        )

        second_answer_choice.add_choice('success', second_decision_choice)

        # Second answer missing entirely -> fallback to strand
        second_answer_choice.add_move('fail', _store_strand_fallback)
        second_answer_choice.add_move(
            'fail',
            self.droomrobot.ask_open,
            lambda: self.user_model['droomplek_speech_text_final'],
            user_model_key='droomplek_motivatie'
        )

        true_case_terminal = InteractionChoice('child_name', InteractionChoiceCondition.HASVALUE)
        true_case_terminal.add_move('success', lambda: None)
        first_decision_choice.add_choice(True, true_case_terminal)

        first_decision_choice.add_choice(False, second_answer_choice)
        interaction_choice.add_choice('success', first_decision_choice)

        # First answer missing entirely -> fallback to strand
        interaction_choice.add_move('fail', _store_strand_fallback)
        interaction_choice.add_move(
            'fail',
            self.droomrobot.ask_open,
            lambda: self.user_model['droomplek_speech_text_final'],
            user_model_key='droomplek_motivatie'
        )

        return interaction_choice

    def build_imagery_store_move(self):
        """Returns an InteractionMove that generates and stores the full imagery payload after droomplek_motivatie is known."""
        def _store_imagery_payload():
            payload = self.droomrobot.generate_droomplek_imagery_payload(
                child_name=self.user_model['child_name'],
                child_age=self.user_model['child_age'],
                droomplek=self.user_model['droomplek'],
                droomplek_article=self.user_model['droomplek_lidwoord'],
                motivatie=self.user_model.get('droomplek_motivatie', ''),
            )
            self.set_user_model_variables({
                'transition_sentence': payload['transition_sentence'],
                'guided_imagery_seed': payload['guided_imagery_seed'],
                'guided_imagery_seed_2': payload['guided_imagery_seed_2'],
                'intervention_preparation_sentences': payload['intervention_preparation_sentences'],
                'intervention_procedure_sentences': payload['intervention_procedure_sentences'],
            })
        return InteractionMove(_store_imagery_payload)
    


