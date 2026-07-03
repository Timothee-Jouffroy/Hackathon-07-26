import pandas as pd
import numpy as np

df = pd.read_excel('all_years_clusterized.xlsx', sheet_name='Global')

years = [2016, 2017, 2018, 2019, 2020, 2021, 2022]
alphas = [2, 3, 4]


def G(data):
    sorted_data = np.sort(data)
    n = len(data)
    S = np.cumsum(sorted_data)
    total = S[-1]

    return (n + 1 - 2 * np.sum(S) / total) / n


def H(alpha, data):
    return (1 / (1 - alpha)) * np.log(np.sum(data ** alpha))


all_years_gini = {}
all_years_renyi = {alpha: {} for alpha in alphas}

for year in years:
    degree_col = f'{year} degree'
    df_clean = df[df[year].notna()].copy()
    clusters = sorted([c for c in df_clean[year].unique()])

    cluster_gini = {}

    for cluster in clusters:
        cluster_rows = df_clean[df_clean[year] == cluster]
        centrality_total = float(cluster_rows[degree_col].sum())

        if centrality_total > 0:
            data = (cluster_rows[degree_col] / centrality_total).to_numpy()
            cluster_gini[cluster] = float(G(data))

            for alpha in alphas:
                all_years_renyi[alpha].setdefault(year, {})[cluster] = float(H(alpha, data))
        else:
            cluster_gini[cluster] = np.nan

            for alpha in alphas:
                all_years_renyi[alpha].setdefault(year, {})[cluster] = np.nan

    all_years_gini[year] = cluster_gini


gini_df = pd.DataFrame.from_dict(all_years_gini, orient='index')
gini_df.index.name = 'year'

with pd.ExcelWriter('G&H.xlsx', engine='openpyxl') as writer:
    gini_df.to_excel(writer, sheet_name='Gini')

    for alpha in alphas:
        renyi_df = pd.DataFrame.from_dict(all_years_renyi[alpha], orient='index')
        renyi_df.index.name = 'year'
        renyi_df.to_excel(writer, sheet_name=f'alpha={alpha}')

print('OK!')