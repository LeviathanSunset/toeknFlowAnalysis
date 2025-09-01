#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit应用启动脚本
"""

import subprocess
import sys
import os

def main():
    """启动Streamlit应用"""
    app_file = "app.py"
    
    if not os.path.exists(app_file):
        print(f"❌ 找不到应用文件: {app_file}")
        return
    
    print("🚀 启动Solscan代币流动分析应用...")
    print("📱 应用将在浏览器中自动打开")
    print("⏹️  按 Ctrl+C 停止应用")
    print("=" * 50)
    
    try:
        # 使用当前Python环境运行Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", app_file, "--server.port=8501"]
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n⏹️  应用已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
    except FileNotFoundError:
        print("❌ 未找到Streamlit，请先安装: pip install streamlit")

if __name__ == "__main__":
    main()
