import re
import sys
sys.path.append('./hydraseq')
import hydraseq
from minicolumn import MiniColumn

def test_mini_column():
    sentence = "spring leaves spring"
    source_files = ["seasons.0.txt", "seasons.1.txt", "seasons.2.txt"]
    mcol = MiniColumn(source_files, "tests/data")

    ctree = mcol.compute_convolution_tree("spring leaves spring")
    assert ctree == \
[
    [
        {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1},
        {'words': [['leaves']], 'convo': ['0_NOU', '0_VER'], 'start': 1, 'end': 2},
        {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 2, 'end': 3}
    ],
    [
        [
            [
                {'words': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 1},
                {'words': [['0_NOU', '0_VER'], ['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_VP'], 'start': 1, 'end': 3}
            ],
            [
                [
                    [
                        {'words': [['1_NP', '1_VP'], ['1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2}
                    ]
                ]
            ]
        ],
        [
            [
                {'words': [['0_ADJ', '0_NOU', '0_VER'], ['0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 2},
                {'words': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 2, 'end': 3}
            ],
            [
                [
                    [
                        {'words': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2}
                    ]
                ]
            ]
        ],
        [
            [
                {'words': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 1},
                {'words': [['0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 1, 'end': 2},
                {'words': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 2, 'end': 3}
            ],
            [
                [
                    [
                        {'words': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2}
                    ]
                ],
                [
                    [
                        {'words': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 1, 'end': 3}
                    ]
                ]
            ]
        ]
    ]
]

def test_reverse_convo():
    source_files = ['face.0.txt', 'face.1.txt', 'face.2.txt']
    mcol = MiniColumn(source_files, 'tests/data')

    assert mcol.reverse_convo("2_FACE") == ['db', 'o', 'u', 'v']

def test_output_to_tree_nodes():
    sentence = "spring leaves spring"
    source_files = ["seasons.0.txt", "seasons.1.txt", "seasons.2.txt"]
    mcol = MiniColumn(source_files, "tests/data")

    convolutions = mcol.hydras[0].convolutions(sentence)
    assert convolutions == [
        {'convo': ['0_ADJ', '0_NOU', '0_VER'], 'end': 1, 'start': 0, 'words': [['spring']]},
        {'convo': ['0_NOU', '0_VER'],          'end': 2, 'start': 1, 'words': [['leaves']]},
        {'convo': ['0_ADJ', '0_NOU', '0_VER'], 'end': 3, 'start': 2, 'words': [['spring']]}
    ]

    assert mcol.patterns_only(convolutions) == [
        ['0_ADJ', '0_NOU', '0_VER'], ['0_NOU', '0_VER'], ['0_ADJ', '0_NOU', '0_VER']
    ]

    assert mcol.resolve_convolution(convolutions)[0] == [
            {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1},
            {'words': [['leaves']], 'convo': ['0_NOU', '0_VER'],          'start': 1, 'end': 2},
            {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 2, 'end': 3}
        ]

    result = mcol.to_tree_nodes(convolutions)
    assert result == [
        {
            'words': [['spring']],
            'convo': ['0_ADJ', '0_NOU', '0_VER'],
            'start': 2,
            'end': 3,
            'lasts': [
                {
                    'words': [['leaves']],
                    'convo': ['0_NOU', '0_VER'],
                    'start': 1,
                    'end': 2,
                    'lasts': [
                        {
                            'words': [['spring']],
                            'convo': ['0_ADJ', '0_NOU', '0_VER'],
                            'start': 0,
                            'end': 1,
                            'lasts': []
                        }
                    ]
                }
            ]
        }
    ]

    assert mcol.reconstruct(result) == [
        [
            {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1},
            {'words': [['leaves']], 'convo': ['0_NOU', '0_VER'],          'start': 1, 'end': 2},
            {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 2, 'end': 3}
        ]
    ]