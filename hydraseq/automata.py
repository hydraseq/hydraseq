import hydraseq as hd

def convert_to_mermaid(lst_transitions):
    """Takes a 'st1 a st2' list of transitions and generates a mermaid compatible
        string like 'st1((st1)) --a--> st2((st2))' """
    def convert_line(str_line):
        start, action, final = str_line.split()
        final = final.replace('^', '')
        return "{}(({})) --{}--> {}(({}))".format(start, start, action, final, final)
    return "\n".join([convert_line(line) for line in lst_transitions])

class DFAstate:
    def __init__(self, transitions, init_state):
        self.states = hd.Hydraseq('_')
        self.init_state = init_state
        [self.states.insert(transition) for transition in transitions]
        self.reset()

    def get_active_states(self):
        return self.states.get_active_values()

    def reset(self, init_state=None):
        self.states.look_ahead(init_state if init_state else self.init_state)
        return self

    def event(self, e):
        self.states.hit([e], is_learning=False)
        for action in self.states.get_next_values():
            self.states.look_ahead(action.replace('^', ''))
        return self

    def __str__(self):
        return "DFA state: {}, preds: {}".format(self.states.get_active_values(), self.states.get_next_values())


if __name__ == "__main__":
    transitions = [
        "s1 a ^s2",
        "s1 b ^s1",
        "s2 a ^s2",
        "s2 b ^s3",
        "s3 a ^s3",
        "s3 b ^s3"
    ]
    dfa = DFAstate(transitions, 's1')
    print(dfa)
    for letter in "bbabba":
        print(letter, dfa.event(letter))