#!/bin/bash

#Variable Secreta
TOKEN_CURSO="FAE_Usach"

#Variables script

URL="https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
FILE="../datos/raw/titanic.csv"
LOG="errores.log"
OUTPUT="reporte_clases.txt"

#Descargar archivo

wget -O $FILE $URL 2> $LOG

#Primera linea

echo "Reporte generado por: $USER el $(date) - Token: $TOKEN_CURSO" > $OUTPUT

#Pipeline

tail -n +2 $FILE | cut -d',' -f3 | sort | uniq -c | sort -nr >>$OUTPUT
 
