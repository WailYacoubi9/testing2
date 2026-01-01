#!/usr/bin/env python3
"""
Plot T(1) benchmark results with median
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuration
CSV_FILE = "t1_wordcount_results.csv"
OUTPUT_FILE = "t1_plot.png"

def plot_t1_results():
    # Lire les données
    df = pd.read_csv(CSV_FILE)

    iterations = df['iteration']
    times_ms = df['time_ms']
    times_s = times_ms / 1000

    # Statistiques
    median = np.median(times_ms)
    mean = np.mean(times_ms)
    std = np.std(times_ms)
    q1 = np.percentile(times_ms, 25)
    q3 = np.percentile(times_ms, 75)

    # Figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8),
                                    gridspec_kw={'height_ratios': [3, 1]})

    # --- Plot 1: Points des 30 itérations ---
    ax1.scatter(iterations, times_ms, s=100, c='#3498db', alpha=0.7,
                edgecolors='black', linewidth=1, label='Mesures')

    # Ligne médiane
    ax1.axhline(y=median, color='#e74c3c', linestyle='-', linewidth=2.5,
                label=f'Médiane = {median:.0f} ms')

    # Ligne moyenne
    ax1.axhline(y=mean, color='#2ecc71', linestyle='--', linewidth=2,
                label=f'Moyenne = {mean:.0f} ms')

    # Zone écart-type
    ax1.fill_between([0, len(iterations)+1], mean-std, mean+std,
                     alpha=0.2, color='#2ecc71', label=f'±σ = {std:.0f} ms')

    ax1.set_xlabel('Itération', fontsize=12)
    ax1.set_ylabel('Temps (ms)', fontsize=12)
    ax1.set_title('Mesure T(1) - Temps d\'exécution Wordcount (n=30)',
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.set_xlim(0, len(iterations)+1)

    # --- Plot 2: Boxplot + Résumé ---
    bp = ax2.boxplot(times_ms, vert=False, patch_artist=True,
                     boxprops=dict(facecolor='#3498db', alpha=0.7),
                     medianprops=dict(color='#e74c3c', linewidth=2))

    ax2.set_xlabel('Temps (ms)', fontsize=12)
    ax2.set_yticks([])
    ax2.set_title('Distribution', fontsize=12)

    # Annotations
    stats_text = f"""
    T(1) = {median:.0f} ms  (médiane)

    Moyenne: {mean:.0f} ms
    Écart-type: {std:.0f} ms
    Q1: {q1:.0f} ms | Q3: {q3:.0f} ms
    Min: {times_ms.min():.0f} ms | Max: {times_ms.max():.0f} ms
    """

    fig.text(0.98, 0.02, stats_text, fontsize=10, family='monospace',
             verticalalignment='bottom', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches='tight')
    print(f"Plot saved: {OUTPUT_FILE}")

    # Afficher résumé
    print("\n" + "="*50)
    print("RÉSULTAT T(1) POUR LE MODÈLE THÉORIQUE")
    print("="*50)
    print(f"T(1) = {median:.0f} ms  (médiane de {len(times_ms)} mesures)")
    print(f"T(1) = {median/1000:.3f} s")
    print("="*50)

if __name__ == "__main__":
    plot_t1_results()
