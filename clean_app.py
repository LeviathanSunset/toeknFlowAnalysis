#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 清理app.py文件的脚本

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"原文件总行数: {len(lines)}")

# 保留前914行和从1093行开始的内容
clean_lines = lines[:914] + lines[1092:]

print(f"清理后行数: {len(clean_lines)}")

with open('app_clean.py', 'w', encoding='utf-8') as f:
    f.writelines(clean_lines)

print('文件清理完成')
