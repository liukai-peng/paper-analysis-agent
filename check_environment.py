"""
Windows环境检查脚本
检查Python、数据库和项目配置
"""
import sys
import os
import subprocess
import platform

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_status(name, status, message=""):
    """打印状态"""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {name:<20} {message}")

def check_python():
    """检查Python环境"""
    print_header("Python环境检查")
    
    # Python版本
    version = sys.version_info
    print_status(f"Python版本", version.major >= 3 and version.minor >= 9, 
                f"{version.major}.{version.minor}.{version.micro}")
    
    # pip
    try:
        import pip
        print_status("pip", True, f"版本 {pip.__version__}")
    except:
        print_status("pip", False, "未安装")
    
    # 必要模块
    required_modules = [
        "streamlit", "pandas", "pymupdf", "openai", 
        "pymysql", "pymongo", "redis", "cryptography"
    ]
    
    print("\n📦 检查Python模块：")
    for module in required_modules:
        try:
            __import__(module)
            print_status(module, True, "已安装")
        except ImportError:
            print_status(module, False, "未安装")

def check_databases():
    """检查数据库服务"""
    print_header("数据库服务检查")
    
    # MySQL
    try:
        result = subprocess.run(
            ["sc", "query", "MySQL80"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "RUNNING" in result.stdout:
            print_status("MySQL", True, "服务正在运行")
        elif "STOPPED" in result.stdout:
            print_status("MySQL", False, "服务已停止")
        else:
            print_status("MySQL", False, "服务未安装")
    except:
        print_status("MySQL", False, "检查失败")
    
    # MongoDB
    try:
        result = subprocess.run(
            ["sc", "query", "MongoDB"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "RUNNING" in result.stdout:
            print_status("MongoDB", True, "服务正在运行")
        elif "STOPPED" in result.stdout:
            print_status("MongoDB", False, "服务已停止")
        else:
            print_status("MongoDB", False, "服务未安装")
    except:
        print_status("MongoDB", False, "检查失败")
    
    # Redis
    try:
        result = subprocess.run(
            ["sc", "query", "Redis"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "RUNNING" in result.stdout:
            print_status("Redis", True, "服务正在运行")
        elif "STOPPED" in result.stdout:
            print_status("Redis", False, "服务已停止")
        else:
            print_status("Redis", False, "服务未安装")
    except:
        print_status("Redis", False, "检查失败")

def check_project():
    """检查项目配置"""
    print_header("项目配置检查")
    
    # 检查配置文件
    if os.path.exists(".env"):
        print_status("配置文件", True, ".env 文件存在")
        
        # 检查配置内容
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "your_mysql_password" in content or "your_password" in content:
            print_status("配置内容", False, "请修改默认密码")
        else:
            print_status("配置内容", True, "密码已设置")
    else:
        print_status("配置文件", False, ".env 文件不存在")
        print("   💡 提示：复制 .env.example 为 .env 并修改配置")
    
    # 检查目录结构
    required_dirs = ["app", "app/core", "app/pages", "app/utils", "app/database", "app/config"]
    print("\n📁 检查目录结构：")
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print_status(dir_name, True, "存在")
        else:
            print_status(dir_name, False, "不存在")
    
    # 检查关键文件
    required_files = [
        "app/main.py",
        "app/database/mysql_manager.py",
        "app/database/mongodb_manager.py",
        "app/database/redis_manager.py",
        "requirements.txt",
        "init_database.py"
    ]
    print("\n📄 检查关键文件：")
    for file_name in required_files:
        if os.path.exists(file_name):
            print_status(file_name, True, "存在")
        else:
            print_status(file_name, False, "不存在")

def check_network():
    """检查网络连接"""
    print_header("网络连接检查")
    
    import socket
    
    # 检查端口占用
    ports = [3306, 27017, 6379, 8501]
    print("\n🌐 检查端口占用：")
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        if result == 0:
            if port == 8501:
                print_status(f"端口 {port}", False, "被占用（Streamlit默认端口）")
            else:
                print_status(f"端口 {port}", True, "已开放")
        else:
            if port == 8501:
                print_status(f"端口 {port}", True, "可用")
            else:
                print_status(f"端口 {port}", False, "未开放")
        sock.close()

def print_recommendations():
    """打印建议"""
    print_header("安装建议")
    
    print("""
如果某些检查未通过，请按以下步骤操作：

1️⃣ 安装Python：
   - 访问 https://www.python.org/downloads/
   - 下载 Python 3.11.x (64-bit)
   - 安装时勾选 "Add Python to PATH"

2️⃣ 安装MySQL：
   - 访问 https://dev.mysql.com/downloads/installer/
   - 下载 MySQL Installer for Windows
   - 安装时设置root密码

3️⃣ 安装MongoDB：
   - 访问 https://www.mongodb.com/try/download/community
   - 下载 MongoDB Community Server
   - 安装为Windows服务

4️⃣ 安装Redis：
   - 访问 https://github.com/microsoftarchive/redis/releases
   - 下载 Redis-x64-3.0.504.msi
   - 安装为Windows服务

5️⃣ 安装依赖：
   pip install -r requirements.txt

6️⃣ 配置项目：
   copy .env.example .env
   编辑 .env 文件设置数据库密码

7️⃣ 初始化数据库：
   python init_database.py

8️⃣ 启动系统：
   streamlit run app/main.py

详细说明请查看 README_WINDOWS.md
""")

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  🎓 文献解读Agent系统 - Windows环境检查")
    print("=" * 60)
    print(f"\n操作系统: {platform.system()} {platform.release()}")
    print(f"Python路径: {sys.executable}")
    print(f"当前目录: {os.getcwd()}")
    
    check_python()
    check_databases()
    check_project()
    check_network()
    print_recommendations()
    
    print("\n" + "=" * 60)
    print("  检查完成！")
    print("=" * 60 + "\n")
    
    input("按回车键退出...")

if __name__ == "__main__":
    main()