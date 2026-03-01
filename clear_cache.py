import shutil
import os

# 清理所有__pycache__目录
for root, dirs, files in os.walk('app'):
    for d in dirs:
        if d == '__pycache__':
            path = os.path.join(root, d)
            print(f"删除: {path}")
            shutil.rmtree(path, ignore_errors=True)

print("清理完成！")
