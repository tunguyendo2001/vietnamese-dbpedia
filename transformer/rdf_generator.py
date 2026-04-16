import json
import os
import yaml
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import FOAF, RDFS, XSD, OWL
from urllib.parse import quote

def clean_uri(text):
    return quote(text.replace(" ", "_"))

def main():
    DBO = Namespace("http://dbpedia.org/ontology/")
    VIDO = Namespace("http://vi.dbpedia.org/ontology/")
    VIR = Namespace("http://vi.dbpedia.org/resource/")
    
    g = Graph()
    g.bind("dbo", DBO)
    g.bind("vido", VIDO)
    g.bind("vir", VIR)
    g.bind("foaf", FOAF)
    g.bind("rdfs", RDFS)
    g.bind("owl", OWL)

    with open("mapping/infobox_mapping.yaml", 'r', encoding='utf-8') as f:
        mapping = yaml.safe_load(f)['mappings']

    # Build case-insensitive lookup for template names
    mapping_lower = {k.lower(): v for k, v in mapping.items()}

    processed_dir = "data/processed"
    files = [f for f in os.listdir(processed_dir) if f.endswith(".json")]
    
    print(f"Generating RDF from {len(files)} files...")
    
    for filename in files:
        with open(os.path.join(processed_dir, filename), 'r', encoding='utf-8') as f:
            article = json.load(f)
        
        subject_uri = VIR[clean_uri(article['title'])]
        g.add((subject_uri, RDFS.label, Literal(article['title'], lang='vi')))
        
        for ib in article['infoboxes']:
            template_name = ib['template']
            
            # Try exact match first, then case-insensitive
            map_rule = mapping.get(template_name)
            if not map_rule:
                map_rule = mapping_lower.get(template_name.lower())
            
            if map_rule:
                # Set class
                class_uri = map_rule['class']
                if class_uri.startswith("dbo:"):
                    g.add((subject_uri, RDF.type, DBO[class_uri[4:]]))
                elif class_uri.startswith("vido:"):
                    g.add((subject_uri, RDF.type, VIDO[class_uri[5:]]))
                
                # Set properties
                for key, value in ib['data'].items():
                    if key in map_rule['properties']:
                        prop_uri = map_rule['properties'][key]
                        
                        # Handle basic prefixing
                        if prop_uri.startswith("dbo:"):
                            p = DBO[prop_uri[4:]]
                        elif prop_uri.startswith("foaf:"):
                            p = FOAF[prop_uri[5:]]
                        elif prop_uri.startswith("rdfs:"):
                            p = RDFS[prop_uri[5:]]
                        elif prop_uri.startswith("vido:"):
                            p = VIDO[prop_uri[5:]]
                        else:
                            continue
                        
                        # Attempt to clean value (remove [[ ]])
                        clean_val = value.replace("[[", "").replace("]]", "").split("|")[0].strip()
                        if clean_val:
                            g.add((subject_uri, p, Literal(clean_val)))

    os.makedirs("data/rdf", exist_ok=True)
    g.serialize(destination="data/rdf/data.ttl", format="turtle")
    print("RDF generated: data/rdf/data.ttl")

if __name__ == "__main__":
    main()
