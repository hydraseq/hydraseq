from hydraseq import MiniColumn


source_files = ['linear.0.000', 'linear.1.001', 'linear.2.002']
data_dir = 'tests/data'
mcol = MiniColumn(source_files, data_dir)

print(mcol.hydras[2])
ctree = mcol.compute_convolution_tree(". . . - - - . . .")

assert len(ctree) == 20
