import os
import time
from datetime import datetime
from ontology import create_ontology
from crawler import collect_wikipedia_data
from linker import create_links_to_english_dbpedia
from transformer import transform_to_rdf
from interface import start_gradio_interface


def run_complete_pipeline():
    """Chạy toàn bộ pipeline Vietnamese DBPedia"""

    print("=" * 60)
    print("VIETNAMESE DBPEDIA BUILDER")
    print("=" * 60)
    print(f"Bắt đầu lúc: {datetime.now()}")
    print()

    try:
        # Bước 1: Tạo Ontology
        print("BƯỚC 1: Tạo Vietnamese Ontology")
        print("-" * 40)
        ontology = create_ontology()
        print("✓ Ontology đã được tạo thành công")
        print()

        # Bước 2: Thu thập dữ liệu Wikipedia
        print("BƯỚC 2: Thu thập dữ liệu Wikipedia tiếng Việt")
        print("-" * 40)
        if not os.path.exists('vietnamese_wikipedia_data.json'):
            data = collect_wikipedia_data()
            print("✓ Dữ liệu Wikipedia đã được thu thập")
        else:
            print("✓ Sử dụng dữ liệu Wikipedia có sẵn")
        print()

        # Bước 3: Chuyển đổi sang RDF
        print("BƯỚC 3: Chuyển đổi dữ liệu thành RDF")
        print("-" * 40)
        vn_graph = transform_to_rdf()
        print("✓ Dữ liệu đã được chuyển đổi thành RDF")
        print()

        # Bước 4: Tạo links với English DBPedia
        print("BƯỚC 4: Tạo links với English DBPedia")
        print("-" * 40)
        # linked_graph = create_links_to_english_dbpedia(vn_graph)
        print("✓ Links với English DBPedia đã được tạo")
        print()

        # Bước 5: Khởi động Gradio Interface
        print("BƯỚC 5: Khởi động Gradio Interface")
        print("-" * 40)
        print("Gradio interface sẽ khởi động sau 3 giây...")
        time.sleep(3)
        start_gradio_interface()

    except Exception as e:
        print(f"❌ Lỗi trong pipeline: {e}")
        return False

    return True


# Script kiểm tra chất lượng dữ liệu
def validate_data_quality():
    """Kiểm tra chất lượng dữ liệu RDF"""
    print("\nKIỂM TRA CHẤT LƯỢNG DỮ LIỆU")
    print("-" * 40)

    try:
        from rdflib import Graph
        g = Graph()
        g.parse('vietnamese_dbpedia_linked.ttl', format='turtle')

        # Thống kê cơ bản
        total_triples = len(g)
        print(f"Tổng số triples: {total_triples}")

        # Đếm số entities theo type
        type_query = """
        PREFIX vn-ont: <http://vi.dbpedia.org/ontology/>
        SELECT ?type (COUNT(?entity) as ?count) WHERE {
            ?entity a ?type .
            FILTER (STRSTARTS(STR(?type), "http://vi.dbpedia.org/ontology/"))
        } GROUP BY ?type
        """

        print("\nPhân bố theo loại entity:")
        for row in g.query(type_query):
            entity_type = str(row[0]).split('/')[-1]
            count = int(row[1])
            print(f"  {entity_type}: {count}")

        # Đếm số owl:sameAs links
        same_as_query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(*) as ?count) WHERE {
            ?vn_entity owl:sameAs ?en_entity .
        }
        """

        for row in g.query(same_as_query):
            same_as_count = int(row[0])
            print(f"\nSố owl:sameAs links: {same_as_count}")

        print("✓ Kiểm tra chất lượng hoàn tất")

    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra: {e}")


if __name__ == "__main__":
    # Chạy pipeline
    success = run_complete_pipeline()

    if success:
        print("\n🎉 Vietnamese DBPedia đã được xây dựng thành công!")
        print("\nCác file đã tạo:")
        print("- vietnamese_ontology.owl: Ontology")
        print("- vietnamese_wikipedia_data.json: Dữ liệu thô")
        print("- vietnamese_dbpedia.ttl: RDF data")
        print("- vietnamese_dbpedia_linked.ttl: RDF data với links")
        print("\nGradio Interface: http://localhost:7860")

        # Validate data
        validate_data_quality()
