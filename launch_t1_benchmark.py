#!/usr/bin/env python3
"""
Lance un benchmark pour mesurer T(1) - temps d'exécution avec 1 seul worker.
Utilise exactement la même méthode que benchmark_job.sh
"""
import subprocess
import time
import os
import sys

# Configuration
TARGET_CLUSTER = "nova"
NODES = 2                    # 2 nodes = 1 master + 1 worker
WALLTIME = "01:00:00"        # 1 heure pour 30 itérations
ITERATIONS = 30              # Minimum pour significativité statistique
INPUT_FILE = "huge_input.txt"  # Même fichier que benchmark_job.sh

HOME_DIR = os.environ['HOME']
SCRIPT_PATH = f"{HOME_DIR}/wordcount-distributed/benchmark_t1_job.sh"

def create_benchmark_script():
    """Crée le script de benchmark pour T(1) - identique à benchmark_job.sh."""
    script_content = f'''#!/bin/bash
#
# Benchmark T(1) - Mesure du temps d'exécution avec 1 worker
# Utilise exactement la même méthode que benchmark_job.sh
#

PROJECT_DIR="$HOME/wordcount-distributed"
INPUT_FILE="{INPUT_FILE}"
CSV_FILE="$PROJECT_DIR/t1_results.csv"
ITERATIONS={ITERATIONS}

cd "$PROJECT_DIR"

# En-tête du CSV (même format que benchmark_job.sh)
if [ ! -f "$CSV_FILE" ]; then
    echo "Nodes,Iteration,Split_Time_ms,Distrib_Exec_Start_ms,Total_Time_ms" > "$CSV_FILE"
fi

NODE_COUNT=$(cat $OAR_NODEFILE | uniq | wc -l)
echo "=== Benchmark T(1) - $NODE_COUNT noeuds ($ITERATIONS iterations) ==="

for ((i=1; i<=ITERATIONS; i++)); do
    echo "------------------------------------------------"
    echo "Iteration $i/$ITERATIONS..."

    # Appel du MÊME script que benchmark_job.sh
    OUTPUT=$(bash deploy/run_nfs_home.sh "$INPUT_FILE" 2>&1)

    if echo "$OUTPUT" | grep -q "Execution completed!"; then

        # Parsing identique à benchmark_job.sh
        T_SPLIT=$(echo "$OUTPUT" | grep "FILE_SPLITTED" | awk '{{print $3}}' | tr -d 'ms')
        T_TOTAL=$(echo "$OUTPUT" | grep "EXECUTION_COMPLETED" | awk '{{print $3}}' | tr -d 'ms')
        T_EXEC_START=$(echo "$OUTPUT" | grep "DISTRIBUTED_EXECUTION_START" | awk '{{print $3}}' | tr -d 'ms')

        # Sécurité valeur vide
        [ -z "$T_SPLIT" ] && T_SPLIT=0
        [ -z "$T_TOTAL" ] && T_TOTAL=0
        [ -z "$T_EXEC_START" ] && T_EXEC_START=0

        # Temps d'exécution pure = Total - Exec_Start
        T_EXEC=$((T_TOTAL - T_EXEC_START))

        echo "Succes : Split=${{T_SPLIT}}ms, Exec=${{T_EXEC}}ms, Total=${{T_TOTAL}}ms"
        echo "$NODE_COUNT,$i,$T_SPLIT,$T_EXEC_START,$T_TOTAL" >> "$CSV_FILE"
    else
        echo "Echec iteration $i"
        echo "$OUTPUT" > "error_t1_iter_${{i}}.txt"
    fi

    sleep 5
done

echo ""
echo "=== Résultats T(1) ==="
cat "$CSV_FILE"
echo ""

# Calculer les statistiques (moyenne, écart-type, intervalle de confiance 95%)
echo "=== Statistiques (n={ITERATIONS}) ==="

# Fonction awk pour calculer mean, std, IC95
calc_stats() {{
    awk -F',' -v col=$1 'NR>1 {{
        sum += $col
        sumsq += ($col)^2
        n++
    }} END {{
        mean = sum/n
        std = sqrt(sumsq/n - mean^2)
        ic95 = 1.96 * std / sqrt(n)
        printf "%.1f ± %.1f (IC95: [%.1f, %.1f])\\n", mean, std, mean-ic95, mean+ic95
    }}'
}}

echo -n "T(1) Total:  "
tail -n {ITERATIONS} "$CSV_FILE" | awk -F',' '{{print $5}}' | awk '{{sum+=$1; sumsq+=$1^2; n++}} END {{
    mean=sum/n; std=sqrt(sumsq/n - mean^2); ic95=1.96*std/sqrt(n)
    printf "%.1f ± %.1f ms (IC95: [%.1f, %.1f])\\n", mean, std, mean-ic95, mean+ic95
}}'

echo -n "T(1) Split:  "
tail -n {ITERATIONS} "$CSV_FILE" | awk -F',' '{{print $3}}' | awk '{{sum+=$1; sumsq+=$1^2; n++}} END {{
    mean=sum/n; std=sqrt(sumsq/n - mean^2); ic95=1.96*std/sqrt(n)
    printf "%.1f ± %.1f ms (IC95: [%.1f, %.1f])\\n", mean, std, mean-ic95, mean+ic95
}}'

echo -n "T(1) Exec:   "
tail -n {ITERATIONS} "$CSV_FILE" | awk -F',' '{{print $5-$4}}' | awk '{{sum+=$1; sumsq+=$1^2; n++}} END {{
    mean=sum/n; std=sqrt(sumsq/n - mean^2); ic95=1.96*std/sqrt(n)
    printf "%.1f ± %.1f ms (IC95: [%.1f, %.1f])\\n", mean, std, mean-ic95, mean+ic95
}}'

echo ""
echo "=== Résumé pour le modèle théorique ==="
AVG_EXEC=$(tail -n {ITERATIONS} "$CSV_FILE" | awk -F',' '{{sum+=($5-$4)}} END {{printf "%.0f", sum/{ITERATIONS}}}')
echo "T(1) = ${{AVG_EXEC}} ms  (temps d'exécution séquentiel)"
'''

    with open(SCRIPT_PATH, 'w') as f:
        f.write(script_content)
    os.chmod(SCRIPT_PATH, 0o755)
    print(f"Script créé: {SCRIPT_PATH}")


def main():
    print("=" * 60)
    print("BENCHMARK T(1) - Temps d'exécution avec 1 worker")
    print("=" * 60)
    print(f"Cluster       : {TARGET_CLUSTER}")
    print(f"Nodes         : {NODES} (1 master + 1 worker)")
    print(f"Fichier       : {INPUT_FILE} (même que benchmark_job.sh)")
    print(f"Itérations    : {ITERATIONS}")
    print(f"Méthode       : deploy/run_nfs_home.sh (identique)")
    print("-" * 60)

    create_benchmark_script()

    cmd = ["oarsub"]
    if TARGET_CLUSTER:
        cmd.extend(["-p", f"cluster='{TARGET_CLUSTER}'"])
    cmd.extend(["-l", f"nodes={NODES},walltime={WALLTIME}"])
    cmd.append(SCRIPT_PATH)

    print(f"\nCommande: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            job_id = "Inconnu"
            for line in result.stdout.splitlines():
                if "OAR_JOB_ID" in line:
                    job_id = line.split("=")[1]

            print(f"Job soumis! ID: {job_id}")
            print()
            print("Suivi:")
            print(f"  oarstat -j {job_id}")
            print(f"  tail -f t1_results.csv")
        else:
            print(f"ERREUR: {result.stderr.strip()}")
            sys.exit(1)

    except FileNotFoundError:
        print("oarsub non trouvé - pas sur Grid5000?")
        print(f"Pour tester: bash {SCRIPT_PATH}")
        sys.exit(1)

    print("-" * 60)
    print("Résultats dans: t1_results.csv")


if __name__ == "__main__":
    main()
