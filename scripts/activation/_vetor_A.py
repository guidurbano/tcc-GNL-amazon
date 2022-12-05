"""Returns if the route is active in one specific day"""
import numpy as np
import pandas as pd

H = 5
data = []
for d in range(1, H + 1):
    for u in range(1, H + 1):
        duration = np.ceil(d)
        end = int((u + duration - 1) % H)
        if end == 0:
            end = H
        list = []
        for t in range(1, H + 1):
            if (t == u) | (t == end):
                activate = 1
            elif u == end:
                if t == u:
                    activate = 1
                else:
                    activate = 0
            else:
                if t < end:
                    if end > u:
                        if t > u:
                            activate = 1
                        else:
                            activate = 0
                    else:
                        activate = 1
                if t > end:
                    if end < u:
                        if t < u:
                            activate = 0
                        else:
                            activate = 1
                    else:
                        activate = 0
            list.append(activate)
        data.append(list)
        print(f'u={u},d={d}: {list} (end={end})')
