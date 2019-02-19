import re
import sys
sys.path.append('./hydraseq')
import hydraseq
from minicolumn import MiniColumn

def test_mini_column():
    sentence = "spring leaves spring"
    source_files = ["seasons.0.txt", "seasons.1.txt", "seasons.2.txt"]
    mcol = MiniColumn(source_files, "tests/data")

    assert mcol.compute_convolution_tree_obj("spring leaves spring") == [
        {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1, 'nexts': []},
        {'words': [['leaves']], 'convo': ['0_NOU', '0_VER'],          'start': 1, 'end': 2, 'nexts': []},
        {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 2, 'end': 3, 'nexts': []},
        [
            [
                {'words': [['0_ADJ', '0_NOU', '0_VER']],                     'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 1, 'nexts': []},
                {'words': [['0_NOU', '0_VER'], ['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_VP'],         'start': 1, 'end': 3, 'nexts': []},
                [
                    [
                        {'words': [['1_NP', '1_VP'], ['1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2, 'nexts': []}
                    ]
                ]
           ],
           [
               {'words': [['0_ADJ', '0_NOU', '0_VER'], ['0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 2, 'nexts': []},
               {'words': [['0_ADJ', '0_NOU', '0_VER']],                     'convo': ['1_NP', '1_VP'], 'start': 2, 'end': 3, 'nexts': []},
               [
                   [
                       {'words': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2, 'nexts': []}
                   ]
               ]
           ],
           [
               {'words': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 1, 'nexts': []},
               {'words': [['0_NOU', '0_VER']],          'convo': ['1_NP', '1_VP'], 'start': 1, 'end': 2, 'nexts': []},
               {'words': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 2, 'end': 3, 'nexts': []},
               [
                    [
                        {'words': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2, 'nexts': []}
                    ],
                    [
                        {'words': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 1, 'end': 3, 'nexts': []}
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

    assert mcol.hydras[0].convolutions(sentence, as_json=True) == [
        {'convo': ['0_ADJ', '0_NOU', '0_VER'], 'end': 1, 'start': 0, 'words': [['spring']]},
        {'convo': ['0_NOU', '0_VER'],          'end': 2, 'start': 1, 'words': [['leaves']]},
        {'convo': ['0_ADJ', '0_NOU', '0_VER'], 'end': 3, 'start': 2, 'words': [['spring']]}
    ]


    print("BLOWUP HERE:",mcol.resolve_convolution_obj(mcol.hydras[0].convolutions(sentence, as_json=True))[0])
    assert mcol.resolve_convolution_obj(mcol.hydras[0].convolutions(sentence, as_json=True))[0] == [
            {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1, 'nexts': []},
            {'words': [['leaves']], 'convo': ['0_NOU', '0_VER'],          'start': 1, 'end': 2, 'nexts': []},
            {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 2, 'end': 3, 'nexts': []}
        ]

    result = mcol.to_tree_nodes_obj(mcol.hydras[0].convolutions(sentence, as_json=True))
    assert mcol.to_tree_nodes_obj(mcol.hydras[0].convolutions(sentence, as_json=True)) == [
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
                            'lasts': [],
                            'nexts': []
                        }
                    ],
                    'nexts': []
                }
            ],
            'nexts': []
        }
    ]

    final = mcol.reconstruct_obj(result)  # TODO: The fight is here, this has to not retrn lasts
    print("FINAL:",final)
    assert mcol.reconstruct_obj(result) == [
        [
            {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1, 'nexts': []},
            {'words': [['leaves']], 'convo': ['0_NOU', '0_VER'],          'start': 1, 'end': 2, 'nexts': []},
            {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 2, 'end': 3, 'nexts': []}
        ]
    ]

    assert mcol.compute_convolution_tree_obj("spring leaves spring") == [
        {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1, 'nexts': []},
        {'words': [['leaves']], 'convo': ['0_NOU', '0_VER'],          'start': 1, 'end': 2, 'nexts': []},
        {'words': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 2, 'end': 3, 'nexts': []},
        [
            [
                {'words': [['0_ADJ', '0_NOU', '0_VER']],                     'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 1, 'nexts': []},
                {'words': [['0_NOU', '0_VER'], ['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_VP'],         'start': 1, 'end': 3, 'nexts': []},
                [
                    [
                        {'words': [['1_NP', '1_VP'], ['1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2, 'nexts': []}
                    ]
                ]
           ],
           [
               {'words': [['0_ADJ', '0_NOU', '0_VER'], ['0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 2, 'nexts': []},
               {'words': [['0_ADJ', '0_NOU', '0_VER']],                     'convo': ['1_NP', '1_VP'], 'start': 2, 'end': 3, 'nexts': []},
               [
                   [
                       {'words': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2, 'nexts': []}
                   ]
               ]
           ],
           [
               {'words': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 1, 'nexts': []},
               {'words': [['0_NOU', '0_VER']],          'convo': ['1_NP', '1_VP'], 'start': 1, 'end': 2, 'nexts': []},
               {'words': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 2, 'end': 3, 'nexts': []},
               [
                    [
                        {'words': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2, 'nexts': []}
                    ],
                    [
                        {'words': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 1, 'end': 3, 'nexts': []}
                    ]
                ]
            ]
        ]
    ]