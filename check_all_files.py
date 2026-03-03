import os
import json

def check_all_files():
    work_dirs = [d for d in os.listdir('project/work_dir') if d.startswith('lit_')]
    print(f"发现 {len(work_dirs)} 个文献目录")
    
    for d in work_dirs:
        analysis_path = os.path.join('project/work_dir', d, 'analysis_result.json')
        if os.path.exists(analysis_path):
            with open(analysis_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            first_pass = data.get('first_pass', {})
            tools = first_pass.get('tools', {})
            has_tf = 'theoretical_framework' in tools
            has_rm = 'research_method' in tools
            has_ds = 'data_source' in tools
            
            print(f"\n{d}:")
            print(f"  tools: {'✓' if tools else '✗'}")
            print(f"  theoretical_framework: {'✓' if has_tf else '✗'}")
            print(f"  research_method: {'✓' if has_rm else '✗'}")
            print(f"  data_source: {'✓' if has_ds else '✗'}")
        else:
            print(f"\n{d}: 没有 analysis_result.json")

if __name__ == "__main__":
    check_all_files()
