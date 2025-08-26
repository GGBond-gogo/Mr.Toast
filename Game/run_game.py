#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股市卧底游戏启动脚本
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        sys.exit(1)
    print(f"✓ Python版本: {sys.version}")

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'flask',
        'flask-socketio',
        'python-socketio',
        'eventlet'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} 已安装")