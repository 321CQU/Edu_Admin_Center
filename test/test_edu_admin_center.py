import unittest

import grpc

from utils.tools.configManager import ConfigReader

from micro_services_protobuf.edu_admin_center import eac_service_pb2_grpc as eac_grpc
from micro_services_protobuf.edu_admin_center import eac_models_pb2 as eac_models
from micro_services_protobuf.mycqu_service import mycqu_model_pb2 as mycqu_models
from micro_services_protobuf.mycqu_service import mycqu_service_pb2_grpc as mycqu_grpc
from micro_services_protobuf.mycqu_service import mycqu_request_response_pb2 as mycqu_rr


class TestEduAdminCenter(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.channel = grpc.aio.insecure_channel('localhost:53212')
        self.stub = eac_grpc.EduAdminCenterStub(self.channel)

        config = ConfigReader()

        self.login_info = mycqu_rr.BaseLoginInfo(auth=config.get_config('test', 'auth'),
                                                 password=config.get_config('test', 'password'))
        self.sid = config.get_config('test', 'sid')

    async def asyncTearDown(self) -> None:
        await self.channel.close()

    async def test_validate_auth(self):
        res = await self.stub.ValidateAuth(self.login_info)
        print(res)
        self.assertIsInstance(res, eac_models.ValidateAuthResponse)

    async def test_fetch_enroll_course_info(self):
        res = await self.stub.FetchEnrollCourseInfo(mycqu_rr.FetchEnrollCourseInfoRequest(base_login_info=self.login_info,
                                                                                          is_major=True))
        print(res)
        self.assertIsInstance(res, mycqu_rr.FetchEnrollCourseInfoResponse)

    async def test_fetch_enroll_course_item(self):
        res = await self.stub.FetchEnrollCourseItem(mycqu_rr.FetchEnrollCourseItemRequest(base_login_info=self.login_info,
                                                                                          id='10000004360', is_major=True))
        print(res)
        self.assertIsInstance(res, mycqu_rr.FetchEnrollCourseItemResponse)

    async def test_fetch_exam(self):
        res = await self.stub.FetchExam(mycqu_rr.FetchExamRequest(base_login_info=self.login_info, stu_id=self.sid))
        print(res)
        self.assertIsInstance(res, mycqu_rr.FetchExamResponse)

    async def test_fetch_course_timetable(self):
        res1 = await self.stub.FetchCourseTimetable(eac_models.FetchCourseTimetableRequest(login_info=self.login_info,
                                                                                           code=self.sid, offset=0))
        # res2 = await self.stub.FetchCourseTimetable(eac_models.FetchCourseTimetableRequest(login_info=self.login_info,
        #                                                                                    code=self.sid, offset=1))
        print(res1)
        # print(res2)
        self.assertIsInstance(res1, eac_models.FetchCourseTimetableResponse)
        # self.assertIsInstance(res2, eac_models.FetchCourseTimetableResponse)

    async def test_fetch_score(self):
        res = await self.stub.FetchScore(mycqu_rr.FetchScoreRequest(base_login_info=self.login_info, is_minor=False))
        print(res)
        self.assertIsInstance(res, mycqu_rr.FetchScoreResponse)

    async def test_fetch_gpa_ranking(self):
        res = await self.stub.FetchGpaRanking(self.login_info)
        print(res)
        self.assertIsInstance(res, mycqu_models.GpaRanking)


if __name__ == '__main__':
    unittest.main()
