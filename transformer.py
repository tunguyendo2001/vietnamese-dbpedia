# transformer.py
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD, FOAF
import json
import re
import yaml
import os
from datetime import datetime

class VietnameseRDFTransformer:
    def __init__(self, mapping_file='mapping/infobox_mapping.yaml'):
        self.g = Graph()
        
        # Namespaces
        self.VN_RES = Namespace("http://vi.dbpedia.org/resource/")
        self.VN_ONT = Namespace("http://vi.dbpedia.org/ontology/")
        self.DBO = Namespace("http://dbpedia.org/ontology/")
        self.PROV = Namespace("http://www.w3.org/ns/prov#")
        
        # Bind namespaces for readability in turtle output
        self.g.bind("vn-res", self.VN_RES)
        self.g.bind("vido", self.VN_ONT)
        self.g.bind("dbo", self.DBO)
        self.g.bind("prov", self.PROV)
        self.g.bind("foaf", FOAF)

        # Load Mapping Config
        self.mappings = {}
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
                self.mappings = yaml_data.get('mappings', {})
        else:
            print(f"⚠️ Không tìm thấy file mapping: {mapping_file}")

    def clean_title(self, title):
        cleaned = re.sub(r'[^\w\s-]', '', title)
        cleaned = re.sub(r'\s+', '_', cleaned)
        return cleaned

    def get_uri_from_string(self, prefix_string):
        """Chuyển đổi chuỗi như 'dbo:Person' thành URIRef"""
        if prefix_string.startswith("dbo:"):
            return self.DBO[prefix_string.split(":")[1]]
        elif prefix_string.startswith("foaf:"):
            return FOAF[prefix_string.split(":")[1]]
        elif prefix_string.startswith("rdfs:"):
            return RDFS[prefix_string.split(":")[1]]
        elif prefix_string.startswith("vido:"):
            return self.VN_ONT[prefix_string.split(":")[1]]
        return URIRef(prefix_string)

    def transform_page_to_rdf(self, page_data):
        title = page_data.get('title')
        if not title: return

        resource_uri = self.VN_RES[self.clean_title(title)]
        
        # 1. Gán Nhãn & Tóm tắt
        self.g.add((resource_uri, RDFS.label, Literal(title, lang='vi')))
        if page_data.get('extract'):
            self.g.add((resource_uri, self.DBO.abstract, Literal(page_data['extract'], lang='vi')))

        # 2. Nhận diện Infobox template
        infobox_data = page_data.get('infobox', {})
        infobox_type = page_data.get('infobox_type') # Yêu cầu crawler phải lưu tên của infobox (vd: 'Thông tin nhân vật')

        entity_class_uri = OWL.Thing # Mặc định
        mapping_rules = None

        # Nếu tìm thấy mapping cho infobox này
        if infobox_type and infobox_type in self.mappings:
            mapping_rules = self.mappings[infobox_type]
            class_str = mapping_rules.get('class', '')
            if class_str:
                entity_class_uri = self.get_uri_from_string(class_str)
        
        # Gán Class type chuẩn (rdf:type)
        self.g.add((resource_uri, RDF.type, entity_class_uri))

        # 3. Trích xuất thuộc tính tự động dựa trên mapping
        if mapping_rules:
            prop_mappings = mapping_rules.get('properties', {})
            for key, value in infobox_data.items():
                clean_key = key.lower().strip()
                if clean_key in prop_mappings:
                    prop_uri = self.get_uri_from_string(prop_mappings[clean_key])
                    
                    # Xử lý Date
                    if 'ngày' in clean_key or 'năm' in clean_key:
                        date_val = self.parse_date(value)
                        if date_val:
                            self.g.add((resource_uri, prop_uri, Literal(date_val, datatype=XSD.date)))
                            continue
                    
                    # Gán giá trị text thông thường
                    self.g.add((resource_uri, prop_uri, Literal(value, lang='vi')))

        # Thêm provenance
        self.add_provenance(resource_uri, page_data)

    def parse_date(self, date_string):
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, str(date_string))
            if match:
                try:
                    if '/' in pattern:
                        day, month, year = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        year, month, day = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    continue
        return None

    def add_provenance(self, resource_uri, page_data):
        prov_node = BNode()
        self.g.add((resource_uri, self.PROV.wasDerivedFrom, prov_node))
        self.g.add((prov_node, RDF.type, self.PROV.Entity))
        wiki_url = f"https://vi.wikipedia.org/wiki/{page_data.get('title', '').replace(' ', '_')}"
        self.g.add((prov_node, self.PROV.wasAttributedTo, URIRef(wiki_url)))
        self.g.add((prov_node, self.PROV.generatedAtTime, Literal(datetime.now().isoformat(), datatype=XSD.dateTime)))

    def transform_all_data(self, data_file='vietnamese_wikipedia_data.json'):
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for page_data in data:
            self.transform_page_to_rdf(page_data)
        print(f"Đã chuyển đổi {len(data)} trang thành RDF")
        print(f"Tổng cộng {len(self.g)} triples")

    def save_rdf(self, filename='vietnamese_dbpedia.ttl'):
        self.g.serialize(destination=filename, format='turtle')
        print(f"RDF data đã được lưu vào {filename}")

# Runtime
if __name__ == "__main__":
    transformer = VietnameseRDFTransformer()
    transformer.transform_all_data()
    transformer.save_rdf()
