# Vietnamese DBpedia (Mini Version)

A senior-level implementation of a Linked Data pipeline for Vietnamese Wikipedia.

## Features
- **Ontology**: Custom Vietnamese ontology (`vido`) extending DBpedia (`dbo`).
- **Crawler**: Intelligent infobox extraction from Vietnamese Wikipedia.
- **Transformation**: RDF generation (Turtle format) using `rdflib`.
- **Linking**: Cross-lingual linking (`owl:sameAs`) to English DBpedia.
- **SPARQL Endpoint**: Apache Jena Fuseki via Docker.

## Project Structure
```
vietnamese-dbpedia/
├── ontology/           # Ontology definitions (OWL, TTL)
├── crawler/            # Wikipedia data collection
├── mapping/            # Infobox-to-Ontology mapping rules
├── transformer/        # RDF generation logic
├── linking/            # Cross-lingual linking logic
├── data/               # Raw, Processed, and RDF storage
├── sparql/             # Dockerized SPARQL endpoint
├── main.py             # Pipeline orchestrator
└── requirements.txt    # Python dependencies
```

## Setup & Running

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Pipeline
This will fetch ~1000 entities, extract infoboxes, transform to RDF, and link to English DBpedia.
```bash
python main.py
```

### 3. Start SPARQL Endpoint
```bash
cd sparql
docker compose up -d
./load_data.sh
```

## Sample SPARQL Queries

Access the endpoint at `http://localhost:3030/ds/query`.

### 1. List all People
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?person ?name
WHERE {
  ?person a dbo:Person ;
          rdfs:label ?name .
}
LIMIT 20
```

### 2. Find Birth Place
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?person ?birthPlace
WHERE {
  ?person dbo:birthPlace ?birthPlace .
}
```

### 3. Query Vietnamese Dynasties
```sparql
PREFIX vido: <http://vi.dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?dynasty ?label
WHERE {
  ?dynasty a vido:VietnameseDynasty ;
           rdfs:label ?label .
}
```

### 4. Query owl:sameAs links (Cross-lingual)
```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?vi_resource ?en_resource
WHERE {
  ?vi_resource owl:sameAs ?en_resource .
}
LIMIT 10
```

### 5. Count Entities by Type
```sparql
SELECT ?type (COUNT(?s) as ?count)
WHERE {
  ?s a ?type .
}
GROUP BY ?type
```
