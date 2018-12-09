import hydraseq as hd

class DFAsimple:
    def __init__(self):
        self.states = hd.Hydraseq('_D')
        self.states.insert('_S1 _S2')
        self.states.insert('_S2 _S1')
        self.states.look_ahead('_S1')

        self.sensor = hd.Hydraseq('_S')
        self.sensor.insert('a _S1')
        self.sensor.insert('a _S2')

    def state(self):
        return self.states.get_active_values()

    def event(self, e):
        predicted = self.states.get_next_values()
        output = self.sensor.insert(e).get_next_values()
        self.states.look_ahead([list(set(predicted) & set(output))])
        return self


class DFAstate:
    def __init__(self):
        self.states = hd.Hydraseq('_D')
        for transition in [
            "s1 a ^s2",
            "s1 b ^s1",
            "s2 a ^s2",
            "s2 b ^s3",
            "s3 a ^s3",
            "s3 b ^s3"
        ]:
            self.states.insert(transition)

        self.states.look_ahead('s1')

    def state(self):
        return self.states.get_active_values()

    def event(self, e):
        self.states.hit([e], is_learning=False)
        for action in self.states.get_next_values():
            self.states.look_ahead(action.replace('^', ''))

        return self

    def __str__(self):
        return "DFA state: {}, preds: {}".format(self.states.get_active_values(), self.states.get_next_values())

dfa = DFAstate()
print(dfa)
for letter in "bbabba":
    print(letter, dfa.event(letter))
    def __str__(self):
        return "DFA state: {}".format(self.states.get_active_values())