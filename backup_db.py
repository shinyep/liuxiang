"""
liuxiang 数据库备份脚本
每天 21:30 由自动化任务触发
- 检查源文件 MD5 是否变化（对比最新备份）
- 无变化则跳过
- 有变化则复制并生成 db_YYYY-MM-DD_HH-MM-SS.sqlite3
- 仅保留最新的 7 个备份文件
"""

import hashlib
import shutil
import glob
import os
import sys
from pathlib import Path
from datetime import datetime

SOURCE = Path(r"E:\liuxiang\dist\成品追溯与客户管理系统\data\db.sqlite3")
BACKUP_DIR = Path(r"E:\liuxiang\数据库备份")
LOG_FILE = BACKUP_DIR / "backup.log"
KEEP_COUNT = 7


def md5(filepath: Path) -> str:
    return hashlib.md5(filepath.read_bytes()).hexdigest()


def get_backup_files() -> list[Path]:
    """获取备份目录中所有 .sqlite3 文件，按修改时间降序（最新在前）"""
    files = sorted(BACKUP_DIR.glob("*.sqlite3"), key=lambda f: f.stat().st_mtime, reverse=True)
    return files


def log(msg: str):
    """同时输出到 stdout 和日志文件"""
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n")

    step = 1
    log(f"[{step}] 目标文件: {SOURCE}")
    if not SOURCE.exists():
        log(f"[{step}] ❌ 源文件不存在: {SOURCE}")
        return
    src_size = SOURCE.stat().st_size
    src_mtime = datetime.fromtimestamp(SOURCE.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    log(f"    大小: {src_size:,} bytes | 修改时间: {src_mtime}")

    step += 1
    src_hash = md5(SOURCE)
    log(f"[{step}] 源文件 MD5: {src_hash}")

    step += 1
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_files = get_backup_files()
    log(f"[{step}] 备份目录: {BACKUP_DIR} | 现有 .sqlite3 文件: {len(backup_files)}")

    step += 1
    if backup_files:
        latest = backup_files[0]
        latest_hash = md5(latest)
        log(f"[{step}] 最新备份: {latest.name}")
        log(f"     MD5: {latest_hash}")
        if src_hash == latest_hash:
            log(f"     → 文件无变化，跳过备份 ✓")
            cleanup(backup_files)
            return
        log(f"     → 文件已变化，执行备份")
    else:
        log(f"[{step}] 无现有备份，执行首次备份")

    step += 1
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest = BACKUP_DIR / f"db_{timestamp}.sqlite3"
    shutil.copy2(SOURCE, dest)
    log(f"[{step}] 备份完成: {dest.name} ({dest.stat().st_size:,} bytes)")

    backup_files = get_backup_files()
    cleanup(backup_files)


def cleanup(backup_files: list[Path]):
    """只保留最新的 KEEP_COUNT 个备份"""
    if len(backup_files) <= KEEP_COUNT:
        log(f"   保留策略: {len(backup_files)}/{KEEP_COUNT} 个，无需清理 ✓")
        return
    to_delete = backup_files[KEEP_COUNT:]
    log(f"   保留策略: 需删除 {len(to_delete)} 个旧文件 (保留 {KEEP_COUNT} 个)")
    for f in to_delete:
        f.unlink()
        log(f"     已删除: {f.name}")


if __name__ == "__main__":
    main()
