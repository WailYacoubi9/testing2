#!/usr/bin/env python3
"""
Calcul du temps d'exécution séquentiel (1 worker) pour le modèle théorique.

Pour calculer le speedup correctement, on a besoin de T_seq - le temps
qu'il faudrait pour traiter le fichier entier sur une seule machine.
"""

import sys
sys.path.insert(0, 'model')
from theoretical_model import *

# =============================================================================
# PARAMÈTRES DU BENCHMARK
# =============================================================================

# Taille du fichier utilisé dans les benchmarks (estimation depuis Split_Time)
# Split de ~19s à 500 MB/s => ~9.5 GB de données
# Mais plus probablement : fichier de ~1GB avec overhead I/O
FILE_SIZE_MB = 1000  # 1 GB (estimation)

# Depuis vos données réelles (2 nodes = 1 worker)
T_MEASURED_1_WORKER = 35.92  # secondes (moyenne de vos benchmarks)

# =============================================================================
# CALCUL DU TEMPS SÉQUENTIEL PUR (SANS OVERHEAD DISTRIBUÉ)
# =============================================================================

def T_sequential(size_mb: float) -> float:
    """
    Temps séquentiel PUR - sans aucun overhead distribué.

    C'est le temps qu'il faudrait pour exécuter wordcount sur
    le fichier entier sur une seule machine, sans:
    - Initialisation de cluster
    - Split de fichier
    - Distribution
    - Communication RMI

    Formule: T_seq = T_read + T_compute + T_write

    Pour wordcount:
    T_seq ≈ (lines / V_wc) + overhead_IO
    """
    lines_per_mb = 10000  # lignes par MB
    total_lines = size_mb * lines_per_mb

    # Temps de calcul pur
    T_compute = total_lines / V_WC

    # Overhead I/O (lecture + écriture résultat)
    T_io = size_mb / 500.0  # ~500 MB/s lecture séquentielle

    return T_compute + T_io


def T_sequential_from_measurements() -> float:
    """
    Calcule T_seq à partir des mesures réelles.

    Avec 1 worker (2 nodes), on mesure:
    - Total: 35.92s
    - Split: ~19s  (overhead parallèle, pas nécessaire en séquentiel)
    - Distrib: ~0s (NFS)
    - Exec: ~17s   (temps réel de calcul)

    Donc T_seq ≈ Exec_time_1_worker = 17s
    (Sans le split qui n'est pas nécessaire en séquentiel pur)
    """
    # Données mesurées pour 2 nodes (1 worker)
    T_total_measured = 35.92
    T_split_measured = 18.55  # moyenne du split pour 2 nodes

    # Le temps séquentiel pur = Total - Split (pas de split en séquentiel)
    T_seq = T_total_measured - T_split_measured

    return T_seq


# =============================================================================
# AFFICHAGE DES RÉSULTATS
# =============================================================================

print("=" * 70)
print("CALCUL DU TEMPS SÉQUENTIEL (1 WORKER) POUR LE MODÈLE THÉORIQUE")
print("=" * 70)
print()

# Méthode 1: Depuis le modèle théorique avec n=1
print("MÉTHODE 1: Modèle théorique avec n=1")
print("-" * 50)
d = decompose(FILE_SIZE_MB, 1, "NFS")
print(f"  T_init(1)  = {d['T_init']:.3f} s  (initialisation 1 worker)")
print(f"  T_split    = {d['T_split']:.3f} s  (split fichier)")
print(f"  T_dist     = {d['T_dist']:.3f} s  (distribution NFS)")
print(f"  T_calc(1)  = {d['T_calc']:.3f} s  (calcul sur 1 worker)")
print(f"  T_agg      = {d['T_agg']:.3f} s  (agrégation)")
print(f"  ─────────────────────────────────")
print(f"  T(1)       = {d['T_total']:.3f} s")
print()

# Méthode 2: Temps séquentiel pur (sans overhead distribué)
print("MÉTHODE 2: Temps séquentiel PUR (sans overhead distribué)")
print("-" * 50)
T_seq_pure = T_sequential(FILE_SIZE_MB)
print(f"  T_read     = {FILE_SIZE_MB/500:.3f} s  (lecture fichier)")
print(f"  T_compute  = {FILE_SIZE_MB * 10000 / V_WC:.3f} s  (wordcount)")
print(f"  ─────────────────────────────────")
print(f"  T_seq_pur  = {T_seq_pure:.3f} s")
print()

# Méthode 3: Depuis les mesures réelles
print("MÉTHODE 3: Depuis les mesures réelles (recommandé)")
print("-" * 50)
T_seq_measured = T_sequential_from_measurements()
print(f"  T_total(2 nodes) = 35.92 s  (mesuré)")
print(f"  T_split          = 18.55 s  (mesuré)")
print(f"  ─────────────────────────────────")
print(f"  T_seq_réel       = {T_seq_measured:.2f} s  (Total - Split)")
print()

# =============================================================================
# COMPARAISON DES SPEEDUPS
# =============================================================================

print("=" * 70)
print("COMPARAISON DES SPEEDUPS AVEC DIFFÉRENTES RÉFÉRENCES")
print("=" * 70)
print()

# Temps mesurés
times_measured = {
    1: 35.92,   # 2 nodes
    2: 28.72,   # 3 nodes
    5: 23.96,   # 6 nodes
    7: 23.15,   # 8 nodes
    10: 22.42,  # 11 nodes
    12: 22.37,  # 13 nodes
    14: 22.35,  # 15 nodes
    17: 22.46,  # 18 nodes
}

# Références pour le speedup
T_ref_measured = 35.92      # T(1 worker) mesuré
T_ref_seq_pure = T_seq_measured  # T_seq sans split (~17s)

print(f"{'Workers':<10} {'T(n) mesuré':<15} {'Speedup (T1/Tn)':<18} {'Speedup (Tseq/Tn)':<18}")
print("-" * 61)

for workers, t_n in sorted(times_measured.items()):
    speedup_t1 = T_ref_measured / t_n
    speedup_seq = T_ref_seq_pure / t_n
    print(f"{workers:<10} {t_n:<15.2f} {speedup_t1:<18.2f} {speedup_seq:<18.2f}")

print()
print("Notes:")
print("  - Speedup (T1/Tn): Utilise T(1 worker) = 35.92s comme référence")
print("  - Speedup (Tseq/Tn): Utilise T_seq_pur = 17.37s comme référence")
print("  - Le deuxième montre le vrai potentiel si le split était parallélisé")
print()

# =============================================================================
# PRÉDICTION POUR SPEEDUP IDÉAL
# =============================================================================

print("=" * 70)
print("ANALYSE: POURQUOI LE SPEEDUP EST LIMITÉ?")
print("=" * 70)
print()

# Fraction séquentielle (loi d'Amdahl)
T_parallel = T_ref_seq_pure  # Partie parallélisable
T_sequential_part = T_ref_measured - T_parallel  # Partie séquentielle (split)
f_seq = T_sequential_part / T_ref_measured

print(f"Temps total avec 1 worker:  {T_ref_measured:.2f} s")
print(f"  - Partie séquentielle (split): {T_sequential_part:.2f} s ({f_seq*100:.1f}%)")
print(f"  - Partie parallélisable:       {T_parallel:.2f} s ({(1-f_seq)*100:.1f}%)")
print()

# Loi d'Amdahl
print("Loi d'Amdahl: Speedup_max = 1 / (f + (1-f)/n)")
print()
print(f"{'Workers (n)':<15} {'Speedup prédit':<18} {'Speedup mesuré':<18}")
print("-" * 51)

for workers in [1, 2, 5, 7, 10, 12, 14, 17]:
    speedup_amdahl = 1 / (f_seq + (1 - f_seq) / workers)
    speedup_measured = T_ref_measured / times_measured.get(workers, T_ref_measured)
    print(f"{workers:<15} {speedup_amdahl:<18.2f} {speedup_measured:<18.2f}")

print()
print(f"Speedup maximum théorique (n → ∞): {1/f_seq:.2f}x")
print()

# =============================================================================
# RECOMMANDATION POUR LE RAPPORT
# =============================================================================

print("=" * 70)
print("RECOMMANDATION POUR LE RAPPORT")
print("=" * 70)
print("""
Pour le modèle théorique dans votre rapport, utilisez:

1. T(1) = 35.92 s (mesuré avec 1 worker/2 nodes)
   → Inclut l'overhead de l'infrastructure distribuée
   → Donne un speedup "réaliste" de votre système

2. T_seq = 17.37 s (temps de calcul pur sans split)
   → Représente le vrai temps séquentiel
   → Montre le potentiel si le split était optimisé

3. Fraction séquentielle f = 51.6%
   → Le split représente plus de la moitié du temps!
   → Speedup maximum possible: ~1.94x (loi d'Amdahl)

CONCLUSION: Le goulot d'étranglement est le SPLIT (19s sur 36s).
Pour améliorer les performances:
  - Paralléliser le split (lecture distribuée)
  - Pré-découper les fichiers
  - Utiliser un format de fichier splittable (Parquet, etc.)
""")
