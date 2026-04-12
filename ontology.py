# ontology_builder.py
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD


class VietnameseOntology:
    def __init__(self):
        self.g = Graph()

        # Định nghĩa namespaces
        self.VN_ONT = Namespace("http://vi.dbpedia.org/ontology/")
        self.VN_RES = Namespace("http://vi.dbpedia.org/resource/")
        self.DBP_ONT = Namespace("http://dbpedia.org/ontology/")

        # Bind namespaces
        self.g.bind("vn-ont", self.VN_ONT)
        self.g.bind("vn-res", self.VN_RES)
        self.g.bind("dbp-ont", self.DBP_ONT)
        self.g.bind("owl", OWL)
        self.g.bind("rdfs", RDFS)

    def create_basic_classes(self):
        """Tạo các class cơ bản cho ontology tiếng Việt"""

        # Các class chính
        classes = [
            ("Người", "Person", "Người"),
            ("ĐịaĐiểm", "Place", "Địa điểm"),
            ("TổChức", "Organisation", "Tổ chức"),
            ("Sự Kiện", "Event", "Sự kiện"),
            ("TácPhẩm", "Work", "Tác phẩm"),
            ("Loài", "Species", "Loài sinh vật")
        ]

        for vn_name, en_name, description in classes:
            class_uri = self.VN_ONT[vn_name]
            self.g.add((class_uri, RDF.type, RDFS.Class))
            self.g.add((class_uri, RDFS.label, Literal(description, lang='vi')))
            self.g.add((class_uri, OWL.equivalentClass, self.DBP_ONT[en_name]))

    def create_properties(self):
        """Tạo các property"""

        properties = [
            ("tên", "name", "Tên của đối tượng"),
            ("ngàySinh", "birthDate", "Ngày sinh"),
            ("nơiSinh", "birthPlace", "Nơi sinh"),
            ("nghềNghiệp", "occupation", "Nghề nghiệp"),
            ("thuộcVề", "country", "Thuộc về quốc gia")
        ]

        for vn_prop, en_prop, description in properties:
            prop_uri = self.VN_ONT[vn_prop]
            self.g.add((prop_uri, RDF.type, RDF.Property))
            self.g.add((prop_uri, RDFS.label, Literal(description, lang='vi')))
            self.g.add((prop_uri, OWL.equivalentProperty, self.DBP_ONT[en_prop]))

    def save_ontology(self, filename="vietnamese_ontology.owl"):
        """Lưu ontology ra file"""
        self.g.serialize(destination=filename, format='xml')
        print(f"Ontology đã được lưu vào {filename}")


# Sử dụng
def create_ontology():
    ont = VietnameseOntology()
    ont.create_basic_classes()
    ont.create_properties()
    ont.save_ontology()
    return ont

if __name__ == "__main__":
    create_ontology()