# rdf_transformer.py
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD, FOAF
import json
import re
from datetime import datetime


class VietnameseRDFTransformer:
    def __init__(self, ontology):
        self.g = Graph()
        self.ontology = ontology

        # Namespaces
        self.VN_RES = Namespace("http://vi.dbpedia.org/resource/")
        self.VN_ONT = Namespace("http://vi.dbpedia.org/ontology/")
        self.DBP_RES = Namespace("http://dbpedia.org/resource/")
        self.PROV = Namespace("http://www.w3.org/ns/prov#")

        # Bind namespaces
        self.g.bind("vn-res", self.VN_RES)
        self.g.bind("vn-ont", self.VN_ONT)
        self.g.bind("dbp-res", self.DBP_RES)
        self.g.bind("prov", self.PROV)
        self.g.bind("foaf", FOAF)

    def clean_title(self, title):
        """Làm sạch title để tạo URI"""
        # Loại bỏ ký tự đặc biệt, thay space bằng _
        cleaned = re.sub(r'[^\w\s-]', '', title)
        cleaned = re.sub(r'\s+', '_', cleaned)
        return cleaned

    def detect_entity_type(self, page_data):
        """Xác định loại entity dựa vào category và infobox"""
        category = page_data.get('category', '').lower()
        title = page_data.get('title', '').lower()
        infobox = page_data.get('infobox', {})

        # Logic đơn giản để phân loại
        if 'nhân vật' in category or 'người' in category:
            return self.VN_ONT.Người
        elif 'thành phố' in category or 'địa điểm' in category:
            return self.VN_ONT.ĐịaĐiểm
        elif 'trường' in category or 'đại học' in category:
            return self.VN_ONT.TổChức
        elif 'công ty' in category:
            return self.VN_ONT.TổChức
        else:
            return self.VN_ONT.Thing  # Default class

    def transform_page_to_rdf(self, page_data):
        """Chuyển đổi một trang Wikipedia thành RDF"""
        title = page_data.get('title')
        if not title:
            return

        # Tạo URI cho resource
        resource_uri = self.VN_RES[self.clean_title(title)]

        # Thêm basic triples
        entity_type = self.detect_entity_type(page_data)
        self.g.add((resource_uri, RDF.type, entity_type))
        self.g.add((resource_uri, RDFS.label, Literal(title, lang='vi')))

        # Thêm abstract
        if page_data.get('extract'):
            self.g.add((resource_uri, self.VN_ONT.abstract,
                        Literal(page_data['extract'], lang='vi')))

        # Xử lý infobox
        self.transform_infobox(resource_uri, page_data.get('infobox', {}))

        # Thêm categories
        for category in page_data.get('categories', []):
            if category.startswith('Thể loại:'):
                category_name = category.replace('Thể loại:', '')
                category_uri = self.VN_RES[self.clean_title(category_name)]
                self.g.add((resource_uri, self.VN_ONT.category, category_uri))

        # Thêm provenance (4* standard)
        self.add_provenance(resource_uri, page_data)

    def transform_infobox(self, resource_uri, infobox_data):
        """Chuyển đổi dữ liệu infobox"""
        property_mapping = {
            'tên': self.VN_ONT.tên,
            'ngày sinh': self.VN_ONT.ngàySinh,
            'nơi sinh': self.VN_ONT.nơiSinh,
            'nghề nghiệp': self.VN_ONT.nghềNghiệp,
            'quốc gia': self.VN_ONT.thuộcVề
        }

        for key, value in infobox_data.items():
            if key.lower() in property_mapping:
                prop = property_mapping[key.lower()]

                # Kiểm tra xem value có phải là date không
                if 'ngày' in key.lower():
                    # Parse date
                    date_value = self.parse_date(value)
                    if date_value:
                        self.g.add((resource_uri, prop, Literal(date_value, datatype=XSD.date)))
                else:
                    self.g.add((resource_uri, prop, Literal(value, lang='vi')))

    def parse_date(self, date_string):
        """Parse date từ string"""
        # Đơn giản hóa - chỉ xử lý format cơ bản
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # dd/mm/yyyy
            r'(\d{4})-(\d{1,2})-(\d{1,2})'  # yyyy-mm-dd
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_string)
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
        """Thêm thông tin provenance (4* standard)"""
        # Tạo provenance node
        prov_node = BNode()
        self.g.add((resource_uri, self.PROV.wasDerivedFrom, prov_node))
        self.g.add((prov_node, RDF.type, self.PROV.Entity))

        # Wikipedia source
        wiki_url = f"https://vi.wikipedia.org/wiki/{page_data.get('title', '').replace(' ', '_')}"
        self.g.add((prov_node, self.PROV.wasAttributedTo, URIRef(wiki_url)))

        # Timestamp
        now = datetime.now().isoformat()
        self.g.add((prov_node, self.PROV.generatedAtTime,
                    Literal(now, datatype=XSD.dateTime)))

    def transform_all_data(self, data_file='vietnamese_wikipedia_data.json'):
        """Chuyển đổi toàn bộ dữ liệu"""
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for page_data in data:
            self.transform_page_to_rdf(page_data)

        print(f"Đã chuyển đổi {len(data)} trang thành RDF")
        print(f"Tổng cộng {len(self.g)} triples")

    def save_rdf(self, filename='vietnamese_dbpedia.ttl'):
        """Lưu RDF data"""
        self.g.serialize(destination=filename, format='turtle')
        print(f"RDF data đã được lưu vào {filename}")


# Sử dụng
def transform_to_rdf():
    # Load ontology
    from ontology import create_ontology
    ontology = create_ontology()  # Từ bước 1

    # Transform data
    transformer = VietnameseRDFTransformer(ontology)
    transformer.transform_all_data()
    transformer.save_rdf()

    return transformer.g