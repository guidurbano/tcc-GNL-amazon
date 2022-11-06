import os

import gurobipy as gp
import numpy as np
import pandas as pd
import yaml

# Config
with open('model\\config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

rio = config['rio']
H = config['horizonte']
num_veic = config['num_veic']
capacities = config['capacities'][:num_veic]
days = list(range(1, H + 1))

# Import data
cwd = os.getcwd()
df_loc = pd.read_parquet(
    cwd + config['data_paths']['loc'] + '{}.parquet'.format(rio))
df_routes = pd.read_parquet(
    cwd + config['data_paths']['routes'] + \
         'rotas_{}_k_{}.parquet'.format(rio, capacities))

df_patterns = pd.read_excel(
    cwd + config['data_paths']['patterns'] + '{}_days.xlsx'.format(H)).drop(
        columns=['num', 'freq']
    )

# Cost for each vehicle (daily)
CF = config['fixed_cost'][:num_veic]
cost_per_day = config['transport_cost'][:num_veic]
C = list()
for k in range(1, num_veic + 1):
    C.append(df_routes.loc[df_routes.tipo_veic == k]['tempo_nav'].apply(
        lambda x: x / 24 * cost_per_day[k - 1]).tolist())

# Create a new model
model = gp.Model('gnl_amazon')

J = df_loc['Nome'].tolist()
K = list(range(num_veic))
R = [l.tolist() for l in df_routes['nos'].tolist()]
R_k = []
for k in range(1, num_veic + 1):
    R_k.append(df_routes.loc[df_routes.tipo_veic == k].index.tolist())
S = df_patterns.values.tolist()
S_j = df_loc['pattern'].tolist()
T = days
Q = df_routes['vetor_loc_rota'].tolist()
P = df_patterns.values.tolist()


def _vetor_A(r, k, u, t, H):
    duration = np.ceil(df_routes.iloc[R_k[k][r]]['tempo_ciclo'])
    end = (u + duration - 1) % H
    if end == 0:
        end = H
    if t <= end:
        return 1
    else:
        return 0


# Create variables
b = model.addVars(len(J), len(S), vtype=gp.GRB.BINARY, name='b')
x = model.addVars(len(K), len(R), len(T), vtype=gp.GRB.BINARY, name='x')
n = model.addVars(len(K), lb=0, vtype=gp.GRB.INTEGER, name='n')

# Objective Function
model.setObjective(
    gp.quicksum(
        C[k][r] * x[(k, r, t)]
        for k in range(len(K))
        for r in range(len(R_k[k]))
        for t in range(len(T))) +
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
    for t in range(len(T)) for j in range(len(J)))

c2_5 = model.addConstrs(
    gp.quicksum(x[(k, r, u)] * _vetor_A(r, k, u, t, H=H)
                for r in range(len(R_k[k])) for u in range(len(T))) <=
    n[(k)]
    for k in range(len(K)) for t in range(len(T)))

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
