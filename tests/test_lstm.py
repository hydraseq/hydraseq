import re
import sys
sys.path.append('./hydraseq')
import hydraseq
from columns import MiniColumn

def test_mini_column():
    sentence = "spring leaves spring"
    source_files = ["seasons.0.txt", "seasons.1.txt", "seasons.2.txt"]
    mcol = MiniColumn(source_files, "tests/data")
    mcol.get_state()
    assert mcol.compute_convolutions(sentence).convolutions == [[[0, 1, ['0_ADJ', '0_NOU', '0_VER']],
        [1, 2, ['0_NOU', '0_VER']],
        [2, 3, ['0_ADJ', '0_NOU', '0_VER']]],
        [[0, 1, ['1_NP', '1_VP']],
        [0, 2, ['1_NP', '1_VP']],
        [1, 2, ['1_NP', '1_VP']],
        [1, 3, ['1_VP']],
        [2, 3, ['1_NP', '1_VP']]],
        [[0, 2, ['2_SENT']],
        [1, 3, ['2_SENT']],
        [2, 4, ['2_SENT']],
        [3, 5, ['2_SENT']]]]



