import os
import json
import glob
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, OWL, RDFS

def evaluate_project(rdf_file="data/rdf/data.ttl", raw_dir="data/raw", processed_dir="data/processed"):
    print("="*60)
    print("🚀 BÁO CÁO ĐÁNH GIÁ CHẤT LƯỢNG VIETNAMESE DBPEDIA")
    print("="*60)

    # Khởi tạo Graph
    g = Graph()
    has_rdf = False
    if os.path.exists(rdf_file):
        try:
            g.parse(rdf_file, format="turtle")
            has_rdf = True
        except Exception as e:
            print(f"Lỗi khi đọc file RDF: {e}")
    else:
        # Fallback thử đọc file khác nếu đổi tên
        fallback_file = "vietnamese_dbpedia_linked.ttl"
        if os.path.exists(fallback_file):
            g.parse(fallback_file, format="turtle")
            has_rdf = True
            rdf_file = fallback_file

    # ==========================================
    # 1. DEFINE AN ONTOLOGY
    # ==========================================
    print("\n[1] YÊU CẦU 1: DEFINE AN ONTOLOGY")
    print("-" * 40)
    ontology_file = "ontology/vi-ontology.ttl"
    if os.path.exists(ontology_file):
        ont_g = Graph()
        ont_g.parse(ontology_file, format="turtle")
        classes = list(ont_g.subjects(RDF.type, OWL.Class))
        props = list(ont_g.subjects(RDF.type, RDF.Property)) + list(ont_g.subjects(RDF.type, OWL.DatatypeProperty))
        print(f"✅ Tệp ontology tồn tại ({ontology_file})")
        print(f"📊 Số lượng Class tự định nghĩa: {len(classes)}")
        print(f"📊 Số lượng Property tự định nghĩa: {len(props)}")
        if len(classes) == 0 or len(props) == 0:
            print("⚠️ Cảnh báo: Ontology quá sơ sài, cần mở rộng thêm.")
    else:
        print("❌ Không tìm thấy file ontology chuẩn.")

    # ==========================================
    # 2. COLLECT VIETNAMESE ARTICLES
    # ==========================================
    print("\n[2] YÊU CẦU 2: CRAWL DỮ LIỆU WIKIPEDIA")
    print("-" * 40)
    if os.path.exists(raw_dir) and os.path.exists(processed_dir):
        raw_files = glob.glob(f"{raw_dir}/*.json")
        processed_files = glob.glob(f"{processed_dir}/*.json")
        
        has_infobox_count = 0
        has_en_title_count = 0
        
        for pf in processed_files:
            with open(pf, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if len(data.get('infoboxes', [])) > 0:
                    has_infobox_count += 1
                if data.get('en_title'):
                    has_en_title_count += 1

        total = len(raw_files)
        if total > 0:
            print(f"✅ Đã crawl thành công: {total} bài viết")
            print(f"📊 Tỷ lệ bài có Infobox: {has_infobox_count}/{total} ({(has_infobox_count/total)*100:.1f}%)")
            print(f"📊 Tỷ lệ bài có link tiếng Anh (en_title): {has_en_title_count}/{total} ({(has_en_title_count/total)*100:.1f}%)")
            if (has_infobox_count/total) < 0.5:
                print("⚠️ Cảnh báo: Tỷ lệ trích xuất infobox thấp. Mất nhiều dữ liệu cấu trúc.")
    else:
        print("❌ Không tìm thấy thư mục data/raw hoặc data/processed.")

    # ==========================================
    # 3. TRANSFORM DATA TO 4* STANDARD
    # ==========================================
    print("\n[3] YÊU CẦU 3: TRANSFORM SANG CHUẨN 4* (RDF/URI)")
    print("-" * 40)
    if has_rdf:
        total_triples = len(g)
        
        # Đếm số lượng entity (subject)
        q_subjects = "SELECT (COUNT(DISTINCT ?s) AS ?c) WHERE { ?s ?p ?o }"
        num_subjects = int(list(g.query(q_subjects))[0][0])
        
        # Đếm số entity có rdf:type
        q_types = "SELECT (COUNT(DISTINCT ?s) AS ?c) WHERE { ?s a ?type }"
        num_typed = int(list(g.query(q_types))[0][0])
        
        # Đếm số entity có attributes thực sự (khác label, type, sameAs)
        q_props = """
        SELECT (COUNT(DISTINCT ?s) AS ?c) WHERE { 
            ?s ?p ?o .
            FILTER (?p NOT IN (
                <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>, 
                <http://www.w3.org/2000/01/rdf-schema#label>, 
                <http://www.w3.org/2002/07/owl#sameAs>
            ))
        }"""
        num_with_props = int(list(g.query(q_props))[0][0])

        print(f"✅ Dữ liệu RDF/Turtle khả dụng")
        print(f"📊 Tổng số Triples: {total_triples}")
        print(f"📊 Tổng số Entities (Subjects): {num_subjects}")
        
        if num_subjects > 0:
            print(f"📊 Trung bình: {total_triples/num_subjects:.1f} triples/entity")
            print(f"📊 Entity có định nghĩa Class (rdf:type): {num_typed}/{num_subjects} ({(num_typed/num_subjects)*100:.1f}%)")
            print(f"📊 Entity có trích xuất thuộc tính (Properties): {num_with_props}/{num_subjects} ({(num_with_props/num_subjects)*100:.1f}%)")
            
            # 4★ check: ratio of URI-valued object properties vs Literals
            q_uri_obj = """
            SELECT (COUNT(*) AS ?c) WHERE {
                ?s ?p ?o .
                FILTER(isURI(?o))
                FILTER(?p NOT IN (
                    <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>,
                    <http://www.w3.org/2002/07/owl#sameAs>
                ))
            }"""
            q_lit_obj = """
            SELECT (COUNT(*) AS ?c) WHERE {
                ?s ?p ?o .
                FILTER(isLiteral(?o))
                FILTER(?p NOT IN (<http://www.w3.org/2000/01/rdf-schema#label>))
            }"""
            num_uri_vals = int(list(g.query(q_uri_obj))[0][0])
            num_lit_vals = int(list(g.query(q_lit_obj))[0][0])
            total_vals = num_uri_vals + num_lit_vals
            uri_ratio = (num_uri_vals / total_vals * 100) if total_vals > 0 else 0
            print(f"\n📊 [4★ Chuẩn] Giá trị là URI (Linked): {num_uri_vals}")
            print(f"📊 [4★ Chuẩn] Giá trị là Literal (chuỗi): {num_lit_vals}")
            print(f"📊 [4★ Chuẩn] Tỷ lệ URI/tổng giá trị: {uri_ratio:.1f}%")
            if uri_ratio >= 30:
                print(f"✅ Đạt chuẩn 4★: Dữ liệu sử dụng URI để định danh thực thể")
            else:
                print(f"⚠️ Chưa đạt chuẩn 4★: Tỷ lệ URI thấp, nhiều giá trị vẫn là chuỗi văn bản")

            if (num_with_props/num_subjects) < 0.2:
                print("❌ Lỗi nghiêm trọng: Transform quá yếu, hơn 80% entity không có thuộc tính dữ liệu thực.")
    else:
        print("❌ Không có dữ liệu RDF để đánh giá.")

    # ==========================================
    # 4. CROSS-LINGUAL LINKING (5* STANDARD)
    # ==========================================
    print("\n[4] YÊU CẦU 4: LINK VỚI ENGLISH DBPEDIA")
    print("-" * 40)
    if has_rdf:
        q_links = """
        SELECT ?s ?o WHERE { 
            ?s <http://www.w3.org/2002/07/owl#sameAs> ?o .
            FILTER(STRSTARTS(STR(?o), "http://dbpedia.org/resource/"))
        }"""
        links = list(g.query(q_links))
        
        valid_links = 0
        self_links = 0
        for row in links:
            # A true self-link is when the full URIs are identical.
            # vir:X owl:sameAs dbr:X is NOT a self-link (different namespaces).
            if str(row[0]) == str(row[1]):
                self_links += 1
            else:
                valid_links += 1

        print(f"📊 Tổng số owl:sameAs links: {len(links)}")
        print(f"✅ Liên kết chéo ngôn ngữ hợp lệ (Khác tên): {valid_links}")
        if self_links > 0:
            print(f"⚠️ Cảnh báo: Phát hiện {self_links} liên kết tự tham chiếu (Self-links). Cần sửa code linker.py.")
    else:
         print("❌ Không có dữ liệu RDF.")

    # ==========================================
    # 5. SPARQL ENDPOINT & INTERFACE
    # ==========================================
    print("\n[5] YÊU CẦU 5: GIAO DIỆN SPARQL / UI")
    print("-" * 40)
    has_docker = os.path.exists("sparql/docker-compose.yml")
        
    if has_docker:
        print("✅ Giao diện Endpoint (M2M): Tồn tại (Apache Jena Fuseki Docker)")
    else:
        print("⚠️ Endpoint (M2M): Không tìm thấy cấu hình Docker SPARQL")

    print("\n" + "="*60)
    print("HOÀN TẤT ĐÁNH GIÁ")

if __name__ == "__main__":
    # Cài đặt rdflib nếu chưa có: pip install rdflib
    evaluate_project()
    