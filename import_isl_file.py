#!/usr/bin/env python3
"""
ISL文件导入工具
从ISL格式文件批量导入卫星链接数据到gRPC服务
"""
import grpc
import sys
import chardet
from grpc_generated import auth_pb2, auth_pb2_grpc
from grpc_generated import satellite_pb2, satellite_pb2_grpc


def detect_encoding(file_path):
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # 读取前10KB
        result = chardet.detect(raw_data)
        encoding = result['encoding'] or 'utf-8'
        if encoding.lower() in ['gb2312', 'gbk']:
            encoding = 'gbk'
        return encoding


def parse_isl_file(file_path, constellation_id):
    """
    解析ISL文件

    ISL文件格式（每行一条链接）：
    卫星ID1 卫星ID2
    """
    encoding = detect_encoding(file_path)
    print(f"检测到文件编码: {encoding}")

    links = []
    line_num = 0

    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
        for line in f:
            line_num += 1
            line = line.strip()
            if not line:
                continue

            # 解析一行数据
            parts = line.split()
            if len(parts) != 2:
                print(f"警告: 行{line_num} 格式错误（需要两个卫星ID），跳过")
                continue

            try:
                sat1_id = int(parts[0])
                sat2_id = int(parts[1])

                # 创建链接数据
                links.append({
                    'constellation_id': constellation_id,
                    'satellite_id1': sat1_id,
                    'satellite_id2': sat2_id
                })

            except ValueError:
                print(f"警告: 行{line_num} 卫星ID必须为数字，跳过")
                continue

    return links


def import_links_stream(channel, token, links):
    """使用流式传输导入链接"""
    client = satellite_pb2_grpc.SatelliteServiceStub(channel)

    def request_generator():
        for link in links:
            yield satellite_pb2.ImportLinksRequest(
                token=token,
                constellation_id=link['constellation_id'],
                satellite_id1=link['satellite_id1'],
                satellite_id2=link['satellite_id2']
            )

    # 调用流式API
    response = client.ImportLinks(request_generator())
    return response


def main():
    """主函数"""
    if len(sys.argv) < 5:
        print("使用方法:")
        print(f"  {sys.argv[0]} <ISL文件路径> <用户名> <密码> <星座ID>")
        print()
        print("示例:")
        print(f"  {sys.argv[0]} links.txt testuser pass123 1")
        sys.exit(1)

    isl_file = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    constellation_id = int(sys.argv[4])

    print("=" * 70)
    print("  ISL文件导入工具")
    print("=" * 70)

    # 连接gRPC服务器
    print("\n[1/4] 连接服务器...")
    channel = grpc.insecure_channel('localhost:50051')
    auth_client = auth_pb2_grpc.AuthServiceStub(channel)

    # 登录获取token
    print("[2/4] 用户登录...")
    try:
        login_resp = auth_client.Login(
            auth_pb2.LoginRequest(username=username, password=password)
        )
        if login_resp.status.code != 200:
            print(f"错误: 登录失败 - {login_resp.status.message}")
            sys.exit(1)

        token = login_resp.token
        print(f"登录成功，用户: {login_resp.user.username}")
    except Exception as e:
        print(f"错误: 登录失败 - {str(e)}")
        sys.exit(1)

    # 解析ISL文件
    print(f"\n[3/4] 解析ISL文件: {isl_file}")
    try:
        links = parse_isl_file(isl_file, constellation_id)
        print(f"成功解析 {len(links)} 条链接")
    except FileNotFoundError:
        print(f"错误: 文件不存在 - {isl_file}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 文件解析失败 - {str(e)}")
        sys.exit(1)

    if not links:
        print("错误: 没有解析到任何链接数据")
        sys.exit(1)

    # 导入链接
    print(f"\n[4/4] 开始导入链接...")
    try:
        response = import_links_stream(channel, token, links)

        print("\n" + "=" * 70)
        print("  导入结果")
        print("=" * 70)
        print(f"状态: {response.status.message}")
        print(f"成功: {response.success_count} 条")
        print(f"失败: {response.fail_count} 条")

        if response.errors:
            print(f"\n错误信息（前{len(response.errors)}条）:")
            for error in response.errors:
                print(f"  - {error}")

        print("=" * 70)

        if response.fail_count > 0:
            sys.exit(1)

    except grpc.RpcError as e:
        print(f"错误: gRPC调用失败 - {e.code()}: {e.details()}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 导入失败 - {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
