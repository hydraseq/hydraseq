from hydraseq import MiniColumn
import time
source_files = [
        'linear.0.000',
        'linear.1.001',
        'linear.2.002',
        'linear.3.003'
        ]
data_dir = 'tests/data/'

mcol = MiniColumn(source_files, data_dir)

#ctree = mcol.compute_convolution_tree(". - .")

efrain = ". . . - . . - . . - . . - ."

now = time.time()
ctree = mcol.compute_convolution_tree(efrain)
print(time.time() - now)

for hydra in mcol.hydras:
    print(hydra.active_nodes)


