#!/bin/bash
#
# Mesure T(1) = temps d'exécution wordcount pour 1 worker
# Fichier: huge_input.txt (20M lignes)
#

INPUT_FILE="huge_input.txt"
ITERATIONS=30
OUTPUT_FILE="t1_wordcount_results.csv"

cd "$HOME/wordcount-distributed"

# Vérifier que le fichier existe
if [ ! -f "$INPUT_FILE" ]; then
    echo "Erreur: $INPUT_FILE non trouvé"
    echo "Créer avec: yes \"pomme poire banane...\" | head -n 20000000 > huge_input.txt"
    exit 1
fi

# Compiler wordcount si nécessaire
if [ ! -f "test/wordcount" ]; then
    echo "Compilation de wordcount..."
    gcc -O2 -o test/wordcount test/wordcount.c
fi

# Header CSV
echo "iteration,time_ms" > "$OUTPUT_FILE"

echo "=== Mesure T(1) Wordcount ==="
echo "Fichier: $INPUT_FILE"
echo "Lignes:  $(wc -l < $INPUT_FILE)"
echo "Taille:  $(du -h $INPUT_FILE | cut -f1)"
echo "Itérations: $ITERATIONS"
echo ""

for i in $(seq 1 $ITERATIONS); do
    # Mesure du temps en millisecondes
    START=$(date +%s%3N)

    ./test/wordcount "$INPUT_FILE" > /dev/null

    END=$(date +%s%3N)
    TIME_MS=$((END - START))

    echo "$i,$TIME_MS" >> "$OUTPUT_FILE"
    printf "Iteration %2d: %d ms\n" $i $TIME_MS
done

echo ""
echo "=== Statistiques (n=$ITERATIONS) ==="

# Calcul moyenne, écart-type, IC95%
tail -n $ITERATIONS "$OUTPUT_FILE" | awk -F',' '
{
    sum += $2
    sumsq += $2^2
    n++
}
END {
    mean = sum/n
    std = sqrt(sumsq/n - mean^2)
    ic95 = 1.96 * std / sqrt(n)
    printf "Moyenne:     %.1f ms\n", mean
    printf "Écart-type:  %.1f ms\n", std
    printf "IC 95%%:      [%.1f, %.1f] ms\n", mean-ic95, mean+ic95
    printf "\n"
    printf "T(1) = %.0f ms  (pour le modèle théorique)\n", mean
    printf "T(1) = %.3f s\n", mean/1000
}'

echo ""
echo "Résultats sauvegardés dans: $OUTPUT_FILE"
