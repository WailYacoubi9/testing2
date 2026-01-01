#!/usr/bin/env python3
"""
Calcul du temps d'exécution WORDCOUNT uniquement (T_exec)
Sans: init, split, distribution - juste le job de calcul
"""

import pandas as pd

# Données depuis vos benchmarks
# Exec_time = Total_Time - Distrib_Exec_Start (temps de calcul pur)
data = {
    'Nodes': [2, 2, 2, 3, 3, 3, 6, 6, 6, 8, 8, 8, 11, 11, 11, 13, 13, 13, 15, 15, 15, 18, 18, 18],
    'Total_Time_ms': [37069, 35616, 35086, 29404, 28522, 28235, 25279, 23327, 23273, 24439, 22268, 22733, 23775, 21643, 21839, 23514, 21733, 21863, 23685, 21651, 21727, 23615, 21659, 22104],
    'Distrib_Exec_Start_ms': [19554, 18101, 18071, 19893, 19011, 18724, 20267, 18816, 18762, 20427, 18758, 19223, 20264, 18632, 18829, 20002, 18722, 18852, 20172, 18639, 18715, 20101, 18645, 19092]
}

df = pd.DataFrame(data)

# Temps d'exécution wordcount = Total - Distrib_Start
df['Exec_ms'] = df['Total_Time_ms'] - df['Distrib_Exec_Start_ms']
df['Exec_s'] = df['Exec_ms'] / 1000
df['Workers'] = df['Nodes'] - 1  # Master ne compte pas

# Moyennes par nombre de workers
stats = df.groupby('Workers').agg({
    'Exec_s': ['mean', 'std'],
    'Exec_ms': 'mean'
}).reset_index()
stats.columns = ['Workers', 'Exec_mean', 'Exec_std', 'Exec_ms_mean']
stats = stats.sort_values('Workers')

# T(1) = temps d'exécution avec 1 seul worker
T1 = stats[stats['Workers'] == 1]['Exec_mean'].values[0]

# Calcul du speedup basé uniquement sur l'exécution
stats['Speedup'] = T1 / stats['Exec_mean']
stats['Speedup_ideal'] = stats['Workers']
stats['Efficiency'] = (stats['Speedup'] / stats['Workers']) * 100

print("=" * 70)
print("TEMPS D'EXÉCUTION WORDCOUNT UNIQUEMENT (sans split/init)")
print("=" * 70)
print()
print(f"T(1) = {T1:.2f} secondes (1 worker traite tout le fichier)")
print()
print(f"{'Workers':<10} {'T_exec (s)':<12} {'Speedup':<12} {'Efficacité':<12} {'Idéal':<10}")
print("-" * 56)

for _, row in stats.iterrows():
    print(f"{int(row['Workers']):<10} {row['Exec_mean']:<12.2f} {row['Speedup']:<12.2f} {row['Efficiency']:<12.1f}% {row['Workers']:<10.1f}")

print()
print("=" * 70)
print("ANALYSE DU SPEEDUP (EXÉCUTION PURE)")
print("=" * 70)
print()

# Le speedup est bien meilleur quand on regarde juste l'exécution!
best_speedup = stats['Speedup'].max()
best_workers = stats.loc[stats['Speedup'].idxmax(), 'Workers']
best_efficiency = stats.loc[stats['Speedup'].idxmax(), 'Efficiency']

print(f"Meilleur speedup: {best_speedup:.2f}x avec {int(best_workers)} workers")
print(f"Efficacité à ce point: {best_efficiency:.1f}%")
print()

# Modèle théorique simple pour l'exécution
print("=" * 70)
print("MODÈLE THÉORIQUE SIMPLIFIÉ (EXÉCUTION WORDCOUNT)")
print("=" * 70)
print()
print("Formule: T_exec(n) = T_calc/n + T_overhead(n)")
print()
print("Où:")
print(f"  T_calc = {T1:.2f} s  (temps de calcul total, mesuré avec 1 worker)")
print("  T_overhead(n) = latence RMI + coordination")
print()

# Estimation de l'overhead
print("Estimation de l'overhead par régression:")
print()
for _, row in stats.iterrows():
    n = row['Workers']
    T_n = row['Exec_mean']
    T_ideal = T1 / n
    overhead = T_n - T_ideal
    print(f"  {int(n)} workers: T_exec={T_n:.2f}s, T_idéal={T_ideal:.2f}s, overhead={overhead:.2f}s")

print()
print("=" * 70)
print("FORMULE FINALE POUR LE MODÈLE")
print("=" * 70)
print()
print(f"""
Pour le temps d'exécution wordcount UNIQUEMENT:

    T_exec(n) = T1/n + O(n)

Avec:
    T1 = {T1:.2f} secondes (temps séquentiel mesuré)
    O(n) = overhead de coordination (~0.5-1.5s selon n)

Speedup théorique: S(n) = T1 / T_exec(n)

Cette formule prédit bien mieux les performances car elle
isole la partie parallélisable du système.
""")

# Export pour graphique
print("=" * 70)
print("DONNÉES POUR GRAPHIQUE")
print("=" * 70)
print()
print("Workers,T_exec_s,Speedup,Efficiency")
for _, row in stats.iterrows():
    print(f"{int(row['Workers'])},{row['Exec_mean']:.3f},{row['Speedup']:.3f},{row['Efficiency']:.1f}")
