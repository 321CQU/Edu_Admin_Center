import asyncio
from typing import List, Tuple, Awaitable, Iterable
from datetime import datetime

import aiomysql
from grpc.aio import ServicerContext
from grpc import StatusCode

from micro_services_protobuf.edu_admin_center import eac_service_pb2_grpc as eac_grpc
from micro_services_protobuf.edu_admin_center import eac_models_pb2 as eac_models
from micro_services_protobuf.mycqu_service import mycqu_model_pb2 as mycqu_models
from micro_services_protobuf.mycqu_service import mycqu_service_pb2_grpc as mycqu_grpc
from micro_services_protobuf.mycqu_service import mycqu_request_response_pb2 as mycqu_rr

from _321CQU.tools.gRPCManager import gRPCManager, ServiceEnum
from _321CQU.tools.gRPCMethodErrorHandler import grpc_method_error_handler

from utils.AuthIdManager import AuthIdManager
from utils.TermHandler import TermHandler
from utils.sqlManager import SqlManager


__all__ = ['DB_TASK', 'EACServicer']


async def _add_score_to_cache(fetch_request: eac_models.FetchScoreRequest,
                              scores: mycqu_rr.FetchScoreResponse):
    uid = AuthIdManager().get_uid(fetch_request.sid)
    if uid is None:
        async with gRPCManager().get_stub(ServiceEnum.MycquService) as stub:
            stub: mycqu_grpc.MycquFetcherStub = stub
            res: mycqu_models.UserInfo = await stub.FetchUser(fetch_request.base_login_info)
            uid = AuthIdManager().add_uid(res.id, res.code, res.name)
    assert uid is not None

    scores: Iterable[mycqu_models.Score] = scores.scores
    target: List[Tuple[bytes, str, str, float, str, str, bool, str]] = []
    for score in scores:
        target.append((uid, score.course.code, score.course.name, score.course.credit,
                       score.course.instructor if len(score.course.instructor) else "未知教师",
                       str(score.session.year) + ("秋" if score.session.is_autumn else "春"),
                       score.study_nature == "初修",
                       score.score))

    async with SqlManager().cursor() as cursor:
        cursor: aiomysql.Cursor = cursor
        await cursor.executemany(
            "insert into ScoreCache (uid, cid, cname, credit, tname, term, is_initial, score) values "
            "(%s, %s, %s, %s, %s, %s, %s, %s) on duplicate key update "
            "ScoreCache.cname = cname, ScoreCache.credit = credit, ScoreCache.tname = tname,"
            "ScoreCache.is_initial = is_initial, ScoreCache.score = score", target
        )

DB_TASK: List[Awaitable] = []


class EACServicer(eac_grpc.EduAdminCenterServicer):
    @grpc_method_error_handler()
    async def ValidateAuth(self, request: mycqu_rr.BaseLoginInfo, context):
        async with gRPCManager().get_stub(ServiceEnum.MycquService) as stub:
            stub: mycqu_grpc.MycquFetcherStub = stub
            res: mycqu_models.UserInfo = await stub.FetchUser(request)
        uid = AuthIdManager().add_uid(res.id, res.code, res.name)
        return eac_models.ValidateAuthResponse(sid=res.code, auth=res.id, name=res.name, uid=uid)

    @grpc_method_error_handler()
    async def FetchEnrollCourseInfo(self, request: mycqu_rr.FetchEnrollCourseInfoRequest, context):
        async with gRPCManager().get_stub(ServiceEnum.MycquService) as stub:
            stub: mycqu_grpc.MycquFetcherStub = stub
            res = await stub.FetchEnrollCourseInfo(request)
        return res

    @grpc_method_error_handler()
    async def FetchEnrollCourseItem(self, request: mycqu_rr.FetchEnrollCourseItemRequest, context):
        async with gRPCManager().get_stub(ServiceEnum.MycquService) as stub:
            stub: mycqu_grpc.MycquFetcherStub = stub
            res = await stub.FetchEnrollCourseItem(request)
        return res

    @grpc_method_error_handler()
    async def FetchExam(self, request: mycqu_rr.FetchExamRequest, context):
        async with gRPCManager().get_stub(ServiceEnum.MycquService) as stub:
            stub: mycqu_grpc.MycquFetcherStub = stub
            res = await stub.FetchExam(request)
        return res

    @grpc_method_error_handler()
    async def FetchCourseTimetable(self, request: eac_models.FetchCourseTimetableRequest, context: ServicerContext):
        session = await TermHandler.get_term_info(request.login_info, request.offset)
        if session is None or request.offset > 1:
            await context.abort(StatusCode.INVALID_ARGUMENT, "无法获取该学期信息")

        if request.offset == 1:
            async with gRPCManager().get_stub(ServiceEnum.MycquService) as stub:
                stub: mycqu_grpc.MycquFetcherStub = stub
                timetables: mycqu_rr.FetchCourseTimetableResponse = await stub.FetchEnrollTimetable(
                    mycqu_rr.FetchEnrollTimetableRequest(base_login_info=request.login_info,
                                                         code=request.code)
                )
        else:
            async with gRPCManager().get_stub(ServiceEnum.MycquService) as stub:
                stub: mycqu_grpc.MycquFetcherStub = stub
                timetables: mycqu_rr.FetchCourseTimetableResponse = await stub.FetchCourseTimetable(
                    mycqu_rr.FetchCourseTimetableRequest(base_login_info=request.login_info,
                                                         code=request.code,
                                                         session=session.session)
                )
        return eac_models.FetchCourseTimetableResponse(
            course_timetables=timetables.course_timetables,
            start_date=datetime.fromtimestamp(session.begin_date).strftime("%Y-%m-%d"),
            end_date=datetime.fromtimestamp(session.end_date).strftime("%Y-%m-%d"),
            session_name=(str(session.session.year) + ("秋" if session.session.is_autumn else "春"))
        )

    @grpc_method_error_handler()
    async def FetchScore(self, request: eac_models.FetchScoreRequest, context):
        async with gRPCManager().get_stub(ServiceEnum.MycquService) as stub:
            stub: mycqu_grpc.MycquFetcherStub = stub
            result = await stub.FetchScore(request)
        task = asyncio.create_task(_add_score_to_cache(request, result))
        DB_TASK.append(task)
        return result

    @grpc_method_error_handler()
    async def FetchGpaRanking(self, request: mycqu_rr.BaseLoginInfo, context):
        async with gRPCManager().get_stub(ServiceEnum.MycquService) as stub:
            stub: mycqu_grpc.MycquFetcherStub = stub
            res = await stub.FetchGpaRanking(request)
        return res

