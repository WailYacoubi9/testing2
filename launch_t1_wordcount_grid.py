#!/usr/bin/env python3
"""
Lance la mesure T(1) wordcount sur Grid5000 (1 seul noeud)
Mesure uniquement le temps d'exécution du wordcount sur huge_input.txt
"""
import subprocess
import os
import sys

# Configuration
TARGET_CLUSTER = "nova"
NODES = 1                    # 1 seul noeud suffit
WALLTIME = "00:30:00"        # 30 min pour 30 itérations
ITERATIONS = 30
INPUT_FILE = "huge_input.txt"

HOME_DIR = os.environ['HOME']
SCRIPT_PATH = f"{HOME_DIR}/wordcount-distributed/t1_wordcount_job.sh"

def create_job_script():
    """Crée le script OAR pour mesurer T(1) wordcount."""
    script_content = f'''#!/bin/bash
#
# Mesure T(1) = temps wordcount pur sur Grid5000
#

cd "$HOME/wordcount-distributed"

INPUT_FILE="{INPUT_FILE}"
ITERATIONS={ITERATIONS}
OUTPUT_FILE="t1_wordcount_results.csv"

# Vérifier le fichier
if [ ! -f "$INPUT_FILE" ]; then
    echo "Erreur: $INPUT_FILE non trouvé"
    exit 1
fi

# Compiler wordcount
gcc -O2 -o test/wordcount test/wordcount.c

# Header CSV
echo "iteration,time_ms" > "$OUTPUT_FILE"

echo "=== Mesure T(1) Wordcount sur Grid5000 ==="
echo "Noeud:   $(hostname)"
echo "Fichier: $INPUT_FILE"
echo "Lignes:  $(wc -l < $INPUT_FILE)"
echo "Taille:  $(du -h $INPUT_FILE | cut -f1)"
echo "Itérations: $ITERATIONS"
echo ""

for i in $(seq 1 $ITERATIONS); do
    START=$(date +%s%3N)
    ./test/wordcount "$INPUT_FILE" > /dev/null
    END=$(date +%s%3N)
    TIME_MS=$((END - START))

    echo "$i,$TIME_MS" >> "$OUTPUT_FILE"
    printf "Iteration %2d: %d ms\\n" $i $TIME_MS
done

echo ""
echo "=== Statistiques (n=$ITERATIONS) ==="

tail -n $ITERATIONS "$OUTPUT_FILE" | awk -F',' '
{{
    sum += $2
    sumsq += $2^2
    n++
}}
END {{
    mean = sum/n
    std = sqrt(sumsq/n - mean^2)
    ic95 = 1.96 * std / sqrt(n)
    printf "Moyenne:     %.1f ms\\n", mean
    printf "Ecart-type:  %.1f ms\\n", std
    printf "IC 95%%:      [%.1f, %.1f] ms\\n", mean-ic95, mean+ic95
    printf "\\n"
    printf "T(1) = %.0f ms\\n", mean
    printf "T(1) = %.3f s\\n", mean/1000
}}'

echo ""
echo "Resultats: $OUTPUT_FILE"
'''

    with open(SCRIPT_PATH, 'w') as f:
        f.write(script_content)
    os.chmod(SCRIPT_PATH, 0o755)
    print(f"Script créé: {SCRIPT_PATH}")


def main():
    print("=" * 60)
    print("MESURE T(1) WORDCOUNT SUR GRID5000")
    print("=" * 60)
    print(f"Cluster    : {TARGET_CLUSTER}")
    print(f"Nodes      : {NODES}")
    print(f"Fichier    : {INPUT_FILE}")
    print(f"Itérations : {ITERATIONS}")
    print("-" * 60)

    create_job_script()

    cmd = ["oarsub"]
    if TARGET_CLUSTER:
        cmd.extend(["-p", f"cluster='{TARGET_CLUSTER}'"])
    cmd.extend(["-l", f"nodes={NODES},walltime={WALLTIME}"])
    cmd.append(SCRIPT_PATH)

    print(f"Commande: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            job_id = "?"
            for line in result.stdout.splitlines():
                if "OAR_JOB_ID" in line:
                    job_id = line.split("=")[1]

            print(f"Job soumis! ID: {job_id}")
            print()
            print("Suivi:")
            print(f"  oarstat -j {job_id}")
            print(f"  cat t1_wordcount_results.csv")
        else:
            print(f"ERREUR: {result.stderr.strip()}")
            sys.exit(1)

    except FileNotFoundError:
        print("oarsub non trouvé")
        print(f"Test local: bash {SCRIPT_PATH}")
        sys.exit(1)


if __name__ == "__main__":
    main()
