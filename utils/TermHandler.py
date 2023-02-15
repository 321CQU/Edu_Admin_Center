import asyncio
import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from micro_services_protobuf.mycqu_service import mycqu_request_response_pb2 as mycqu_rr
from micro_services_protobuf.mycqu_service import mycqu_service_pb2_grpc as mycqu_grpc
from micro_services_protobuf.mycqu_service import mycqu_model_pb2 as mycqu_model

from _321CQU.tools import gRPCManager
from _321CQU.service import ServiceEnum


class TermHandler:
    term_list: List[mycqu_model.CquSessionInfo] = []
    curr_term: Optional[mycqu_model.CquSessionInfo] = None
    last_update_date = datetime.datetime.fromtimestamp(0)
    has_fetched = asyncio.Event()

    @staticmethod
    async def _set_term_list(login_info: mycqu_rr.BaseLoginInfo):
        async with gRPCManager().get_stub(ServiceEnum.MycquService) as stub:
            stub: mycqu_grpc.MycquFetcherStub = stub
            res: mycqu_rr.FetchAllSessionInfoResponse = await stub.FetchAllSessionInfo(login_info)
            TermHandler.term_list = res.session_infos

    @staticmethod
    async def _set_curr_term(login_info: mycqu_rr.BaseLoginInfo):
        async with gRPCManager().get_stub(ServiceEnum.MycquService) as stub:
            stub: mycqu_grpc.MycquFetcherStub = stub
            res: mycqu_model.CquSessionInfo = await stub.FetchCurrSessionInfo(login_info)
            TermHandler.curr_term = res

    @staticmethod
    def _get_target_term(term_offset: int) -> mycqu_model.CquSession:
        temp = term_offset + TermHandler.curr_term.session.is_autumn
        target_term = temp % 2
        target_year = TermHandler.curr_term.session.year + \
                      int(Decimal(str(temp / 2)).quantize(Decimal('0'), rounding=ROUND_HALF_UP))

        return mycqu_model.CquSession(year=target_year, is_autumn=bool(target_term))

    @staticmethod
    async def get_term_info(login_info: mycqu_rr.BaseLoginInfo, term_offset: int) -> Optional[mycqu_model.CquSessionInfo]:
        if (datetime.datetime.now() - TermHandler.last_update_date).days > 30:
            TermHandler.has_fetched.clear()
            TermHandler.last_update_date = datetime.datetime.now()
            await asyncio.gather(TermHandler._set_term_list(login_info),
                                 TermHandler._set_curr_term(login_info))
            TermHandler.has_fetched.set()

        await TermHandler.has_fetched.wait()

        target_term = TermHandler._get_target_term(term_offset) if term_offset != 0 else TermHandler.curr_term.session
        result = list(filter(lambda x: x.session.year == target_term.year and
                                       x.session.is_autumn == target_term.is_autumn, TermHandler.term_list))
        if len(result) > 0:
            return result[0]
        else:
            return None
