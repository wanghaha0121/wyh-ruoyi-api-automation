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


#存放role相关的session
chain = {}   #role链共用数据容器
@pytest.fixture(scope="module")
def role_chain(user_client):
    suffix = random.randint(10000,99999)
    role_name = f"自动化角色_{suffix}"
    role_key = f"auth_{suffix}"
    user_name = f"自动化用户_{suffix}"
    #建角色
    resp = api_request(
        session=user_client,
        method="post",
        url="/system/role",
        json_data={
            "roleName": role_name,
            "roleKey": role_key,
            "roleSort": 2,
            "status": "0",
            "menuIds": [],  # 不传 menuIds 后端会空指针，必须传
        },
    )
    assert resp.json()["code"] == 200, f"建角色失败：{resp.json()}"

    resp = api_request(
        session=user_client,
        method="get",
        url="/system/role/list",
        params={"pageNum": 1, "pageSize": 50, "roleName": role_name},
    )
    rows = resp.json().get("rows") or []
    matched = [r for r in rows if r["roleName"] == role_name]
    assert matched, f"角色建成功但查不到：{role_name}，返回={rows}"
    chain["role_id"] = matched[0]["roleId"]
    chain["role_key"] = role_key
    chain["role_name"] = role_name

    #建用户
    resp = api_request(
        session=user_client,
        method="post",
        url="/system/user",
        json_data={
            "userName": user_name,
            "nickName": user_name,
            "password": "123456",
            "status": "0",
            "postIds": [],
            "roleIds": [],  # 故意留空：后面才能断言"分配前是空的"
        },
    )
    assert resp.json()["code"] == 200, f"建用户失败：{resp.json()}"

    resp = api_request(
        session=user_client,
        method="get",
        url="/system/user/list",
        params={"pageNum": 1, "pageSize": 50, "userName": user_name},
    )
    rows = resp.json().get("rows") or []
    matched = [r for r in rows if r["userName"] == user_name]
    assert matched, f"用户建成功但查不到：{user_name}，返回={rows}"
    chain["user_id"] = matched[0]["userId"]
    chain["user_name"] = user_name

    yield chain

    #删除(先删用户再删角色)
    api_request(
        session=user_client,
        method="delete",
        url=f"/system/user/{chain['user_id']}"
    )
    api_request(
        session=user_client,
        method="delete",
        url=f"/system/role/{chain['role_id']}"
    )

#存放dept相关的session
dept_chain = {}
@pytest.fixture(scope="module")
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

    dept_chain["dept_id"] = matched[0]["deptId"]
    dept_chain["dept_name"] = dept_name
    dept_chain["parent_id"] = 101
    dept_chain["user_id"] = None
    yield dept_chain

    #删除，有用户挂着的部门删不动
    try:
        if dept_chain.get("user_id"):
            api_request(
                session=user_client,
                method="delete",
                url=f"/system/user/{dept_chain['user_id']}"
            )
        r = api_request(
            session=user_client,
            method="delete",
            url=f"/system/dept/{dept_chain['dept_id']}"
        )
        if r.json().get("code") != 200:
            print(f"兜底异常清理：{r.json()}")
    except Exception as e:
        print(f"兜底清理异常：{e}")
