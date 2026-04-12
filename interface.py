# gradio_sparql_interface.py
import gradio as gr
import pandas as pd
from rdflib import Graph
import json
import io
import time
from datetime import datetime


class VietnameseDBPediaGradioInterface:
    def __init__(self, rdf_file='vietnamese_dbpedia_linked.ttl'):
        self.graph = Graph()
        self.rdf_file = rdf_file
        self.load_data()

        # Example queries với nhiều ví dụ thực tế
        self.example_queries = {
            "🙋‍♂️ Tất cả người (Person)": """PREFIX vn-res: <http://vi.dbpedia.org/resource/>
PREFIX vn-ont: <http://vi.dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?person ?name ?birthDate ?occupation WHERE {
    ?person a vn-ont:Người .
    ?person rdfs:label ?name .
    OPTIONAL { ?person vn-ont:ngàySinh ?birthDate }
    OPTIONAL { ?person vn-ont:nghềNghiệp ?occupation }
    FILTER (lang(?name) = 'vi')
} 
ORDER BY ?name
LIMIT 15""",

            "🏢 Tất cả tổ chức (Organization)": """PREFIX vn-res: <http://vi.dbpedia.org/resource/>
PREFIX vn-ont: <http://vi.dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?org ?name ?country ?category WHERE {
    ?org a vn-ont:TổChức .
    ?org rdfs:label ?name .
    OPTIONAL { ?org vn-ont:thuộcVề ?country }
    OPTIONAL { ?org vn-ont:category ?category }
    FILTER (lang(?name) = 'vi')
} 
ORDER BY ?name
LIMIT 15""",

            "🏛️ Tất cả địa điểm (Places)": """PREFIX vn-res: <http://vi.dbpedia.org/resource/>
PREFIX vn-ont: <http://vi.dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?place ?name ?abstract WHERE {
    ?place a vn-ont:ĐịaĐiểm .
    ?place rdfs:label ?name .
    OPTIONAL { ?place vn-ont:abstract ?abstract }
    FILTER (lang(?name) = 'vi')
} 
ORDER BY ?name
LIMIT 15""",

            "🔗 Entities có liên kết DBPedia EN": """PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX vn-ont: <http://vi.dbpedia.org/ontology/>

SELECT ?vn_entity ?vn_name ?en_entity ?type WHERE {
    ?vn_entity owl:sameAs ?en_entity .
    ?vn_entity rdfs:label ?vn_name .
    ?vn_entity a ?type .
    FILTER (lang(?vn_name) = 'vi')
    FILTER (STRSTARTS(STR(?type), "http://vi.dbpedia.org/ontology/"))
} 
ORDER BY ?vn_name
LIMIT 20""",

            "📊 Thống kê theo loại entity": """PREFIX vn-ont: <http://vi.dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?type ?typeName (COUNT(?entity) as ?count) WHERE {
    ?entity a ?type .
    ?type rdfs:label ?typeName .
    FILTER (STRSTARTS(STR(?type), "http://vi.dbpedia.org/ontology/"))
    FILTER (lang(?typeName) = 'vi')
} 
GROUP BY ?type ?typeName 
ORDER BY DESC(?count)""",

            "🎓 Tìm trường đại học": """PREFIX vn-res: <http://vi.dbpedia.org/resource/>
PREFIX vn-ont: <http://vi.dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?university ?name ?abstract WHERE {
    ?university a vn-ont:TổChức .
    ?university rdfs:label ?name .
    ?university vn-ont:category ?cat .
    ?university vn-ont:abstract ?abstract .
    FILTER (CONTAINS(LCASE(STR(?cat)), "đại học") || CONTAINS(LCASE(?name), "đại học"))
    FILTER (lang(?name) = 'vi')
} 
ORDER BY ?name
LIMIT 10""",

            "🌍 Tìm thành phố Việt Nam": """PREFIX vn-res: <http://vi.dbpedia.org/resource/>
PREFIX vn-ont: <http://vi.dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?city ?name ?abstract WHERE {
    ?city a vn-ont:ĐịaĐiểm .
    ?city rdfs:label ?name .
    ?city vn-ont:category ?cat .
    OPTIONAL { ?city vn-ont:abstract ?abstract }
    FILTER (CONTAINS(LCASE(STR(?cat)), "thành phố"))
    FILTER (lang(?name) = 'vi')
} 
ORDER BY ?name
LIMIT 15""",

            "🏪 Tìm công ty Việt Nam": """PREFIX vn-res: <http://vi.dbpedia.org/resource/>
PREFIX vn-ont: <http://vi.dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?company ?name ?abstract WHERE {
    ?company a vn-ont:TổChức .
    ?company rdfs:label ?name .
    ?company vn-ont:category ?cat .
    OPTIONAL { ?company vn-ont:abstract ?abstract }
    FILTER (CONTAINS(LCASE(STR(?cat)), "công ty"))
    FILTER (lang(?name) = 'vi')
} 
ORDER BY ?name
LIMIT 10"""
        }

    def load_data(self):
        """Load RDF data with progress tracking"""
        try:
            print("🔄 Đang load RDF data...")
            start_time = time.time()
            self.graph.parse(self.rdf_file, format='turtle')
            load_time = time.time() - start_time
            print(f"✅ Đã load {len(self.graph):,} triples trong {load_time:.2f}s")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi load dữ liệu: {e}")
            return False

    def execute_sparql_query(self, query, output_format="Table", progress=gr.Progress()):
        """Execute SPARQL query với progress bar"""
        if not query.strip():
            return "⚠️ Vui lòng nhập SPARQL query", None, "Không có query", ""

        try:
            progress(0, desc="Đang thực thi query...")
            start_time = time.time()

            # Execute query
            results = self.graph.query(query)

            progress(0.5, desc="Đang xử lý kết quả...")

            # Handle different types of queries
            if not results.vars:  # ASK query hoặc CONSTRUCT
                if hasattr(results, '__bool__'):  # ASK query
                    execution_time = time.time() - start_time
                    status = f"✅ ASK query hoàn thành trong {execution_time:.3f}s"
                    result_text = f"Kết quả ASK query: {bool(results)}"
                    return status, None, result_text, ""
                else:  # CONSTRUCT query
                    execution_time = time.time() - start_time
                    status = f"✅ CONSTRUCT query hoàn thành trong {execution_time:.3f}s"
                    return status, None, "CONSTRUCT query executed", ""

            # Convert to list of dicts
            result_list = []
            for row in results:
                row_dict = {}
                for i, var in enumerate(results.vars):
                    value = str(row[i]) if row[i] else ""
                    # Clean up URIs để dễ đọc
                    if value.startswith("http://vi.dbpedia.org/resource/"):
                        value = value.replace("http://vi.dbpedia.org/resource/", "vn:")
                    elif value.startswith("http://dbpedia.org/resource/"):
                        value = value.replace("http://dbpedia.org/resource/", "dbp:")
                    row_dict[str(var)] = value
                result_list.append(row_dict)

            execution_time = time.time() - start_time

            if not result_list:
                status = f"✅ Query thành công trong {execution_time:.3f}s - Không có kết quả"
                return status, None, "Không có dữ liệu phù hợp với query", ""

            progress(0.8, desc="Đang format kết quả...")

            # Format theo yêu cầu
            if output_format == "Table":
                df = pd.DataFrame(result_list)
                status = f"✅ Tìm thấy {len(result_list)} kết quả trong {execution_time:.3f}s"
                return status, df, "", f"📊 {len(result_list)} rows × {len(df.columns)} columns"

            elif output_format == "JSON":
                json_result = json.dumps(result_list, ensure_ascii=False, indent=2)
                status = f"✅ Tìm thấy {len(result_list)} kết quả trong {execution_time:.3f}s"
                return status, None, json_result, f"📄 {len(result_list)} objects in JSON format"

            elif output_format == "CSV":
                df = pd.DataFrame(result_list)
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_result = csv_buffer.getvalue()
                status = f"✅ Tìm thấy {len(result_list)} kết quả trong {execution_time:.3f}s"
                return status, None, csv_result, f"📄 {len(result_list)} rows in CSV format"

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"❌ Lỗi sau {execution_time:.3f}s: {str(e)}"
            return error_msg, None, str(e), "Query failed"

    def load_example_query(self, example_name):
        """Load example query"""
        if example_name in self.example_queries:
            return self.example_queries[example_name]
        return ""

    def get_data_stats(self):
        """Lấy thống kê chi tiết về dữ liệu"""
        try:
            # Tổng số triples
            total_triples = len(self.graph)

            # Đếm số entities theo type
            type_query = """
            PREFIX vn-ont: <http://vi.dbpedia.org/ontology/>
            SELECT ?type (COUNT(?entity) as ?count) WHERE {
                ?entity a ?type .
                FILTER (STRSTARTS(STR(?type), "http://vi.dbpedia.org/ontology/"))
            } GROUP BY ?type ORDER BY DESC(?count)
            """

            type_results = list(self.graph.query(type_query))
            type_stats = []
            total_entities = 0

            for row in type_results:
                entity_type = str(row[0]).split('/')[-1]
                count = int(row[1])
                total_entities += count
                type_stats.append(f"   • **{entity_type}**: {count:,}")

            # Đếm owl:sameAs links
            sameAs_query = """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            SELECT (COUNT(*) as ?count) WHERE {
                ?vn_entity owl:sameAs ?en_entity .
            }
            """

            sameAs_results = list(self.graph.query(sameAs_query))
            sameAs_count = int(sameAs_results[0][0]) if sameAs_results else 0

            # Đếm properties
            prop_query = """
            SELECT (COUNT(DISTINCT ?p) as ?count) WHERE {
                ?s ?p ?o .
            }
            """
            prop_results = list(self.graph.query(prop_query))
            prop_count = int(prop_results[0][0]) if prop_results else 0

            # Tỷ lệ link
            link_ratio = (sameAs_count / total_entities * 100) if total_entities > 0 else 0

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            stats = f"""# 📊 **THỐNG KÊ VIETNAMESE DBPEDIA**
*Cập nhật lúc: {current_time}*

---

## 🔢 **Tổng quan**
- **Tổng số RDF triples**: {total_triples:,}
- **Tổng số entities**: {total_entities:,}  
- **Số loại properties**: {prop_count:,}
- **File dữ liệu**: `{self.rdf_file}`

---

## 📋 **Phân bố theo loại Entity**
{chr(10).join(type_stats)}

---

## 🔗 **Liên kết Quốc tế**
- **owl:sameAs links với DBPedia EN**: {sameAs_count:,}
- **Tỷ lệ entities có link**: {link_ratio:.1f}%

---

## ✅ **Trạng thái hệ thống**
- 🟢 **Database**: Sẵn sàng
- 🟢 **SPARQL Engine**: Hoạt động
- 🟢 **Interface**: Online

---

## 🎯 **Gợi ý sử dụng**
1. Chọn **query mẫu** từ dropdown để bắt đầu
2. Thử **format khác nhau**: Table, JSON, CSV  
3. Xem tab **"Hướng dẫn"** để học SPARQL
4. Query có thể mất vài giây với dataset lớn
"""
            return stats

        except Exception as e:
            return f"""# ❌ **LỖI KHI LẤY THỐNG KÊ**

```
{str(e)}
```

Vui lòng kiểm tra lại file dữ liệu hoặc restart interface."""

    def validate_query(self, query):
        """Validate SPARQL query syntax"""
        if not query.strip():
            return False, "Query rỗng"

        # Basic validation
        query_upper = query.upper()
        if not any(keyword in query_upper for keyword in ['SELECT', 'CONSTRUCT', 'ASK', 'DESCRIBE']):
            return False, "Query phải chứa SELECT, CONSTRUCT, ASK, hoặc DESCRIBE"

        return True, "OK"

    def create_interface(self):
        """Tạo Gradio interface với design đẹp"""

        # Custom CSS
        css = """
        .gradio-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .tab-nav button {
            font-size: 16px;
            font-weight: 500;
        }
        .query-box textarea {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
        }
        """

        with gr.Blocks(
                title="Vietnamese DBPedia SPARQL Interface",
                theme=gr.themes.Soft(),
                css=css
        ) as interface:

            # Header
            gr.Markdown("""
            # 🇻🇳 Vietnamese DBPedia SPARQL Interface
            ### Giao diện truy vấn dữ liệu DBPedia tiếng Việt sử dụng SPARQL

            *Phiên bản tích hợp đầy đủ với ontology tiếng Việt và liên kết quốc tế*
            """)

            with gr.Tab("🔍 SPARQL Query", elem_id="query-tab"):
                with gr.Row():
                    with gr.Column(scale=3):
                        # Example queries dropdown
                        example_dropdown = gr.Dropdown(
                            choices=list(self.example_queries.keys()),
                            label="📝 Chọn query mẫu (hoặc tự viết)",
                            value=list(self.example_queries.keys())[0],
                            interactive=True
                        )

                        # Query input với class tùy chỉnh
                        query_input = gr.Textbox(
                            label="🔧 SPARQL Query Editor",
                            placeholder="Nhập SPARQL query của bạn...",
                            lines=12,
                            value=self.example_queries[list(self.example_queries.keys())[0]],
                            elem_classes=["query-box"]
                        )

                        with gr.Row():
                            # Output format
                            format_radio = gr.Radio(
                                choices=["Table", "JSON", "CSV"],
                                label="📋 Định dạng kết quả",
                                value="Table"
                            )

                            # Execute button
                            execute_btn = gr.Button(
                                "🚀 Thực thi Query",
                                variant="primary",
                                size="lg"
                            )

                    with gr.Column(scale=1):
                        # Status display
                        status_output = gr.Textbox(
                            label="📊 Trạng thái thực thi",
                            lines=4,
                            interactive=False,
                            placeholder="Sẵn sàng thực thi query..."
                        )

                        # Quick stats
                        quick_stats = gr.Textbox(
                            label="📈 Thông tin kết quả",
                            lines=2,
                            interactive=False,
                            placeholder="Chưa có dữ liệu"
                        )

                # Conditional outputs based on format
                with gr.Row():
                    with gr.Column():
                        # Table output (visible by default)
                        table_output = gr.Dataframe(
                            label="📊 Kết quả dạng bảng",
                            wrap=True,
                            # height=400,
                            visible=True
                        )

                        # Text output for JSON/CSV (hidden by default)
                        text_output = gr.Textbox(
                            label="📄 Kết quả dạng text",
                            lines=20,
                            visible=False,
                            interactive=False,
                            show_copy_button=True
                        )

            with gr.Tab("📊 Thống kê & Monitoring"):
                with gr.Row():
                    refresh_stats_btn = gr.Button("🔄 Refresh thống kê", variant="secondary")

                stats_output = gr.Markdown(value=self.get_data_stats())

            with gr.Tab("📖 Hướng dẫn & Examples"):
                gr.Markdown("""
                ## 🎯 Hướng dẫn sử dụng

                ### 1. 🚀 **Cách chạy Query**
                - **Bước 1**: Chọn query mẫu từ dropdown hoặc tự viết
                - **Bước 2**: Chọn định dạng output (Table/JSON/CSV) 
                - **Bước 3**: Click "Thực thi Query"
                - **Bước 4**: Xem kết quả ở phần bên dưới

                ### 2. 🏷️ **Namespaces & Prefixes quan trọng**
                ```sparql
                PREFIX vn-res: <http://vi.dbpedia.org/resource/>      # Vietnamese resources
                PREFIX vn-ont: <http://vi.dbpedia.org/ontology/>      # Vietnamese ontology  
                PREFIX dbp-res: <http://dbpedia.org/resource/>        # English DBPedia resources
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>  # RDF Schema
                PREFIX owl: <http://www.w3.org/2002/07/owl#>          # Web Ontology Language
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>  # RDF
                ```

                ### 3. 🏗️ **Các Class chính trong Vietnamese Ontology**
                | Class | Mô tả | Ví dụ |
                |-------|-------|--------|
                | `vn-ont:Người` | Con người | Hồ Chí Minh, Trần Đại Nghĩa |
                | `vn-ont:ĐịaĐiểm` | Địa điểm | Hà Nội, TP.HCM, Phú Quốc |  
                | `vn-ont:TổChức` | Tổ chức | ĐH Bách Khoa, FPT, Vietcombank |
                | `vn-ont:SựKiện` | Sự kiện | Cách mạng tháng Tám |
                | `vn-ont:TácPhẩm` | Tác phẩm | Truyện Kiều, Số Đỏ |

                ### 4. 🔗 **Properties thường dùng**
                | Property | Mô tả | Kiểu dữ liệu |
                |----------|-------|--------------|
                | `rdfs:label` | Tên/nhãn chính | Text (vi/en) |
                | `vn-ont:ngàySinh` | Ngày sinh | Date |
                | `vn-ont:nơiSinh` | Nơi sinh | Resource |
                | `vn-ont:nghềNghiệp` | Nghề nghiệp | Text |
                | `vn-ont:abstract` | Tóm tắt | Text |
                | `vn-ont:category` | Danh mục | Resource |
                | `owl:sameAs` | Liên kết tương đương | URI |

                ### 5. 💡 **Template Queries hữu ích**

                #### 🔍 **Tìm kiếm cơ bản**
                ```sparql
                SELECT ?entity ?name WHERE {
                    ?entity a vn-ont:Người .
                    ?entity rdfs:label ?name .
                    FILTER (CONTAINS(LCASE(?name), "nguyễn"))
                } LIMIT 10
                ```

                #### 🔗 **Kết hợp với DBPedia tiếng Anh**
                ```sparql
                SELECT ?vn_name ?en_entity WHERE {
                    ?vn_entity rdfs:label ?vn_name .
                    ?vn_entity owl:sameAs ?en_entity .
                    FILTER (lang(?vn_name) = 'vi')
                    FILTER (CONTAINS(LCASE(?vn_name), "hồ chí minh"))
                }
                ```

                #### 📊 **Query thống kê**
                ```sparql
                SELECT ?category (COUNT(?entity) as ?count) WHERE {
                    ?entity vn-ont:category ?category .
                } GROUP BY ?category ORDER BY DESC(?count)
                ```

                ### 6. ⚡ **Tips & Tricks**

                - **LIMIT**: Luôn dùng LIMIT để tránh kết quả quá lớn
                - **FILTER**: Dùng để lọc theo điều kiện
                - **OPTIONAL**: Cho phép thuộc tính không bắt buộc
                - **DISTINCT**: Loại bỏ kết quả trùng lặp
                - **ORDER BY**: Sắp xếp kết quả
                - **CONTAINS()**: Tìm kiếm text chứa chuỗi con
                - **lang()**: Lọc theo ngôn ngữ (vi, en)

                ### 7. 🐛 **Troubleshooting**

                - **Query chậm?** → Thêm LIMIT nhỏ hơn  
                - **Không có kết quả?** → Kiểm tra PREFIX và Class names
                - **Lỗi syntax?** → Kiểm tra dấu chấm, ngoặc nhọn
                - **Encoding lỗi?** → Đảm bảo text Vietnamese được encode đúng
                """)

            # Event handlers
            def on_format_change(format_type):
                """Handle format change"""
                if format_type == "Table":
                    return gr.update(visible=True), gr.update(visible=False)
                else:
                    return gr.update(visible=False), gr.update(visible=True)

            # Connect events
            format_radio.change(
                on_format_change,
                inputs=[format_radio],
                outputs=[table_output, text_output]
            )

            example_dropdown.change(
                self.load_example_query,
                inputs=[example_dropdown],
                outputs=[query_input]
            )

            execute_btn.click(
                self.execute_sparql_query,
                inputs=[query_input, format_radio],
                outputs=[status_output, table_output, text_output, quick_stats]
            )

            refresh_stats_btn.click(
                self.get_data_stats,
                outputs=[stats_output]
            )

        return interface

    def launch(self, share=False, debug=True, server_port=7860, server_name="0.0.0.0"):
        """Khởi chạy Gradio interface với cấu hình tối ưu"""
        interface = self.create_interface()

        print("🎯 Vietnamese DBPedia SPARQL Interface")
        print("=" * 50)
        print(f"🌐 Local URL: http://localhost:{server_port}")

        if share:
            print("🔗 Public URL sẽ được tạo...")

        print("🚀 Đang khởi chạy interface...")

        interface.launch(
            share=share,
            debug=debug,
            server_port=server_port,
            server_name=server_name,
            show_error=True,
            # show_tips=True,
            height=800,
            favicon_path=None
        )


# Main function để chạy standalone
def start_gradio_interface(rdf_file='vietnamese_dbpedia_linked.ttl', share=True):
    """Khởi chạy Gradio interface"""
    try:
        interface = VietnameseDBPediaGradioInterface(rdf_file)
        print("✅ Dữ liệu đã được load thành công")
        interface.launch(share=share)
    except Exception as e:
        print(f"❌ Lỗi khi khởi chạy interface: {e}")
        print("💡 Đảm bảo file RDF exists và có thể đọc được")


if __name__ == "__main__":
    # Chạy interface standalone để test
    start_gradio_interface()