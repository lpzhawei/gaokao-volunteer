"""重新生成用户手册PDF"""
import sys
sys.path.insert(0, '.')
from create_manual_pdf import main as gen_manual

output_path = gen_manual()
print(f"用户手册已生成: {output_path}")
