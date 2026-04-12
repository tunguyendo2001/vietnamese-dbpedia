# entity_linker.py
import requests
import json
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL
import difflib


class DBPediaLinker:
    def __init__(self, vietnamese_graph):
        self.vn_graph = vietnamese_graph
        self.dbpedia_endpoint = "http://dbpedia.org/sparql"
        self.VN_RES = Namespace("http://vi.dbpedia.org/resource/")
        self.DBP_RES = Namespace("http://dbpedia.org/resource/")

    def query_dbpedia(self, query):
        """Query DBPedia SPARQL endpoint"""
        try:
            params = {
                'query': query,
                'format': 'application/sparql-results+json'
            }
            response = requests.get(self.dbpedia_endpoint, params=params)
            return response.json()
        except Exception as e:
            print(f"Lỗi query DBPedia: {e}")
            return None

    def find_english_equivalent(self, vietnamese_title):
        """Tìm equivalent entity trong DBPedia tiếng Anh"""

        # Query tìm entity có tên tương tự
        query = f"""
        SELECT DISTINCT ?entity ?label WHERE {{
            ?entity rdfs:label ?label .
            FILTER (lang(?label) = 'en')
            FILTER (contains(lcase(?label), lcase("{vietnamese_title}")))
        }}
        LIMIT 10
        """

        results = self.query_dbpedia(query)
        if not results:
            return None

        # Tìm match tốt nhất bằng string similarity
        best_match = None
        best_score = 0

        for binding in results['results']['bindings']:
            en_label = binding['label']['value']
            en_uri = binding['entity']['value']

            # Tính similarity score
            score = difflib.SequenceMatcher(None, vietnamese_title.lower(),
                                            en_label.lower()).ratio()

            if score > best_score and score > 0.7:  # Threshold
                best_score = score
                best_match = {
                    'uri': en_uri,
                    'label': en_label,
                    'score': score
                }

        return best_match

    def create_owl_same_as_links(self):
        """Tạo owl:sameAs links"""
        # Lấy tất cả Vietnamese entities
        query = """
        SELECT DISTINCT ?entity ?label WHERE {
            ?entity rdfs:label ?label .
            FILTER (lang(?label) = 'vi')
        }
        """

        # Query Vietnamese graph
        vn_entities = []
        for row in self.vn_graph.query(query):
            vn_entities.append({
                'uri': str(row[0]),
                'label': str(row[1])
            })

        # Tìm equivalent entities
        links_created = 0
        for vn_entity in vn_entities:
            print(f"Đang tìm link cho: {vn_entity['label']}")

            en_match = self.find_english_equivalent(vn_entity['label'])
            if en_match:
                # Thêm owl:sameAs link
                vn_uri = URIRef(vn_entity['uri'])
                en_uri = URIRef(en_match['uri'])

                self.vn_graph.add((vn_uri, OWL.sameAs, en_uri))
                links_created += 1

                print(f"  -> Linked to: {en_match['label']} (score: {en_match['score']:.2f})")

        print(f"Đã tạo {links_created} owl:sameAs links")

    def save_linked_data(self, filename='vietnamese_dbpedia_linked.ttl'):
        """Lưu dữ liệu đã link"""
        self.vn_graph.serialize(destination=filename, format='turtle')
        print(f"Linked data đã được lưu vào {filename}")


# Sử dụng
def create_links_to_english_dbpedia(vietnamese_graph):
    linker = DBPediaLinker(vietnamese_graph)
    linker.create_owl_same_as_links()
    linker.save_linked_data()
    return linker.vn_graph

if __name__ == "__main__":
    create_links_to_english_dbpedia()
