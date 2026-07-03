import pandas as pd
import numpy as np

df = pd.read_excel('all_years_clusterized_1.xlsx', sheet_name='Global')

years = [2016, 2017, 2018, 2019, 2020, 2021, 2022]
degree_cols = [f'{year} degree' for year in years]

dict_matrices_prochain_cluster = {}
dict_matrices_ancien_cluster = {}
dict_indices_depart = {}
dict_indices_arrivee = {}

for i in range(len(years) - 1):
    year_prec = years[i]
    year_suiv = years[i+1]
    
    degree_col_prec = degree_cols[i]
    degree_col_suiv = degree_cols[i+1]
    
    # Nettoyage des NaN pour l'année N+1
    df_clean = df[df[year_suiv].notna()]
    
    # notna() dans les listes de clusters pour éviter la ligne NaN parasite
    clusters_prec = sorted([c for c in df_clean[year_prec].unique() if pd.notna(c)])
    clusters_suiv = sorted([c for c in df_clean[year_suiv].unique() if pd.notna(c)])
    
    matrice_prochain_cluster = pd.DataFrame(0.0, index=clusters_prec, columns=clusters_suiv)
    matrice_ancien_cluster = pd.DataFrame(0.0, index=clusters_prec, columns=clusters_suiv)
    
    for j in range(len(clusters_prec)):
        for k in range(len(clusters_suiv)):
            
            #On calcule la proba d'aller à un cluster k en venant d'un cluster j, pondéré par les centralités de l'année n
            numerator1 = sum(df_clean[(df_clean[year_prec] == clusters_prec[j]) & (df_clean[year_suiv] == clusters_suiv[k])][degree_col_prec])
            denominator1 = sum(df_clean[df_clean[year_prec] == clusters_prec[j]][degree_col_prec])
            
            if denominator1 > 0:
                matrice_prochain_cluster.iloc[j, k] = numerator1 / denominator1
            else:
                matrice_prochain_cluster.iloc[j, k] = 0
            
            
            
            #On calcule la proba d'avoir été dans un cluster j sachant qu'on est dans un cluster k, pondéré par les centralités de l'année n+1
            numerator2 = sum(df_clean[(df_clean[year_prec] == clusters_prec[j]) & (df_clean[year_suiv] == clusters_suiv[k])][degree_col_suiv])
            denominator2 = sum(df_clean[df_clean[year_suiv] == clusters_suiv[k]][degree_col_suiv])
            
            if denominator2 > 0:
                matrice_ancien_cluster.iloc[j, k] = numerator2 / denominator2
            else:
                matrice_ancien_cluster.iloc[j, k] = 0
                
    dict_matrices_prochain_cluster[f"{year_prec}->{year_suiv}"] = matrice_prochain_cluster
    dict_matrices_ancien_cluster[f"{year_prec}<-{year_suiv}"] = matrice_ancien_cluster
    
    
    
    # --- Indices d'évolution des clusters de départ ---
    # R = rapport des moyennes : centralité moyenne à N+1 de la cohorte (articles du cluster j suivis à N+1)
    #     / centralité moyenne à N du cluster j -> effet influence par article (consolidation si R > 1)
    # G = croissance absolue : centralité totale à N+1 du successeur principal (argmax de la matrice forward)
    #     / centralité totale à N du cluster j -> effet de masse, recrutement inclus (expansion si G >> R)
    
    indices_depart = pd.DataFrame(index=clusters_prec,
                                  columns=['nb articles', 'successeur', 'retention', 'R', 'G'])
    
    for cluster in clusters_prec:
        cluster_complet = df[df[year_prec] == cluster]
        cohorte = df_clean[df_clean[year_prec] == cluster]
        
        moyenne_prec = cluster_complet[degree_col_prec].mean()
        moyenne_suiv = cohorte[degree_col_suiv].mean()
        total_prec = cluster_complet[degree_col_prec].sum()
        
        successeur = matrice_prochain_cluster.loc[cluster].idxmax()
        total_successeur = df_clean[df_clean[year_suiv] == successeur][degree_col_suiv].sum()
        
        indices_depart.loc[cluster, 'nb articles'] = len(cluster_complet)
        indices_depart.loc[cluster, 'successeur'] = successeur
        indices_depart.loc[cluster, 'retention'] = matrice_prochain_cluster.loc[cluster, successeur]
        indices_depart.loc[cluster, 'R'] = moyenne_suiv / moyenne_prec if moyenne_prec > 0 else np.nan
        indices_depart.loc[cluster, 'G'] = total_successeur / total_prec if total_prec > 0 else np.nan
    
    dict_indices_depart[f"{year_prec}->{year_suiv}"] = indices_depart
    
    
    
    # --- Indices des clusters d'arrivée (composition du cluster k à N+1) ---
    # taux de recrutement : part de la centralité totale du cluster k portée par les articles nouveaux
    #     (absents du graphe à N) -> complément à 1 de la somme de colonne de la matrice backward
    # R arrivee : centralité moyenne des articles du cluster k à N+1 / centralité moyenne à N des anciens articles
    
    indices_arrivee = pd.DataFrame(index=clusters_suiv,
                                   columns=['nb articles', 'nb nouveaux', 'taux recrutement', 'R arrivee'])
    
    for cluster in clusters_suiv:
        membres = df_clean[df_clean[year_suiv] == cluster]
        nouveaux = membres[membres[year_prec].isna()]
        anciens = membres[membres[year_prec].notna()]
        
        total_suiv = membres[degree_col_suiv].sum()
        moyenne_suiv = membres[degree_col_suiv].mean()
        moyenne_anciens_prec = anciens[degree_col_prec].mean() if len(anciens) > 0 else np.nan
        
        indices_arrivee.loc[cluster, 'nb articles'] = len(membres)
        indices_arrivee.loc[cluster, 'nb nouveaux'] = len(nouveaux)
        indices_arrivee.loc[cluster, 'taux recrutement'] = nouveaux[degree_col_suiv].sum() / total_suiv if total_suiv > 0 else np.nan
        indices_arrivee.loc[cluster, 'R arrivee'] = moyenne_suiv / moyenne_anciens_prec if moyenne_anciens_prec and moyenne_anciens_prec > 0 else np.nan
    
    dict_indices_arrivee[f"{year_prec}->{year_suiv}"] = indices_arrivee


# Sauvegarde Excel
with pd.ExcelWriter('matrices_transition.xlsx', engine='openpyxl') as writer:
    for key, matrix in dict_matrices_prochain_cluster.items():
        matrix.to_excel(writer, sheet_name=key)
    for key, matrix in dict_matrices_ancien_cluster.items():
        matrix.to_excel(writer, sheet_name=key)

with pd.ExcelWriter('indices_evolution.xlsx', engine='openpyxl') as writer:
    for key, table in dict_indices_depart.items():
        table.to_excel(writer, sheet_name=f"depart {key}")
    for key, table in dict_indices_arrivee.items():
        table.to_excel(writer, sheet_name=f"arrivee {key}")

print('OK !')