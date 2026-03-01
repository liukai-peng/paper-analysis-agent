# 🎓 文献解读Agent系统 - Windows安装指南

专门针对Windows系统的完整安装和配置指南。

## 📋 目录

- [系统要求](#系统要求)
- [安装步骤](#安装步骤)
- [数据库安装](#数据库安装)
- [配置说明](#配置说明)
- [启动系统](#启动系统)
- [常见问题](#常见问题)

## 💻 系统要求

- Windows 10/11 (64位)
- Python 3.9+ (推荐3.11)
- 内存：8GB+ (推荐16GB)
- 磁盘空间：10GB+
- 网络连接

## 🚀 安装步骤

### 第一步：安装Python

1. 访问 [Python官网](https://www.python.org/downloads/)
2. 下载 Python 3.11.x (64-bit)
3. 运行安装程序，**勾选"Add Python to PATH"**
4. 点击"Install Now"
5. 验证安装：
   ```cmd
   python --version
   pip --version
   ```

### 第二步：安装Git (可选但推荐)

1. 访问 [Git官网](https://git-scm.com/download/win)
2. 下载并安装 Git for Windows
3. 使用默认设置即可

### 第三步：下载项目代码

**方式1：使用Git克隆**
```cmd
cd "D:\Program Files\Desktop\文献2010-2013\NLP"
git clone <你的项目仓库地址> 文献解读
```

**方式2：直接下载ZIP**
1. 下载项目ZIP文件
2. 解压到 `D:\Program Files\Desktop\文献2010-2013\NLP\文献解读`

### 第四步：安装依赖

```cmd
cd "D:\Program Files\Desktop\文献2010-2013\NLP\文献解读\backend"
pip install -r requirements.txt
```

> 如果安装缓慢，可以使用清华镜像：
> ```cmd
> pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

## 🗄️ 数据库安装

### 1. 安装MySQL

#### 方式1：使用MySQL Installer (推荐)

1. 访问 [MySQL下载页面](https://dev.mysql.com/downloads/installer/)
2. 下载 **MySQL Installer for Windows** (选择较大的那个，包含所有组件)
3. 运行安装程序
4. 选择 **"Server only"** 或 **"Full"**
5. 设置root密码（记住这个密码！）
6. 完成安装

#### 方式2：使用XAMPP (更简单)

1. 访问 [XAMPP官网](https://www.apachefriends.org/)
2. 下载 XAMPP for Windows
3. 安装时**只勾选MySQL**（不需要Apache、PHP等）
4. 安装完成后，打开XAMPP Control Panel
5. 点击MySQL的"Start"按钮启动服务

#### 验证MySQL安装

```cmd
mysql --version
```

如果提示找不到命令，需要添加环境变量：
1. 找到MySQL安装目录（如 `C:\Program Files\MySQL\MySQL Server 8.0\bin`）
2. 添加到系统PATH环境变量

#### 创建数据库

```cmd
mysql -u root -p
```

输入密码后，执行：
```sql
CREATE DATABASE literature_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 2. 安装MongoDB

#### 方式1：使用MongoDB Installer

1. 访问 [MongoDB下载页面](https://www.mongodb.com/try/download/community)
2. 选择 **MongoDB Community Server**
3. 下载 Windows x64 版本
4. 运行安装程序
5. 选择 **"Complete"** 安装
6. 勾选 **"Install MongoDB as a Service"**
7. 完成安装

#### 方式2：使用ZIP包

1. 下载MongoDB ZIP包
2. 解压到 `C:\mongodb`
3. 创建数据目录 `C:\mongodb\data\db`
4. 创建配置文件 `C:\mongodb\mongod.cfg`：
   ```yaml
   systemLog:
     destination: file
     path: C:\mongodb\log\mongod.log
   storage:
     dbPath: C:\mongodb\data\db
   ```
5. 安装为Windows服务：
   ```cmd
   cd C:\mongodb\bin
   mongod.exe --config "C:\mongodb\mongod.cfg" --install
   net start MongoDB
   ```

#### 验证MongoDB安装

```cmd
mongod --version
```

### 3. 安装Redis

#### 方式1：使用MSI安装包 (推荐)

1. 访问 [Redis Windows版本](https://github.com/microsoftarchive/redis/releases)
2. 下载最新版本的MSI文件（如 `Redis-x64-3.0.504.msi`）
3. 运行安装程序
4. 使用默认设置即可
5. 安装完成后，Redis会自动作为Windows服务启动

#### 方式2：使用ZIP包

1. 下载Redis ZIP包
2. 解压到 `C:\redis`
3. 打开命令提示符：
   ```cmd
   cd C:\redis
   redis-server.exe redis.windows.conf
   ```

#### 验证Redis安装

```cmd
redis-cli ping
```

如果返回 `PONG`，说明安装成功。

## ⚙️ 配置说明

### 1. 创建配置文件

在项目目录下创建 `.env` 文件：

```cmd
cd "D:\Program Files\Desktop\文献2010-2013\NLP\文献解读\backend"
copy .env.example .env
```

### 2. 编辑配置文件

使用记事本或VS Code编辑 `.env` 文件：

```env
# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的MySQL密码
MYSQL_DATABASE=literature_agent

# MongoDB配置
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=literature_agent

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 会话配置
SESSION_EXPIRES_HOURS=24

# Deepseek API配置
DEEPSEEK_API_KEY=你的Deepseek_API密钥
```

> **注意**：将 `你的MySQL密码` 替换为你安装MySQL时设置的密码

### 3. 验证数据库服务

确保所有数据库服务都在运行：

```cmd
# 检查MySQL
sc query MySQL80

# 检查MongoDB
sc query MongoDB

# 检查Redis
sc query Redis
```

如果服务未运行，启动它们：

```cmd
net start MySQL80
net start MongoDB
net start Redis
```

## 🎮 启动系统

### 1. 初始化数据库

```cmd
cd "D:\Program Files\Desktop\文献2010-2013\NLP\文献解读\backend"
python init_database.py
```

如果看到以下输出，说明初始化成功：
```
✅ MySQL数据库初始化成功
✅ MongoDB数据库初始化成功
✅ Redis连接初始化成功
```

### 2. 启动应用

```cmd
streamlit run app/main.py
```

系统会自动打开浏览器，访问 `http://localhost:8501`

### 3. 创建启动脚本

为了方便启动，可以创建批处理文件 `start.bat`：

```batch
@echo off
cd /d "D:\Program Files\Desktop\文献2010-2013\NLP\文献解读\backend"
echo 正在启动文献解读Agent系统...
streamlit run app/main.py
pause
```

双击 `start.bat` 即可启动系统。

## ❓ 常见问题

### Q1: pip安装依赖失败

**A:** 尝试使用国内镜像源：
```cmd
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: MySQL连接失败

**A:** 
1. 确认MySQL服务已启动：
   ```cmd
   net start MySQL80
   ```
2. 检查密码是否正确
3. 确认端口3306未被占用：
   ```cmd
   netstat -ano | findstr 3306
   ```

### Q3: MongoDB连接失败

**A:**
1. 确认MongoDB服务已启动：
   ```cmd
   net start MongoDB
   ```
2. 检查数据目录权限
3. 查看日志文件：`C:\mongodb\log\mongod.log`

### Q4: Redis连接失败

**A:**
1. 确认Redis服务已启动：
   ```cmd
   net start Redis
   ```
2. 或者手动启动：
   ```cmd
   redis-server.exe
   ```

### Q5: 端口被占用

**A:** 查找并关闭占用端口的程序：
```cmd
# 查看8501端口占用
netstat -ano | findstr 8501

# 结束进程（将PID替换为实际的进程ID）
taskkill /PID 进程ID /F
```

### Q6: Python版本问题

**A:** 如果系统中有多个Python版本，使用完整路径：
```cmd
C:\Users\你的用户名\AppData\Local\Programs\Python\Python311\python.exe -m streamlit run app/main.py
```

### Q7: 防火墙阻止连接

**A:** 添加Windows防火墙例外：
1. 打开"Windows安全中心"
2. 点击"防火墙和网络保护"
3. 点击"允许应用通过防火墙"
4. 添加Python和Streamlit

### Q8: 中文显示乱码

**A:** 设置Windows区域设置：
1. 打开"设置" → "时间和语言" → "语言"
2. 点击"管理语言设置"
3. 在"非Unicode程序的语言"中选择"中文(简体，中国)"
4. 重启电脑

## 🔧 系统维护

### 备份数据

```cmd
# 备份MySQL
mysqldump -u root -p literature_agent > backup_mysql.sql

# 备份MongoDB
mongodump --db literature_agent --out backup_mongodb

# 备份Redis (需要安装redis-cli)
redis-cli SAVE
copy C:\redis\dump.rdb backup_redis.rdb
```

### 恢复数据

```cmd
# 恢复MySQL
mysql -u root -p literature_agent < backup_mysql.sql

# 恢复MongoDB
mongorestore --db literature_agent backup_mongodb/literature_agent
```

### 更新系统

```cmd
cd "D:\Program Files\Desktop\文献2010-2013\NLP\文献解读\backend"
git pull
pip install -r requirements.txt --upgrade
```

## 📞 技术支持

如果遇到问题：

1. 查看日志文件：`backend/logs/`
2. 检查数据库服务状态
3. 确认配置文件正确
4. 查看Windows事件查看器

## 🎉 恭喜！

现在你已经成功在Windows系统上安装并配置了文献解读Agent系统！

开始使用：
1. 打开浏览器访问 `http://localhost:8501`
2. 注册新账户
3. 配置Deepseek API密钥
4. 上传PDF文献开始分析

---

💡 **提示**：建议将 `start.bat` 文件发送到桌面快捷方式，方便快速启动系统！