#!/bin/bash

# Configuration
DATA_FILE="../data/rdf/data.ttl"
ONTOLOGY_FILE="../ontology/vi-ontology.ttl"
FUSEKI_URL="http://localhost:3030/ds/data"
AUTH="admin:admin"

echo "Checking if files exist..."
if [ ! -f "$DATA_FILE" ]; then echo "Error: $DATA_FILE not found"; exit 1; fi
if [ ! -f "$ONTOLOGY_FILE" ]; then echo "Error: $ONTOLOGY_FILE not found"; exit 1; fi

echo "Waiting for Fuseki to start..."
until curl -s -u "$AUTH" http://localhost:3030/$/ping > /dev/null; do
  printf "."
  sleep 2
done
echo " Fuseki is up!"

echo "Loading Ontology..."
STATUS_ONT=$(curl -s -o /dev/null -w "%{http_code}" -u "$AUTH" -X POST -H "Content-Type: text/turtle" -T "$ONTOLOGY_FILE" "$FUSEKI_URL")
echo "Ontology Load Status: $STATUS_ONT"

echo "Loading Data..."
STATUS_DATA=$(curl -s -o /dev/null -w "%{http_code}" -u "$AUTH" -X POST -H "Content-Type: text/turtle" -T "$DATA_FILE" "$FUSEKI_URL")
echo "Data Load Status: $STATUS_DATA"

if [[ "$STATUS_ONT" == "200" || "$STATUS_ONT" == "201" || "$STATUS_ONT" == "204" ]] && \
   [[ "$STATUS_DATA" == "200" || "$STATUS_DATA" == "201" || "$STATUS_DATA" == "204" ]]; then
  echo "✅ Done! Data loaded successfully."
else
  echo "❌ Error: Failed to load data. Check authentication and dataset state."
fi
