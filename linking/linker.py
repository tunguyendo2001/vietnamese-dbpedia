import json
import os
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import OWL
from urllib.parse import quote

def clean_uri(text):
    return quote(text.replace(" ", "_"))

def main():
    VIR = Namespace("http://vi.dbpedia.org/resource/")
    DBR = Namespace("http://dbpedia.org/resource/")
    
    g = Graph()
    g.parse("data/rdf/data.ttl", format="turtle")
    g.bind("owl", OWL)
    g.bind("dbr", DBR)

    processed_dir = "data/processed"
    files = [f for f in os.listdir(processed_dir) if f.endswith(".json")]
    
    print(f"Establishing links for {len(files)} entities...")
    
    links_added = 0
    for filename in files:
        with open(os.path.join(processed_dir, filename), 'r', encoding='utf-8') as f:
            article = json.load(f)
        
        if article.get('en_title'):
            vi_uri = VIR[clean_uri(article['title'])]
            en_uri = DBR[clean_uri(article['en_title'])]
            g.add((vi_uri, OWL.sameAs, en_uri))
            links_added += 1

    g.serialize(destination="data/rdf/data.ttl", format="turtle")
    print(f"Links established: {links_added}. Updated data/rdf/data.ttl")

if __name__ == "__main__":
    main()
