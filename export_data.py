#!/usr/bin/env python3
"""
数据导出工具
从gRPC服务导出星座的TLE和ISL数据为ZIP文件
"""
import grpc
import sys
from grpc_generated import auth_pb2, auth_pb2_grpc
from grpc_generated import constellation_pb2, constellation_pb2_grpc


def export_constellations(channel, token, constellation_ids, output_file):
    """导出星座数据"""
    client = constellation_pb2_grpc.ConstellationServiceStub(channel)

    # 调用导出API
    response = client.ExportConstellations(
        constellation_pb2.ExportConstellationsRequest(
            token=token,
            constellation_ids=constellation_ids
        )
    )

    if response.status.code != 200:
        raise Exception(response.status.message)

    # 保存ZIP文件
    with open(output_file, 'wb') as f:
        f.write(response.zip_data)

    return len(response.zip_data)


def list_constellations(channel, token):
    """列出所有星座"""
    client = constellation_pb2_grpc.ConstellationServiceStub(channel)

    response = client.ListConstellations(
        constellation_pb2.ListConstellationsRequest(token=token)
    )

    return response.constellations


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("使用方法:")
        print(f"  {sys.argv[0]} <用户名> <密码> [星座ID1 星座ID2 ...]")
        print()
        print("示例:")
        print(f"  {sys.argv[0]} testuser pass123           # 列出所有星座")
        print(f"  {sys.argv[0]} testuser pass123 1 2 3     # 导出指定星座")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    constellation_ids = [int(x) for x in sys.argv[3:]] if len(sys.argv) > 3 else []

    print("=" * 70)
    print("  数据导出工具")
    print("=" * 70)

    # 连接gRPC服务器
    print("\n[1/3] 连接服务器...")
    channel = grpc.insecure_channel('localhost:50051')
    auth_client = auth_pb2_grpc.AuthServiceStub(channel)

    # 登录获取token
    print("[2/3] 用户登录...")
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

    # 如果没有指定星座ID，列出所有星座
    if not constellation_ids:
        print("\n[3/3] 列出所有星座...")
        try:
            constellations = list_constellations(channel, token)

            if not constellations:
                print("没有找到任何星座")
                sys.exit(0)

            print("\n可用的星座:")
            print("-" * 70)
            for const in constellations:
                print(f"  ID: {const.id:3d}  名称: {const.constellation_name:20s}  卫星数: {const.satellite_count}")
            print("-" * 70)
            print(f"\n要导出星座数据，请指定星座ID:")
            print(f"  {sys.argv[0]} {username} {password} [星座ID...]")

        except Exception as e:
            print(f"错误: 获取星座列表失败 - {str(e)}")
            sys.exit(1)

        sys.exit(0)

    # 导出数据
    print(f"\n[3/3] 导出星座数据...")
    output_file = "constellation_data.zip"

    try:
        file_size = export_constellations(channel, token, constellation_ids, output_file)

        print("\n" + "=" * 70)
        print("  导出成功")
        print("=" * 70)
        print(f"导出星座数: {len(constellation_ids)}")
        print(f"文件大小: {file_size} 字节")
        print(f"保存位置: {output_file}")
        print("\nZIP文件包含:")
        print("  - tles.txt  (卫星TLE数据)")
        print("  - isls.txt  (卫星链接数据)")
        print("=" * 70)

    except grpc.RpcError as e:
        print(f"错误: gRPC调用失败 - {e.code()}: {e.details()}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 导出失败 - {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
