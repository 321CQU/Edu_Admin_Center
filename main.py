import asyncio
from configparser import Error as ConfigError
import logging
import os

import grpc

from _321CQU.tools.gRPCMetrics import GRPCMetricsServerInterceptor, start_metrics_server
from micro_services_protobuf.edu_admin_center import eac_service_pb2_grpc as eac_grpc
from _321CQU.tools.gRPCManager import gRPCManager, ServiceEnum

from service import EACServicer
from utils.tools.configManager import ConfigReader


def _get_metrics_port():
    port = os.getenv("METRICS_PORT")
    if port:
        return port
    try:
        return ConfigReader().get_config("Metrics", "port")
    except ConfigError:
        return None


async def serve():
    grpc_manager = gRPCManager(caller="edu_admin_center")
    port = grpc_manager.get_service_config(ServiceEnum.EduAdminCenter)[1]

    metrics_server = await start_metrics_server(_get_metrics_port())
    server = grpc.aio.server(interceptors=[GRPCMetricsServerInterceptor()])
    eac_grpc.add_EduAdminCenterServicer_to_server(EACServicer(), server)
    server.add_insecure_port('[::]:' + port)
    await server.start()
    try:
        await server.wait_for_termination()
    finally:
        await grpc_manager.close_all()
        if metrics_server is not None:
            metrics_server.close()
            await metrics_server.wait_closed()


if __name__ == '__main__':
    print("启动 edu admin center 服务")
    logging.basicConfig(level=logging.INFO)
    asyncio.new_event_loop().run_until_complete(serve())
