import gurobipy as gp
from gurobipy import GRB

# =================== SETUP ===============================
n_clientes = 4  # numero de clientes
n = n_clientes + 1  # depósito + clientes
m = 3  # numero de veiculos

# =================== PARAMETROS ===============================
N = range(n)
V = range(m)

# Custo de cada trecho
custo = {(i, j): 0 for i in N for j in N}
custo[(0, 1)] = 360
custo[(0, 2)] = 620
custo[(0, 3)] = 620
custo[(0, 4)] = 590
custo[(1, 2)] = 255
custo[(1, 3)] = 260
custo[(1, 4)] = 240
custo[(2, 3)] = 10
custo[(2, 4)] = 65
custo[(3, 4)] = 75

for i, j in custo.keys():  # Simetria da matriz de custo
    custo[j, i] = custo[i, j]

# Capacidade do veiculo
Q = 99

# Demanda do cliente
d = {i: 0 for i in N[1:]}
d[0] = 0
d[1] = 100
d[2] = 39
d[3] = 40
d[4] = 15

# =================== MODELO ===============================
model = gp.Model('VRP')

# Variaveis
x = model.addVars(N, N, V, vtype=GRB.BINARY, name='x')
f = model.addVars(N, N, V, vtype=GRB.CONTINUOUS, name='f')

# F Obj
model.setObjective(gp.quicksum(custo[(i, j)] * x[(i, j, k)]
                   for j in N
                   for i in N
                   for k in V),
                   sense=GRB.MINIMIZE)

# Restrições
c1 = model.addConstrs(gp.quicksum(x[(i, j, k)]
                                  for k in V
                                  for i in N if i != j) == 1
                      for j in N[1:])

c2 = model.addConstrs(gp.quicksum(x[(0, j, k)]
                                  for j in N) == 1
                      for k in V)

c3 = model.addConstrs(gp.quicksum(x[(i, 0, k)]
                                  for i in N) == 1
                      for k in V)

c4 = model.addConstrs(gp.quicksum(x[(i, j, k)]
                                  for i in N if i != j) == gp.quicksum(x[(j, h, k)]
                                                                       for h in N if h != j)
                      for j in N[1:]
                      for k in V)

c5 = model.addConstrs(gp.quicksum(d[i] * (gp.quicksum(x[(i, j, k)]
                                                      for j in N[1:] if i != j))
                                  for i in N) <= Q
                      for k in V)

c6 = model.addConstr(gp.quicksum(f[(0, j, k)]
                                 for j in N[1:]
                                 for k in V), GRB.EQUAL, n)

c7 = model.addConstrs(gp.quicksum(f[(i, j, k)]
                                  for i in N if i != j
                                  for k in V) - gp.quicksum(f[(j, i, k)]
                                                            for i in N if i != j
                                                            for k in V) == 1 for j in N[1:])

c8 = model.addConstrs(f[(i, j, k)] <= abs(n) * x[(i, j, k)]
                      for i in N
                      for j in N
                      for k in V)

# Restrição adicional para i == j
for k in range(m):
    for i in range(n):
        for j in range(n):
            if i == j:
                model.addConstr(x[(i, j, k)], GRB.EQUAL, 0)

# =================== OTIMIZAÇÃO ===============================
# Otimizar
model.optimize()

# Debugg de restrições
if not model.feasibility:
    model.computeIIS()
    model.write("model.ilp")

# Imprimo as variaveis diferentes de zero
for v in model.getVars():
    if v.x != 0:
        print('%s = %g' % (v.varName, v.x))

print('F. Obj: %g' % model.objVal)

# Imprimo as variaveis diferentes de zero e as rotas
for k in range(m):
    rota = [0]
    anterior = 0
    for var in x:
        for j in range(n):
            if x[anterior, j, k].X == 1:  # Mostro
                if j != 0:
                    rota.append(j)
                    anterior = j
                    break
                else:
                    break

    rota.append(0)
    print(f'Solução Ótima do veiculo {k}: {rota}')  # rota selecionada de cada veiculo
