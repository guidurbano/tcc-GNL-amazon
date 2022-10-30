"""Route generator given configuration parameters"""
import os
from itertools import combinations

import numpy as np
import pandas as pd
import yaml

# Config
with open('scripts\\route_generator\\config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

rio = config['rio']
capacities = config['cap_max']
vel_media = config['vel_media'] * 1.852
t_carregamento = config['t_carregamento'] * 4 / 60

# Import data
cwd = os.getcwd()
df_dist = pd.read_excel(cwd + config['data_paths']['dist'], index_col=0)
df_loc = pd.read_parquet(
    cwd + config['data_paths']['loc'] + '{}.parquet'.format(rio))


def make_route(data: pd.DataFrame,
               df_dist: pd.DataFrame,
               cap_max: float,
               rio: str) -> pd.DataFrame:

    # Ordenar localidades por distancia a Manaus
    locs = data[data.Rio == rio]['Nome'].tolist()
    locs_ordered = df_dist.loc[locs].sort_values('MANAUS').index.tolist()

    localidades = data.set_index('Nome').loc[locs_ordered].index.tolist()
    demandas = data.set_index('Nome').loc[locs_ordered]['demanda_por_visita'].tolist()

    rotas = []
    demandas_rotas = []

    distancias_manaus = []
    tempos_porto = []
    tempos_nav = []
    tempos_ciclo = []

    num_rotas_totais = 0

    for i in range(1, len(localidades) + 1):  # Para cada combinacao (1 a 1, 2 a 2....)
     #   print(f'Combinações {i} a {i}:')
        comb_demandas = list(combinations(demandas, i))
        comb_locais = list(combinations(localidades, i))

        target_capac_max = 0
        for j, demanda_comb in enumerate(comb_demandas):  # Para cada rota nas combinacoes
            demanda_comb = sum(demanda_comb)
            if demanda_comb <= cap_max:  # se atingir a capacidade maxiam do navio
    #            print(f'Demanda total da rota: {demanda_comb}')
                demandas_rotas.append(demanda_comb)

                target_capac_max +=1
                # Estabelecer os nos da combinacao
                nos_comb = list(comb_locais[j])
    #            print(f'Rota: {nos_comb}')
                rotas.append(nos_comb)

                dist_manaus = 0
                dist_manaus += df_dist.loc[nos_comb[0], 'MANAUS']
                #final = df_dist.loc[nos_comb[-1], 'MANAUS']
  #              print(f'Distância do Primeiro local até Manaus: {dist_manaus}')
  #              print(f'Distância último local até Manaus: {final}')
                for k in range(0, len(nos_comb)):
                    if k < len(nos_comb) - 1:
                        no_anterior = nos_comb[k]
                        no_posterior = nos_comb[k+1]
                        distancia_entre_nos = df_dist.loc[no_anterior, no_posterior]
    #                    print(f'Arcos: {no_anterior} + {no_posterior}')
   #                     print(f'Distância do arco: {distancia_entre_nos}')
                        dist_manaus += distancia_entre_nos

                dist_manaus = round(dist_manaus, 2)
    #            print(f'Distância percorrida: {round(dist_manaus,2)}')
                distancias_manaus.append(dist_manaus)

                tempo_porto = round(demanda_comb * t_carregamento, 2)
                tempo_nav = round(2 * dist_manaus / vel_media, 2)
                tempo_ciclo = round(tempo_porto + tempo_nav, 2)

    #            print(f'Tempo de porto: {tempo_porto}')
                tempos_porto.append(tempo_porto)
    #            print(f'Tempo de nav: {tempo_nav}')
                tempos_nav.append(tempo_nav)
    #            print(f'Tempo de ciclo: {tempo_ciclo}')
                tempos_ciclo.append(tempo_ciclo)

    #            print('*******************************************')
    #    print(f'Total de rotas com {i} localidades: {target_capac_max}')
        num_rotas_totais += target_capac_max
    #    print('-------------------------------------------------')

        if target_capac_max == 0:
    #        print('Não há combinações maiores possíveis\n')
            break

    #print(f'Número total de rotas: {num_rotas_totais}\n')
    #print(f'Lista de rotas: {rotas}\n')
    #print(f'Demanda [containers] das rotas: {demandas_rotas}\n')
    #print(f'Tempo [h] de porto das rotas: {tempos_porto}')
    #print(f'Tempo [h] de navegação nas rotas: {tempos_nav}')
    #print(f'Tempo [h] de ciclo nas rotas: {tempos_ciclo}')
    #print(f'Distâncias máximas até Manaus: {distancias_manaus}')

    cols = {
        'nos': pd.Series(rotas),
        'demanda': pd.Series(demandas_rotas),
        'tempo_porto': pd.Series(tempos_porto),
        'tempo_nav': pd.Series(tempos_nav),
        'tempo_ciclo': pd.Series(tempos_ciclo),
        'distancia': pd.Series(distancias_manaus),
        }

    rotas = pd.DataFrame.from_dict(cols, orient='index').T
    rotas['vetor_loc_rota'] = rotas['nos'].apply(_loc_belong_route,
                                                 locs_ordered=locs_ordered)
    rotas['capacidade'] = cap_max

    return rotas


def _loc_belong_route(data: pd.DataFrame, locs_ordered: list):
    vetor_Q = np.zeros(len(locs_ordered))
    for i in range(0, len(vetor_Q)):
        if locs_ordered[i] in data:
            vetor_Q[i] = 1
    return vetor_Q


# Run for multiple vehicles
routes_full = pd.DataFrame()
for i, cap_max in enumerate(capacities):
    routes = make_route(data=df_loc,
                        cap_max=cap_max,
                        df_dist=df_dist,
                        rio=rio)
    routes['tipo_veic'] = i + 1
    routes_full = pd.concat([routes_full, routes],
                            ignore_index=True)

# Save
route_folder = cwd + config['data_paths']['routes_folder']
str_fleet = 'k_' + str(capacities)
routes_full.to_parquet(route_folder + f'rotas_{rio}_{str_fleet}.parquet')
