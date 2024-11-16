from fealpy.backend import backend_manager as bm
from fealpy.opt import *
from fealpy.opt.optimizer_base import opt_alg_options
from fealpy.opt.benchmark import iopt_benchmark_data as iopt_data
# device = 'cpu'

# 定义后端
# bm.set_backend('pytorch')
# 定义设备
# device = 'cuda'
# bm.set_default_device(device)

import time 
start_time = time.perf_counter()

num = 1
lb, ub = iopt_data[num]['domain']
NP = 100
MaxIters = 1000
dim = 30
x0 = lb + bm.random.rand(NP, dim) * (ub - lb)
option = opt_alg_options(x0, iopt_data[num]['objective'], iopt_data[num]['domain'], NP, MaxIters=MaxIters)
optimizer = LevyQuantumParticleSwarmOpt(option)

gbest, gbest_f = optimizer.run()
print("The final result by QPSO: ", gbest_f)


end_time = time.perf_counter()
running_time = end_time - start_time
print("Running time :", running_time)