import os

import gurobipy as gp
import numpy as np
import pandas as pd
import yaml


# Config
with open('model\\config2.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

rio = config['rio']
horizontes = config['horizonte']
H = np.lcm.reduce(horizontes)
num_veic = config['num_veic']
capacities = config['capacities'][:num_veic]
days = list(range(1, H + 1))
# Import data
cwd = os.getcwd()

for i, z in enumerate(rio):
    if i == 0:
        df_loc_global = pd.read_parquet(
            cwd + config['data_paths']['loc'] + '{}.parquet'.format(z))
        df_routes_global = pd.read_parquet(
            cwd + config['data_paths']['routes'] + \
                'rotas_{}_k_{}.parquet'.format(z, capacities))
        Q_1 = df_routes_global['vetor_loc_rota'].tolist()
        for m in range(len(Q_1)):
            Q_1[m] = np.append(Q_1[m], [0,0,0,0,0,0,0,0])
        df_routes_global['horizonte_rio'] = horizontes[i]
    else:
        df_loc = pd.read_parquet(
            cwd + config['data_paths']['loc'] + '{}.parquet'.format(z))
        df_loc_global = pd.concat([df_loc_global, df_loc])

        df_routes = pd.read_parquet(
            cwd + config['data_paths']['routes'] + \
                'rotas_{}_k_{}.parquet'.format(z, capacities))
        Q_2 = df_routes['vetor_loc_rota'].tolist()
        for mm in range(len(Q_2)):
            Q_2[mm] = np.append([0,0,0,0,0,0,0], Q_2[mm])
        df_routes['horizonte_rio'] = horizontes[i]
        df_routes_global = pd.concat([df_routes_global, df_routes])
        Q_1 = np.append(Q_1, Q_2, axis=0)
Q = Q_1
df_routes_global = df_routes_global.reset_index(drop=True)
df_loc_global = pd.read_parquet(
            cwd + config['data_paths']['loc'] + '{}.parquet'.format(rio))

df_patterns = pd.read_excel(
    cwd + config['data_paths']['patterns'] + '{}_days.xlsx'.format(H)).drop(
        columns=['num', 'freq']
    )
# Cost for each vehicle (daily)
CF = config['fixed_cost'][:num_veic]
cost_per_day = config['transport_cost'][:num_veic]
C = list()
for _k in range(1, num_veic + 1):
    C.append(df_routes_global.loc[df_routes_global.tipo_veic == _k]['tempo_nav'].apply(
        lambda x: x / 24 * cost_per_day[_k - 1]).tolist())

J = df_loc_global['Nome'].tolist()
K = list(range(num_veic))
R = [l.tolist() for l in df_routes_global['nos'].tolist()]
R_k = []
for k in range(1, num_veic + 1):
    R_k.append(df_routes_global.loc[df_routes_global.tipo_veic == k].index.tolist())
S = df_patterns.values.tolist()
S_j = df_loc_global['pattern'].tolist()
T = days
#Q = df_routes_global['vetor_loc_rota'].tolist()
P = df_patterns.values.tolist()


def _vetor_A(r, k, u, t):
    duration = np.ceil(df_routes_global.iloc[R_k[k][r]]['tempo_ciclo']  / 24)
    h = df_routes_global.iloc[R_k[k][r]]['horizonte_rio']
    end = (u + duration - 1) % h
    if end == 0:
        end = h
    if (t == u) | (t == end):
        return 1
    elif u == end:
        if t == u:
            return 1
        else:
            return 0
    else:
        if t < end:
            if end > u:
                if t > u:
                    return 1
                else:
                    return 0
            else:
                return 1
        if t > end:
            if end < u:
                if t < u:
                    return 0
                else:
                    return 1
            else:
                return 0

# Create a new model
model = gp.Model('gnl_amazon')

# Create variables
b = model.addVars(len(J), len(S), vtype=gp.GRB.BINARY, name='b')
x = model.addVars(len(K), len(R), len(T), vtype=gp.GRB.BINARY, name='x')
n = model.addVars(len(K), lb=0, vtype=gp.GRB.INTEGER, name='n')


# Objective Function
def _f_w(k, r, H):
    f_w = (H / df_routes_global.iloc[R_k[k][r]]['horizonte_rio'])
    return f_w


model.setObjective(
    gp.quicksum(
        C[k][r] * x[(k, r, t)] * _f_w(k, r, H)
        for k in range(len(K))
        for r in range(len(R_k[k]))
        for t in range(len(T))
        ) +
    gp.quicksum(
        CF[k] * n[(k)]
        for k in range(len(K))),
    sense=gp.GRB.MINIMIZE)

# Restrictions
c2_3 = model.addConstrs(
    gp.quicksum(b[(j, s)]
                for s in S_j[j]) == 1
    for j in range(len(J)))

c2_4 = model.addConstrs(
    gp.quicksum(x[(k, r, t)] * Q[r][j]
                for k in range(len(K)) for r in range(len(R_k[k]))) ==
    gp.quicksum(b[(j, s)] * P[s][t]
                for s in S_j[j])
    for t in range(len(days)) for j in range(len(J)))

c2_5 = model.addConstrs(
    gp.quicksum(x[(k, r, u)] * _vetor_A(r, k, u=u+1, t=t+1)
                for r in range(len(R_k[k])) for u in range(len(days)))  <=
    n[(k)]
    for k in range(len(K)) for t in range(len(days)))

# Results and debug
out_file = cwd + config['data_paths']['results'] + '{}\\{}_k_{}'.format(
    rio, rio, capacities)
model.optimize()
model.printQuality()
model.printStats()
model.printAttr('x')
model.printAttr('objVal')
model.write(out_file + '.json')
model.write(out_file + '.sol')
model.write(out_file + '.lp')
