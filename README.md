# 河北省高考志愿填报系统 2026

## 项目简介

专为河北省2026年高考考生开发的智能志愿填报辅助系统。

- **技术栈**：Python 3.10+ · PyQt6 · SQLite · pandas · reportlab
- **核心功能**：导入投档数据 → 录入考生信息 → 自动生成96个冲稳保志愿 → 导出Excel/PDF
- **目标上线**：2026年6月30日前

---

## 目录结构

```
gaokao_volunteer/
├── main.py              # 程序入口
├── requirements.txt     # 依赖包列表
├── gaokao.spec          # PyInstaller打包配置
├── 启动系统.bat          # Windows快速启动脚本
├── src/
│   ├── core/
│   │   ├── engine.py    # 智能推荐引擎（核心算法）
│   │   └── exporter.py  # 导出模块（Excel/PDF）
│   ├── data/
│   │   ├── database.py  # 数据库初始化与操作
│   │   └── importer.py  # Excel数据导入解析
│   └── gui/
│       ├── main_window.py  # 主窗口
│       ├── input_panel.py  # 考生信息录入面板
│       ├── data_panel.py   # 数据管理面板
│       └── result_panel.py # 志愿结果面板
├── tools/
│   ├── gen_demo_data.py    # 演示数据生成
│   ├── test_engine.py      # 推荐引擎测试
│   └── test_export.py      # 导出功能测试
├── data/
│   └── db/gaokao.db        # SQLite数据库（自动创建）
└── output/                 # 导出文件目录
```

---

## 快速开始

### 方式一：使用启动脚本（推荐）
```
双击 启动系统.bat
```

### 方式二：命令行
```bash
# 激活虚拟环境
venv\Scripts\activate

# 运行
python main.py
```

### 方式三：生成演示数据后测试
```bash
python tools\gen_demo_data.py
python main.py
```

---

## 使用流程

1. **导入数据**  
   点击「数据管理」标签页 → 选择河北省投档Excel文件 → 设置年份/科目/批次 → 导入

2. **填写考生信息**  
   点击「考生信息与推荐」→ 填写分数、选科、身体条件、偏好 → 点击「开始生成96个志愿」

3. **查看结果**  
   系统自动跳转到「志愿结果」页 → 可筛选/搜索 → 导出Excel或PDF

---

## 打包为安装程序

```bash
# 安装PyInstaller
pip install pyinstaller

# 打包
pyinstaller gaokao.spec

# 输出在 dist\ 目录
```

---

## 数据说明

- 系统内置2022~2025年模拟演示数据（用于测试）
- 真实数据请导入河北省教育考试院官方Excel文件
- 支持每年更新导入，重复导入自动覆盖

---

## 免责声明

本系统仅供参考，不构成任何录取承诺。  
最终填报以河北省教育考试院官方信息为准，责任由考生自行承担。

---

**项目负责人：张哥 | 2026年高考版 | 开发部**
