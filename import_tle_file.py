#!/usr/bin/env python3
"""
TLE文件导入工具
从TLE格式文件批量导入卫星数据到gRPC服务
"""
import grpc
import sys
import re
import chardet
from grpc_generated import auth_pb2, auth_pb2_grpc
from grpc_generated import constellation_pb2, constellation_pb2_grpc


def detect_encoding(file_path):
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # 读取前10KB
        result = chardet.detect(raw_data)
        encoding = result['encoding'] or 'utf-8'
        if encoding.lower() in ['gb2312', 'gbk']:
            encoding = 'gbk'
        return encoding


def parse_tle_file(file_path, constellation_id):
    """
    解析TLE文件

    TLE文件格式（每3行一个卫星）：
    星座名称 卫星ID
    TLE Line 1
    TLE Line 2
    """
    encoding = detect_encoding(file_path)
    print(f"检测到文件编码: {encoding}")

    satellites = []
    lines = []
    line_num = 0

    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
        for line in f:
            line_num += 1
            line = line.strip()
            if not line:
                continue

            lines.append((line_num, line))

            # 每3行解析一个卫星
            if len(lines) == 3:
                (num1, line1), (num2, line2), (num3, line3) = lines

                try:
                    # 从第一行提取卫星ID
                    match = re.search(r'\s+(\d+)$', line1)
                    if not match:
                        print(f"警告: 行{num1} 未找到卫星ID，跳过")
                        lines = []
                        continue

                    satellite_id = int(match.group(1))

                    # 创建卫星数据
                    satellites.append({
                        'satellite_id': satellite_id,
                        'constellation_id': constellation_id,
                        'info_line1': line2,
                        'info_line2': line3
                    })

                except Exception as e:
                    print(f"警告: 行{num1}-{num3} 解析失败: {str(e)}")

                finally:
                    lines = []

    # 检查是否有未完成的3行
    if lines:
        print(f"警告: 文件末尾有{len(lines)}行未能组成完整的卫星数据")

    return satellites


def import_satellites_stream(channel, token, satellites):
    """使用流式传输导入卫星"""
    client = constellation_pb2_grpc.ConstellationServiceStub(channel)

    def request_generator():
        for sat in satellites:
            yield constellation_pb2.ImportSatellitesRequest(
                token=token,
                constellation_id=sat['constellation_id'],
                satellite_id=sat['satellite_id'],
                info_line1=sat['info_line1'],
                info_line2=sat['info_line2']
            )

    # 调用流式API
    response = client.ImportSatellites(request_generator())
    return response


def main():
    """主函数"""
    if len(sys.argv) < 5:
        print("使用方法:")
        print(f"  {sys.argv[0]} <TLE文件路径> <用户名> <密码> <星座ID>")
        print()
        print("示例:")
        print(f"  {sys.argv[0]} satellites.txt testuser pass123 1")
        sys.exit(1)

    tle_file = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    constellation_id = int(sys.argv[4])

    print("=" * 70)
    print("  TLE文件导入工具")
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

    # 解析TLE文件
    print(f"\n[3/4] 解析TLE文件: {tle_file}")
    try:
        satellites = parse_tle_file(tle_file, constellation_id)
        print(f"成功解析 {len(satellites)} 个卫星")
    except FileNotFoundError:
        print(f"错误: 文件不存在 - {tle_file}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 文件解析失败 - {str(e)}")
        sys.exit(1)

    if not satellites:
        print("错误: 没有解析到任何卫星数据")
        sys.exit(1)

    # 导入卫星
    print(f"\n[4/4] 开始导入卫星...")
    try:
        response = import_satellites_stream(channel, token, satellites)

        print("\n" + "=" * 70)
        print("  导入结果")
        print("=" * 70)
        print(f"状态: {response.status.message}")
        print(f"成功: {response.success_count} 个")
        print(f"失败: {response.fail_count} 个")

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
