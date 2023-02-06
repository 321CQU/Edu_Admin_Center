import asyncio
import logging

import grpc

from micro_services_protobuf.edu_admin_center import eac_service_pb2_grpc as eac_grpc
from _321CQU.tools.gRPCManager import gRPCManager, ServiceEnum

from service import EACServicer


async def serve():
    port = gRPCManager().get_service_config(ServiceEnum.EduAdminCenter)[1]

    server = grpc.aio.server()
    eac_grpc.add_EduAdminCenterServicer_to_server(EACServicer(), server)
    server.add_insecure_port('[::]:' + port)
    await server.start()
    await server.wait_for_termination()


if __name__ == '__main__':
    print("启动 edu admin center 服务")
    logging.basicConfig(level=logging.INFO)
    asyncio.new_event_loop().run_until_complete(serve())
