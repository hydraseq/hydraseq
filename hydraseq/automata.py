"""
Deterministic Finite Automata
Examples taken from Understanding Computation Chapter 2

Conversion to mermaid cretes directly graphable in html using mermaidjs
"""
import hydraseq as hd

class DFAstate:
    def __init__(self, transitions, init_state, accepting_states=[]):
        self.states = hd.Hydraseq('_')
        self.init_state = init_state
        self.acceptings = accepting_states
        self.transitions = transitions
        [self.states.insert(transition) for transition in transitions]
        self.reset()

    def get_active_states(self):
        return self.states.get_active_values()

    def in_accepting(self):
        """Return True if current state is one of accepting states"""
        return any([state in self.acceptings for state in self.states.get_active_values()])

    def reset(self, init_state=None):
        self.states.look_ahead(init_state if init_state else self.init_state)
        return self

    def event(self, e):
        self.states.hit([e], is_learning=False)
        for action in self.states.get_next_values():
            self.states.look_ahead(action.replace('^', ''))
        return self

    def read_string(self, str):
        self.reset()
        [self.event(char) for char in str]
        return self

    def convert_to_mermaid(self):
        """Takes a 'st1 a st2' list of transitions and generates a mermaid compatible
            string like 'st1((st1)) --a--> st2((st2))' """
        def _convert_line(str_line):
            start, action, final = str_line.split()
            final = final.replace('^', '')
            return "{}(({})) --{}--> {}(({}))".format(start, start, action, final, final)

        return "\n".join([_convert_line(line) for line in self.transitions])

    def __str__(self):
        return "DFA state: {}, preds: {}".format(self.states.get_active_values(), self.states.get_next_values())
