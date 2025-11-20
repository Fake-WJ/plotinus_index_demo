#!/usr/bin/env python3
"""
生成gRPC Python代码的脚本
"""
import subprocess
import os
import sys
import re

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTO_DIR = os.path.join(ROOT_DIR, 'protos')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'grpc_generated')

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Proto文件列表
PROTO_FILES = [
    'common.proto',
    'auth.proto',
    'constellation.proto',
    'satellite.proto',
    'base.proto'
]

def generate_grpc_code():
    """生成gRPC Python代码"""
    print("Starting gRPC Python code generation...")

    for proto_file in PROTO_FILES:
        proto_path = os.path.join(PROTO_DIR, proto_file)

        if not os.path.exists(proto_path):
            print(f"Warning: Proto file does not exist: {proto_path}")
            continue

        print(f"Compiling: {proto_file}")

        # 调用protoc编译器
        cmd = [
            'python', '-m', 'grpc_tools.protoc',
            f'--proto_path={PROTO_DIR}',
            f'--python_out={OUTPUT_DIR}',
            f'--grpc_python_out={OUTPUT_DIR}',
            proto_path
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"[OK] Successfully compiled: {proto_file}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to compile: {proto_file}")
            print(f"Error message: {e.stderr}")
            sys.exit(1)

    # 创建__init__.py
    init_file = os.path.join(OUTPUT_DIR, '__init__.py')
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write('"""Auto-generated gRPC code"""\n')

    # 修复导入问题
    print("\nFixing imports in generated files...")
    fix_imports()

    print("\n[OK] All Proto files compiled successfully!")
    print(f"Generated files location: {OUTPUT_DIR}")


def fix_imports():
    """修复生成文件中的导入问题"""
    # 获取所有生成的Python文件
    all_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.py') and f != '__init__.py']

    for filename in all_files:
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 修复导入: import xxx_pb2 as -> from . import xxx_pb2 as
        content = re.sub(r'^import (\w+_pb2) as', r'from . import \1 as', content, flags=re.MULTILINE)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  Fixed imports in {filename}")


if __name__ == '__main__':
    generate_grpc_code()
