# 智能论文分析系统

一个基于 AI 的学术论文分析工具，帮助研究生新手快速理解和学习学术论文。

## 功能特点

- **PDF 论文分析**: 上传 PDF 文件，自动提取和分析论文结构
- **分步学习模式**: 7 个步骤引导新手逐步学习论文
- **文献库管理**: 保存和管理已分析的文献
- **多格式导出**: 支持 JSON、Markdown、TXT 格式导出

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

复制 `.env.example` 为 `.env`，并填入你的 DeepSeek API 密钥：

```
DEEPSEEK_API_KEY=your_api_key_here
```

或者在应用界面中直接输入 API 密钥。

### 3. 运行应用

```bash
python run.py
```

应用将在 http://localhost:8502 启动。

## 使用说明

1. **上传 PDF**: 在左侧边栏上传 PDF 文件
2. **查看结构**: 系统自动分析论文结构
3. **选择分析模式**: 选择快速分析或深度分析
4. **分步学习**: 按照 7 个步骤逐步学习论文内容
5. **保存到文献库**: 分析结果可保存供以后查看

## 项目结构

```
backend/
├── app/
│   ├── core/           # 核心工作流和 Agent
│   ├── database/       # 数据库管理
│   ├── ui_modules/     # Streamlit UI 组件
│   └── utils/          # 工具函数
├── project/work_dir/   # 分析结果存储
├── run.py              # 启动脚本
└── requirements.txt    # 依赖列表
```

## 技术栈

- **前端**: Streamlit
- **AI**: DeepSeek API
- **数据库**: SQLite / MongoDB / MySQL (可选)
