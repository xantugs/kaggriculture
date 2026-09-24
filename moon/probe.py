import os, subprocess, time, sys
print('cpu_count', os.cpu_count(), flush=True)
try:
    print(open('/proc/meminfo').read().split('\n')[0], flush=True)
    print(subprocess.run(['nproc'], capture_output=True, text=True).stdout, flush=True)
    print(subprocess.run(['bash', '-c', 'lscpu | head -20'], capture_output=True, text=True).stdout, flush=True)
except Exception as e:
    print(e)
import numpy as np
t = time.time(); a = np.random.rand(512, 512).astype(np.float32)
for _ in range(200): a @ a
print('matmul200', round(time.time() - t, 3), flush=True)
