#!/usr/bin/env python3
"""
Lance un benchmark pour mesurer T(1) - temps d'exécution avec 1 seul worker.
Utile pour calculer le speedup théorique.
"""
import subprocess
import time
import os
import sys

# Configuration
TARGET_CLUSTER = "nova"      # Cluster cible (nova, ecotype, etc.)
NODES = 2                    # 2 nodes = 1 master + 1 worker
WALLTIME = "00:15:00"        # 15 minutes suffisent pour 1 worker
ITERATIONS = 5               # Nombre de répétitions pour moyenne fiable

HOME_DIR = os.environ['HOME']
SCRIPT_PATH = f"{HOME_DIR}/wordcount-distributed/benchmark_t1_job.sh"

def create_benchmark_script():
    """Crée le script de benchmark pour T(1)."""
    script_content = f'''#!/bin/bash
#
# Benchmark T(1) - Mesure du temps d'exécution avec 1 worker
#

cd {HOME_DIR}/wordcount-distributed

# Fichier de sortie
OUTPUT_FILE="t1_results.csv"

# Créer le header si le fichier n'existe pas
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Iteration,Nodes,Workers,Exec_Time_ms,Total_Time_ms" > "$OUTPUT_FILE"
fi

# Récupérer la liste des noeuds
NODES_LIST=$(cat $OAR_NODEFILE | sort -u)
MASTER=$(echo "$NODES_LIST" | head -1)
WORKER=$(echo "$NODES_LIST" | tail -1)

echo "=== Benchmark T(1) ==="
echo "Master: $MASTER"
echo "Worker: $WORKER"
echo ""

# Compiler si nécessaire
bash deploy/setup.sh > /dev/null 2>&1

# Lancer le worker sur le noeud distant
ssh $WORKER "cd {HOME_DIR}/wordcount-distributed && java -cp bin network.worker.WorkerNode $WORKER 3000" &
WORKER_PID=$!
sleep 3

# Exécuter {ITERATIONS} itérations
for i in $(seq 1 {ITERATIONS}); do
    echo "Iteration $i/{ITERATIONS}..."

    START_TOTAL=$(date +%s%3N)

    # Exécution du wordcount distribué
    java -cp bin scheduler.Main \\
        {HOME_DIR}/wordcount-distributed/test/data_1gb.txt \\
        "[$WORKER:3000]" \\
        > /tmp/run_$i.log 2>&1

    END_TOTAL=$(date +%s%3N)

    TOTAL_TIME=$((END_TOTAL - START_TOTAL))

    # Extraire le temps d'exécution depuis les logs si disponible
    EXEC_TIME=$(grep -oP "Execution time: \\K[0-9]+" /tmp/run_$i.log 2>/dev/null || echo "$TOTAL_TIME")

    echo "$i,2,1,$EXEC_TIME,$TOTAL_TIME" >> "$OUTPUT_FILE"
    echo "  -> Total: ${{TOTAL_TIME}}ms, Exec: ${{EXEC_TIME}}ms"

    sleep 2
done

# Cleanup
kill $WORKER_PID 2>/dev/null

echo ""
echo "=== Résultats T(1) ==="
echo "Fichier: $OUTPUT_FILE"
cat "$OUTPUT_FILE"
echo ""

# Calculer la moyenne
AVG=$(tail -n {ITERATIONS} "$OUTPUT_FILE" | awk -F',' '{{sum+=$5}} END {{print sum/{ITERATIONS}}}')
echo "Moyenne T(1): ${{AVG}}ms"
'''

    with open(SCRIPT_PATH, 'w') as f:
        f.write(script_content)
    os.chmod(SCRIPT_PATH, 0o755)
    print(f"Script créé: {SCRIPT_PATH}")


def main():
    print("=" * 60)
    print("LANCEMENT BENCHMARK T(1) - Temps d'exécution 1 worker")
    print("=" * 60)
    print(f"Cluster cible : {TARGET_CLUSTER}")
    print(f"Nodes         : {NODES} (1 master + 1 worker)")
    print(f"Itérations    : {ITERATIONS}")
    print(f"Walltime      : {WALLTIME}")
    print("-" * 60)

    # Créer le script de benchmark
    create_benchmark_script()

    # Construire la commande oarsub
    cmd = ["oarsub"]

    if TARGET_CLUSTER:
        cmd.extend(["-p", f"cluster='{TARGET_CLUSTER}'"])

    cmd.extend(["-l", f"nodes={NODES},walltime={WALLTIME}"])
    cmd.append(SCRIPT_PATH)

    print(f"\nSoumission du job...")
    print(f"Commande: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            output_lines = result.stdout.splitlines()
            job_id = "Inconnu"
            for line in output_lines:
                if "OAR_JOB_ID" in line:
                    job_id = line.split("=")[1]

            print(f"Job soumis avec succès!")
            print(f"Job ID: {job_id}")
            print()
            print("Suivi:")
            print(f"  oarstat -j {job_id}")
            print(f"  tail -f t1_results.csv")
        else:
            print("ERREUR lors de la soumission")
            print(f"Stderr: {result.stderr.strip()}")
            sys.exit(1)

    except FileNotFoundError:
        print("ERREUR: oarsub non trouvé (pas sur Grid5000?)")
        print()
        print("Pour tester localement, exécutez:")
        print(f"  bash {SCRIPT_PATH}")
        sys.exit(1)
    except Exception as e:
        print(f"Exception: {e}")
        sys.exit(1)

    print("-" * 60)
    print("Une fois terminé, T(1) sera dans t1_results.csv")


if __name__ == "__main__":
    main()
