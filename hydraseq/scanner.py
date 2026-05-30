"""
PatternScanner: sliding-window sequence pattern recognition built on Hydraseq.

Usage pattern:
    1. Build an encoder: a callable that maps a raw token (str) -> list[str] of category labels
    2. Train a Hydraseq on sequences of those category labels capped with a concept token
    3. Wrap both in PatternScanner
    4. Call get_markers(sentence, targets) to find spans that resolve to concept tokens
    5. Call get_paths(markers) to chain non-overlapping spans into full parses
"""

from collections import namedtuple

Marker = namedtuple('Marker', ['start', 'end', 'length', 'labels', 'text'])


class LayeredScanner:
    """Stack multiple PatternScanners so each layer's output labels become the
    next layer's input tokens.

    Usage pattern:
        1. Build N PatternScanners, each trained on sequences from its level
        2. Provide intermediate target labels that each layer should resolve to
        3. Call scan(tokens, final_targets) — output is Markers from the top layer

    The path chosen between layers is the one that covers the longest span,
    which favours the most complete parse at each level.
    """

    def __init__(self, layers, intermediate_targets):
        """
        Args:
            layers:                 list of PatternScanner, ordered bottom to top
            intermediate_targets:   list of target label lists, one per layer except
                                    the last (those are passed to scan() instead)
        """
        assert len(intermediate_targets) == len(layers) - 1, \
            "Need one intermediate_targets entry per layer except the last"
        self.layers = layers
        self.intermediate_targets = intermediate_targets

    def scan(self, tokens, final_targets):
        """Run the full layer stack and return top-level Markers.

        Args:
            tokens:         str or list[str] of raw input tokens
            final_targets:  list[str] of concept labels the top layer should find

        Returns:
            list of Marker namedtuples from the top layer
        """
        current = tokens if isinstance(tokens, list) else tokens.lower().split()

        for scanner, targets in zip(self.layers[:-1], self.intermediate_targets):
            markers = scanner.get_markers(current, targets)
            if not markers:
                return []
            paths = scanner.get_paths(markers)
            if not paths:
                return []
            # pick the path covering the longest span
            best = max(paths, key=lambda p: p[-1].end - p[0].start)
            # labels of each marker in the best path become tokens for the next layer
            current = [m.labels[0] for m in best]

        return self.layers[-1].get_markers(current, final_targets)


class PatternScanner:
    def __init__(self, seq, encoder, tokenizer=None):
        """
        Args:
            seq:        a trained Hydraseq instance
            encoder:    callable(token: str) -> list[str] of category labels
            tokenizer:  optional callable(sentence: str) -> list[str] of tokens
                        defaults to lowercase whitespace split
        """
        self.seq = seq
        self.encoder = encoder
        self.tokenizer = tokenizer or (lambda s: s.lower().strip().split())

    def get_markers(self, sentence, targets):
        """Slide a window over every span of the sentence and return spans that
        predict one of the target concept labels.

        Args:
            sentence:   str or list[str] of tokens
            targets:    list[str] of concept labels to look for (e.g. ['ADDRESS'])

        Returns:
            list of Marker namedtuples: (start, end, length, labels, text)
        """
        tokens = self.tokenizer(sentence) if isinstance(sentence, str) else sentence
        markers = []
        for idx_beg in range(len(tokens)):
            for idx_end in range(idx_beg + 1, len(tokens) + 1):
                encoded = [self.encoder(t) for t in tokens[idx_beg:idx_end]]
                next_values = self.seq.look_ahead(encoded).get_next_values()
                matches = list(set(next_values) & set(targets))
                if matches:
                    markers.append(Marker(
                        start=idx_beg,
                        end=idx_end,
                        length=idx_end - idx_beg,
                        labels=matches,
                        text=' '.join(tokens[idx_beg:idx_end])
                    ))
        return markers

    def get_paths(self, markers):
        """Chain non-overlapping markers into all possible complete paths using BFS.

        Each path is a list of Markers that tile end-to-end with no gaps and no
        type repetition between adjacent markers.

        Args:
            markers:    list of Marker namedtuples (output of get_markers)

        Returns:
            list of paths, where each path is a list of Markers
        """
        def get_successors(marker, all_markers):
            return [m for m in all_markers if m.start == marker.end]

        all_paths = []
        for marker in markers:
            fringe = [[marker]]
            while fringe:
                path = fringe.pop()
                successors = get_successors(path[-1], markers)
                if successors:
                    for s in successors:
                        fringe.append(path + [s])
                else:
                    all_paths.append(path)
        return all_paths
