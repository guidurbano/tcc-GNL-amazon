import os

import gurobipy as gp
import numpy as np
import pandas as pd
import yaml


# Config
with open('model\\multiple\\config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

rios = config['rios']
horizontes = config['horizontes']
H = np.lcm.reduce(horizontes)
num_veic = config['num_veic']
capacities = config['capacities'][:num_veic]
max_num_loc = config['max_num_loc']
# Import data
cwd = os.getcwd()


def _add_locs(data):
    v = list(data[0])
    rio = data[1]
    if rios == ['Amazonas', 'Madeira']:
        if rio == 'Amazonas':
            return v + list(np.zeros(8))
        if rio == 'Madeira':
            return list(np.zeros(7)) + v
    if rios == ['Amazonas', 'Solimoes']:
        if rio == 'Amazonas':
            return v + list(np.zeros(16))
        if rio == 'Solimoes':
            return list(np.zeros(7)) + v
    if rios == ['Madeira', 'Solimoes']:
        if rio == 'Madeira':
            return v + list(np.zeros(16))
        if rio == 'Solimoes':
            return list(np.zeros(8)) + v
    if rios == ['Amazonas', 'Madeira', 'Solimoes']:
        if rio == 'Amazonas':
            return v + list(np.zeros(16 + 8))
        if rio == 'Madeira':
            return list(np.zeros(7)) + v + list(np.zeros(16))
        if rio == 'Solimoes':
            return list(np.zeros(7 + 8)) + v


def _horizonte_rio(rio):
    if rio == 'Amazonas':
        return 7
    if rio == 'Madeira':
        return 14
    if rio == 'Solimoes':
        return 21


df_loc_global = pd.read_parquet(
            cwd + config['data_paths']['loc'] + '{}.parquet'.format(rios))

df_routes_global = pd.DataFrame()
loc_paths = [cwd + config['data_paths']['routes'] +
            'rotas_{}_k_{}.parquet'.format(rio, capacities)
             for rio in rios]

for path in loc_paths:
    df_routes = pd.read_parquet(path)
    df_routes_global = pd.concat([df_routes_global, df_routes])

df_routes_global['vetor_loc_rota'] = df_routes_global[['vetor_loc_rota', 'rio']].apply(
    _add_locs, axis=1)

df_routes_global = df_routes_global.sort_values(by=['tipo_veic', 'rio'])
df_routes_global['horizonte_rio'] = df_routes_global.rio.apply(_horizonte_rio)
df_routes_global['num_visits'] = df_routes_global['vetor_loc_rota'].apply(
    lambda x: sum(x))
df_routes_global = df_routes_global[df_routes_global['num_visits'] <= max_num_loc]
df_routes_global = df_routes_global.reset_index(drop=True)

Q = df_routes_global['vetor_loc_rota'].tolist()

## Pattern
df_patterns = pd.read_excel(
    cwd + config['data_paths']['patterns'] + '{}_days.xlsx'.format(H)).drop(
        columns=['num', 'freq']
    )
# Cost for each vehicle (daily)
CF = config['fixed_cost'][:num_veic]
cost_per_day = config['transport_cost'][:num_veic]


def transport_cost(data):
    tempo_nav, tipo_veic = data[0], int(data[1])
    return tempo_nav / 24 * cost_per_day[tipo_veic - 1]


C = df_routes_global[['tempo_nav', 'tipo_veic']].apply(
    transport_cost, axis=1).tolist()

# Parameters
J = df_loc_global['Nome'].tolist()
K = list(range(num_veic))
R = df_routes_global.index.tolist()
S = df_patterns.values.tolist()
S_j = df_loc_global['pattern'].tolist()
T = list(range(1, H + 1))
P = df_patterns.values.tolist()


def _vetor_A(r, u, t):
    duration = np.ceil(df_routes_global.iloc[r]['tempo_ciclo'] / 24)
    h = df_routes_global.iloc[r]['horizonte_rio']
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
x = model.addVars(len(R), len(T), vtype=gp.GRB.BINARY, name='x')
n = model.addVars(len(K), lb=0, vtype=gp.GRB.INTEGER, name='n')


# Objective Function
def _f_w(r, H):
    f_w = (H / df_routes_global.iloc[r]['horizonte_rio'])
    return f_w


model.setObjective(
    gp.quicksum(
        C[r] * x[(r, t)] * _f_w(r, H)
        for r in range(len(R))
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
    gp.quicksum(x[(r, t)] * Q[r][j]
                for r in range(len(R))) ==
    gp.quicksum(b[(j, s)] * P[s][t]
                for s in S_j[j])
    for t in range(len(T)) for j in range(len(J)))

c2_5 = model.addConstrs(
    gp.quicksum(x[(r, u)] * _vetor_A(r, u=u+1, t=t+1)
                for r in range(len(R))
                if df_routes_global.iloc[r]['tipo_veic'] == k + 1
                for u in range(len(T))) <=
    n[(k)]
    for k in range(len(K)) for t in range(len(T)))

# Results and debug
out_file = cwd + config['data_paths']['results'] + '{}\\{}_k_{}'.format(
    rios, rios, capacities)
model.optimize()
model.printQuality()
model.printStats()
model.printAttr('x')
model.printAttr('objVal')
model.write(out_file + '.json')
model.write(out_file + '.sol')
model.write(out_file + '.lp')
