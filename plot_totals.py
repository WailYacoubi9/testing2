#!/usr/bin/env python3
"""
Plot benchmark results: Total Time, Speedup, and Efficiency
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

CSV_FILE = "benchmark_results.csv"
OUTPUT_IMAGE = "benchmark_analysis.png"

def plot_benchmark_analysis():
    print(f"Reading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)

    # Convert to seconds
    df['Total_s'] = df['Total_Time_ms'] / 1000
    df['Split_s'] = df['Split_Time_ms'] / 1000
    df['Exec_s'] = (df['Total_Time_ms'] - df['Distrib_Exec_Start_ms']) / 1000

    # Workers = Nodes - 1 (master doesn't execute)
    df['Workers'] = df['Nodes'] - 1

    # Group by nodes and calculate mean + std
    stats = df.groupby('Nodes').agg({
        'Total_s': ['mean', 'std'],
        'Split_s': ['mean', 'std'],
        'Exec_s': ['mean', 'std'],
        'Workers': 'first'
    }).reset_index()

    stats.columns = ['Nodes', 'Total_mean', 'Total_std', 'Split_mean', 'Split_std',
                     'Exec_mean', 'Exec_std', 'Workers']
    stats = stats.sort_values('Nodes')

    # Calculate speedup (reference: 2 nodes = 1 worker)
    t_ref = stats[stats['Nodes'] == 2]['Total_mean'].values[0]
    stats['Speedup'] = t_ref / stats['Total_mean']
    stats['Speedup_ideal'] = stats['Workers']
    stats['Efficiency'] = (stats['Speedup'] / stats['Workers']) * 100

    print("\n" + "="*70)
    print("BENCHMARK RESULTS SUMMARY")
    print("="*70)
    print(f"{'Nodes':>6} {'Workers':>8} {'Total(s)':>10} {'Speedup':>10} {'Efficiency':>12}")
    print("-"*70)
    for _, row in stats.iterrows():
        print(f"{row['Nodes']:>6} {row['Workers']:>8} {row['Total_mean']:>10.2f} "
              f"{row['Speedup']:>10.2f}x {row['Efficiency']:>11.1f}%")
    print("="*70)

    # Create figure with 4 subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Color scheme
    colors = {'total': '#e74c3c', 'exec': '#3498db', 'split': '#2ecc71',
              'ideal': '#95a5a6', 'speedup': '#9b59b6'}

    # --- PLOT 1: Total Time vs Nodes ---
    ax1 = axes[0, 0]
    ax1.errorbar(stats['Nodes'], stats['Total_mean'], yerr=stats['Total_std'],
                 fmt='o-', color=colors['total'], linewidth=2.5, markersize=8,
                 capsize=5, capthick=2, label='Total Time')
    ax1.set_xlabel('Number of Nodes', fontsize=11)
    ax1.set_ylabel('Time (seconds)', fontsize=11)
    ax1.set_title('Total Execution Time vs Nodes', fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc='upper right')

    # Add min annotation
    min_idx = stats['Total_mean'].idxmin()
    min_val = stats.loc[min_idx, 'Total_mean']
    min_nodes = stats.loc[min_idx, 'Nodes']
    ax1.annotate(f'Min: {min_val:.1f}s\n({int(min_nodes)} nodes)',
                 xy=(min_nodes, min_val), xytext=(min_nodes+2, min_val+3),
                 fontsize=9, arrowprops=dict(arrowstyle='->', color='green'),
                 color='green')

    # --- PLOT 2: Speedup ---
    ax2 = axes[0, 1]
    ax2.plot(stats['Workers'], stats['Speedup_ideal'], '--', color=colors['ideal'],
             linewidth=2, label='Ideal (Linear)')
    ax2.plot(stats['Workers'], stats['Speedup'], 'o-', color=colors['speedup'],
             linewidth=2.5, markersize=8, label='Actual Speedup')
    ax2.fill_between(stats['Workers'], stats['Speedup'], stats['Speedup_ideal'],
                     alpha=0.2, color=colors['speedup'])
    ax2.set_xlabel('Number of Workers', fontsize=11)
    ax2.set_ylabel('Speedup (x)', fontsize=11)
    ax2.set_title('Speedup Analysis', fontsize=12, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend(loc='upper left')

    # --- PLOT 3: Time Breakdown ---
    ax3 = axes[1, 0]
    width = 0.35
    x = np.arange(len(stats))
    ax3.bar(x - width/2, stats['Split_mean'], width, label='Split Time',
            color=colors['split'], alpha=0.8)
    ax3.bar(x + width/2, stats['Exec_mean'], width, label='Execution Time',
            color=colors['exec'], alpha=0.8)
    ax3.set_xlabel('Number of Nodes', fontsize=11)
    ax3.set_ylabel('Time (seconds)', fontsize=11)
    ax3.set_title('Time Breakdown (Split vs Execution)', fontsize=12, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(stats['Nodes'].astype(int))
    ax3.legend()
    ax3.grid(True, linestyle='--', alpha=0.7, axis='y')

    # --- PLOT 4: Efficiency ---
    ax4 = axes[1, 1]
    bars = ax4.bar(stats['Nodes'], stats['Efficiency'], color=colors['speedup'],
                   alpha=0.8, edgecolor='black')
    ax4.axhline(y=100, color='green', linestyle='--', linewidth=2, label='100% Efficiency')
    ax4.axhline(y=50, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='50% Efficiency')
    ax4.set_xlabel('Number of Nodes', fontsize=11)
    ax4.set_ylabel('Efficiency (%)', fontsize=11)
    ax4.set_title('Parallel Efficiency', fontsize=12, fontweight='bold')
    ax4.set_ylim(0, 120)
    ax4.legend(loc='upper right')
    ax4.grid(True, linestyle='--', alpha=0.7, axis='y')

    # Add percentage labels on bars
    for bar, eff in zip(bars, stats['Efficiency']):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                 f'{eff:.0f}%', ha='center', va='bottom', fontsize=9)

    plt.suptitle('Distributed Makefile Benchmark Analysis', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=300, bbox_inches='tight')
    print(f"\nGraph saved: {OUTPUT_IMAGE}")

    # Also save individual plots
    # Total time only
    fig2, ax = plt.subplots(figsize=(10, 6))
    ax.errorbar(stats['Nodes'], stats['Total_mean'], yerr=stats['Total_std'],
                fmt='o-', color=colors['total'], linewidth=2.5, markersize=10,
                capsize=5, capthick=2)
    ax.set_xlabel('Number of Nodes', fontsize=12)
    ax.set_ylabel('Total Time (seconds)', fontsize=12)
    ax.set_title('Total Execution Time vs Number of Nodes', fontsize=14, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.7)
    for i, row in stats.iterrows():
        ax.annotate(f'{row["Total_mean"]:.1f}s',
                    xy=(row['Nodes'], row['Total_mean']),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)
    plt.tight_layout()
    plt.savefig('total_time_plot.png', dpi=300, bbox_inches='tight')
    print(f"Graph saved: total_time_plot.png")

if __name__ == "__main__":
    plot_benchmark_analysis()
