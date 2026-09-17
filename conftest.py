import pytest
import requests
import random
from utils.api_request import api_request

LOGIN_DATA = {"username": "admin", "password": "admin123"}

#空fixture，测未授权场景
@pytest.fixture()
def client():
    s = requests.Session()
    yield s
    s.close()

#提取token
@pytest.fixture(scope='session')
def token():
    s = requests.Session()
    resp = api_request(
        session=s,
        method='post',
        url="/login",
        json_data=LOGIN_DATA
    )
    body = resp.json()
    assert body["code"] == 200, f"登录失败：{body}"
    assert body.get("token"), f"登录成功但没返回 token：{body}"
    s.close()
    return resp.json()["token"]

#带着token信息的session
@pytest.fixture(scope='session')
def user_client(token):
    s = requests.Session()
    s.headers.update({"Authorization":f"Bearer {token}"})#给session加上鉴权头
    yield s
    s.close()


#独立登录的会话，用于“登出”
@pytest.fixture()
def fresh_client():
    s = requests.Session()
    resp = api_request(
        session=s,
        method="post",
        url="/login",
        json_data=LOGIN_DATA
    )
    t = resp.json()["token"]
    s.headers.update({"Authorization":f"Bearer {t}"})
    yield s
    s.close()

#存放deptId的session
@pytest.fixture()
def create_dept(user_client):
    #新增
    dept_name = f"自动化部门_{random.randint(10000, 99999)}"
    resp = api_request(
        session=user_client,
        method='post',
        url='/system/dept',
        json_data={
            "parentId": "101",
            "deptName": dept_name,
            "orderNum": 0,
            "status": "0"
        }
    )
    assert resp.json()["code"] == 200, f"前置失败：新增部门 {resp.json()}"

    #查询
    resp_list = api_request(
        session=user_client,
        method='get',
        url='/system/dept/list',
        params={"deptName": dept_name}
    )
    rows = resp_list.json()["data"]
    matched = [d for d in rows if d["deptName"] == dept_name]
    assert matched, f"新增成功但查不到 {dept_name}，接口返回：{rows}"
    dept_id = matched[0]["deptId"]
    yield dept_id

    #删除
    api_request(
        session=user_client,
        method='delete',
        url=f'/system/dept/{dept_id}'
    )


#存放userId的session
@pytest.fixture()
def create_user(user_client):
    #新增
    suffix = random.randint(10000,99999)
    user_name = f"自动化用户_{suffix}"
    resp = api_request(
        session=user_client,
        method='post',
        url='/system/user',
        json_data={
            "userName":user_name,
            "nickName":user_name,
            "password":"123456",
            "status":"0",
            "postIds":[],
            "roleIds":[]
        }
    )
    assert resp.json()["code"] == 200, f"前置新增用户失败 {resp.json()}"

    #查询
    resp_list = api_request(
        session=user_client,
        method="get",
        url="/system/user/list",
        params={
                "userName":user_name
        }
    )
    rows = resp_list.json()["rows"]
    matched = [d for d in rows if d["userName"] == user_name]
    assert matched,f"新增成功，但是查不到用户：{user_name}"
    user_name = matched[0]["userName"]
    user_id = matched[0]["userId"]

    yield user_id,user_name

    # 删除
    api_request(
        session=user_client,
        method='delete',
        url=f'/system/user/{matched[0]["userId"]}'
    )

