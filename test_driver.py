from hydraseq import MiniColumn

source_files = ['linear.0.000', 'linear.1.001', 'linear.2.002', 'linear.3.003']
data_dir = 'tests/data/'

mcol = MiniColumn(source_files, data_dir)

ctree = mcol.compute_convolution_tree(". - .")
