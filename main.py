import subprocess
import os
import sys

def run_script(script_path):
    print(f"=== Running {script_path} ===")
    result = subprocess.run([sys.executable, script_path], capture_output=False)
    if result.returncode != 0:
        print(f"Error running {script_path}")
        sys.exit(1)

def main():
    # 0. Install requirements (optional if already installed)
    # subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # 1. Download Data
    run_script("crawler/download_dump.py")
    
    # 2. Extract Infoboxes
    run_script("crawler/extract_infobox.py")
    
    # 3. Transform to RDF
    run_script("transformer/rdf_generator.py")
    
    # 4. Linking
    run_script("linking/linker.py")
    
    print("\n" + "="*30)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("RDF Data is ready at: data/rdf/data.ttl")
    print("="*30)
    print("\nNext step: Run SPARQL endpoint using Docker")
    print("cd sparql && docker-compose up -d")

if __name__ == "__main__":
    main()
