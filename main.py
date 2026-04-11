"""
程序入口
"""
import sys
import logging
from pathlib import Path
import os

# 配置日志
# 日志目录为当前目录（exe所在目录）
if getattr(sys, 'frozen', False):
    log_dir = Path(sys.executable).parent
else:
    log_dir = Path(__file__).parent

log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            log_dir / "app.log",
            encoding="utf-8", mode="a"
        )
    ]
)

logger = logging.getLogger(__name__)

# 获取应用根目录（打包后或开发环境）
# PyInstaller onedir 模式：datas 声明的文件都在 _internal/ 子目录中
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent / "_internal"
else:
    BASE_DIR = Path(__file__).parent


def main():
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtGui import QFont, QIcon
    from src.data.database import init_db, _get_active_db_path, FALLBACK_DB_PATH
    from src.gui.main_window import MainWindow

    # 检查是否有可用的数据库文件
    active_db = _get_active_db_path()
    if active_db is None:
        logger.error("没有可用的数据库文件")
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "错误", f"数据库文件不存在\n\n安装目录：{FALLBACK_DB_PATH}\n\n请重新安装程序。")
        sys.exit(1)

    logger.info("使用数据库：%s", active_db)

    # 初始化数据库
    try:
        init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.exception("数据库初始化失败")
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "错误", f"数据库初始化失败：\n{e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("河北省高考志愿填报系统")
    app.setOrganizationName("gaokao2026")

    # 设置应用图标（任务栏/标题栏）
    from PyQt6.QtGui import QPixmap
    resources_dir = BASE_DIR / "resources"
    app_icon = QIcon()
    for sz in [16, 24, 32, 48, 64, 128, 256]:
        icon_png = resources_dir / f"icon_{sz}.png"
        if icon_png.exists():
            app_icon.addPixmap(QPixmap(str(icon_png)))
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # 全局字体
    font = QFont("微软雅黑", 10)
    app.setFont(font)

    # 全局异常捕获
    def handle_exception(exc_type, exc_value, exc_traceback):
        logger.exception("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(None, "错误", f"程序发生错误：\n{exc_value}")

    sys.excepthook = handle_exception

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
