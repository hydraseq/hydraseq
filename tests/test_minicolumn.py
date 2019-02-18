import re
import sys
sys.path.append('./hydraseq')
import hydraseq
from minicolumn import MiniColumn

def test_mini_column():
    sentence = "spring leaves spring"
    source_files = ["seasons.0.txt", "seasons.1.txt", "seasons.2.txt"]
    mcol = MiniColumn(source_files, "tests/data")
    mcol.get_state()

    assert mcol.compute_convolution_tree("spring leaves spring") == [
            [0, 1, ['0_ADJ', '0_NOU', '0_VER']],
            [1, 2, ['0_NOU', '0_VER']],
            [2, 3, ['0_ADJ', '0_NOU', '0_VER']],
            [
                [
                    [0, 1, ['1_NP', '1_VP']],
                    [1, 3, ['1_VP']],
                    [
                        [
                            [0, 2, ['2_SENT']]
                        ]
                    ]
                ],
                [
                    [0, 2, ['1_NP', '1_VP']],
                    [2, 3, ['1_NP', '1_VP']],
                    [
                        [
                            [0, 2, ['2_SENT']]
                        ]
                    ]
                ],
                [
                    [0, 1, ['1_NP', '1_VP']],
                    [1, 2, ['1_NP', '1_VP']],
                    [2, 3, ['1_NP', '1_VP']],
                    [
                        [
                            [0, 2, ['2_SENT']]
                        ],
                        [
                            [1, 3, ['2_SENT']]
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

    assert mcol.hydras[0].convolutions(sentence) == [
        [0, 1, ['0_ADJ', '0_NOU', '0_VER']],
        [1, 2, ['0_NOU', '0_VER']],
        [2, 3, ['0_ADJ', '0_NOU', '0_VER']]
    ]

    assert mcol.hydras[0].convolutions(sentence, as_json=True) == [
        {'convo': ['0_ADJ', '0_NOU', '0_VER'], 'end': 1, 'start': 0, 'word': [['spring']]},
        {'convo': ['0_NOU', '0_VER'],          'end': 2, 'start': 1, 'word': [['leaves']]},
        {'convo': ['0_ADJ', '0_NOU', '0_VER'], 'end': 3, 'start': 2, 'word': [['spring']]}
    ]

    assert mcol.resolve_convolution(mcol.hydras[0].convolutions(sentence))[0] == [
        [0, 1, ['0_ADJ', '0_NOU', '0_VER']],
        [1, 2, ['0_NOU', '0_VER']],
        [2, 3, ['0_ADJ', '0_NOU', '0_VER']]
    ]

    assert mcol.resolve_convolution_obj(mcol.hydras[0].convolutions(sentence, as_json=True))[0] == [
            {'word': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1, 'nexts': []},
            {'word': [['leaves']], 'convo': ['0_NOU', '0_VER'], 'start': 1, 'end': 2, 'nexts': []},
            {'word': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 2, 'end': 3, 'lasts': [
                {'word': [['leaves']], 'convo': ['0_NOU', '0_VER'], 'start': 1, 'end': 2, 'lasts': [
                    {'word': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1, 'lasts': [], 'nexts': []}
                ], 'nexts': []}
            ], 'nexts': []}
        ]

    result = mcol.to_tree_nodes_obj(mcol.hydras[0].convolutions(sentence, as_json=True))
    assert mcol.to_tree_nodes_obj(mcol.hydras[0].convolutions(sentence, as_json=True)) == [
        {
            'word': [['spring']],
            'convo': ['0_ADJ', '0_NOU', '0_VER'],
            'start': 2,
            'end': 3,
            'lasts': [
                {
                    'word': [['leaves']],
                    'convo': ['0_NOU', '0_VER'],
                    'start': 1,
                    'end': 2,
                    'lasts': [
                        {
                            'word': [['spring']],
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

    final = mcol.reconstruct_obj(result)
    assert mcol.reconstruct_obj(result) == [
        [
            {'word': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1, 'nexts': []},
            {'word': [['leaves']], 'convo': ['0_NOU', '0_VER'], 'start': 1, 'end': 2, 'nexts': []},
            {'word': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 2, 'end': 3, 'lasts': [
                {'word': [['leaves']], 'convo': ['0_NOU', '0_VER'], 'start': 1, 'end': 2, 'lasts': [
                    {'word': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1, 'lasts': [], 'nexts': []}
                ], 'nexts': []}
            ], 'nexts': []}
        ]
    ]

    res = mcol.compute_convolution_tree("spring leaves spring")
    print("RES->",res)
    res_obj = mcol.compute_convolution_tree_obj("spring leaves spring")
    print("RES_OBJ->", res_obj)
    assert mcol.compute_convolution_tree_obj("spring leaves spring") == [
        {'word': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1, 'nexts': []},
        {'word': [['leaves']], 'convo': ['0_NOU', '0_VER'], 'start': 1, 'end': 2, 'nexts': []},
        {'word': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 2, 'end': 3, 'lasts': [
            {'word': [['leaves']], 'convo': ['0_NOU', '0_VER'], 'start': 1, 'end': 2, 'lasts': [
                {'word': [['spring']], 'convo': ['0_ADJ', '0_NOU', '0_VER'], 'start': 0, 'end': 1, 'lasts': [], 'nexts': []}
            ], 'nexts': []}
        ], 'nexts': []},
        [
            [
                {'word': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 1, 'nexts': []},
                {'word': [['0_NOU', '0_VER'], ['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_VP'], 'start': 1, 'end': 3, 'lasts': [
                    {'word': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 1, 'lasts': [], 'nexts': []}
                    ], 'nexts': []},
            [
                [
                    {'word': [['1_NP', '1_VP'], ['1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2, 'lasts': [], 'nexts': []}
                ]
            ]
        ],
        [
            {'word': [['0_ADJ', '0_NOU', '0_VER'], ['0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 2, 'nexts': []},
            {'word': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 2, 'end': 3, 'lasts': [
                {'word': [['0_ADJ', '0_NOU', '0_VER'], ['0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 2, 'lasts': [], 'nexts': []}
            ], 'nexts': []},
            [
                [
                    {'word': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2, 'lasts': [], 'nexts': []}

                ]
            ]
            ],
            [
                {'word': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 1, 'nexts': []},
                {'word': [['0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 1, 'end': 2, 'nexts': []},
                {'word': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 2, 'end': 3, 'lasts': [
                    {'word': [['0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 1, 'end': 2, 'lasts': [
                        {'word': [['0_ADJ', '0_NOU', '0_VER']], 'convo': ['1_NP', '1_VP'], 'start': 0, 'end': 1, 'lasts': [], 'nexts': []}
                        ], 'nexts': []}
                    ], 'nexts': []},
                [
                    [
                        {'word': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 0, 'end': 2, 'lasts': [], 'nexts': []}
                    ],
                    [
                        {'word': [['1_NP', '1_VP'], ['1_NP', '1_VP']], 'convo': ['2_SENT'], 'start': 1, 'end': 3, 'lasts': [], 'nexts': []}

                    ]
                ]
            ]
        ]
    ]