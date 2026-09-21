import random

import requests
import pytest

from conftest import create_user
from utils.api_request import api_request

def add_data(userName,nickName,password="123456",status="0",postIds=None,roleIds=None):
    body = {
        "userName":userName,
        "nickName":nickName,
        "password":password,
        "status":status,
        "postIds":postIds if postIds is not None else [],
        "roleIds":roleIds if roleIds is not None else []
    }
    return body

def change_data(userId,deptId,nickName,sex,status,userName):
    body = {"userId":userId,
            "userName": userName,
            "nickName": nickName,
            "status": status,
            "sex": sex,
            "deptId":deptId
    }
    return body

#添加用户
def test_add_user(user_client):
    suffix = random.randint(10000,99999)
    userName = f"自动化用户_{suffix}"
    req_body = add_data(
        userName=userName,
        nickName=userName,
        password="123456",
        status="0",
        postIds=[],
        roleIds=[],
    )
    resp = api_request(
        session=user_client,
        method="post",
        url="/system/user",
        json_data=req_body
    )
    body = resp.json()
    assert resp.json()["code"] == 200,f"新增用户失败：{body}"

    # #新增后校验：列表里能查到
    # resp_list = api_request(
    #     session=user_client,
    #     method="get",
    #     url="/system/user/list",
    #     params={"pageNum": "1",
    #             "pageSize": "10",
    #             "userName": user_name
    #     }
    # )
    # matched = [d for d in resp_list.json()["rows"] if d["userName"] == user_name]
    # assert matched, f"新增返回成功但列表查不到：{user_name}"

    # # 清理，不留脏数据
    # api_request(
    #     session=user_client,
    #     method="delete",
    #     url=f"/system/user/{matched[0]['userId']}"
    # )


#查询用户
def test_search_user(user_client, create_user):
    user_id,user_name= create_user

    resp = api_request(
        session=user_client,
        method="get",
        url="/system/user/list",
        params={
            "userName":user_name
        }
    )
    body = resp.json()
    assert body["msg"] == "查询成功",f"查询失败：{body}"
    assert body["total"] >= 1,f"查不到任何用户：{body}"

#修改用户（状态/手机号）
def test_change_user(user_client,create_user):
    user_id,user_name= create_user

    # 先查一次，拿到真实的 userName（用户名不能乱填，改名要单独走接口语义）
    detail = api_request(
        session=user_client,
        method="get",
        url=f"/system/user/list",
        params={
            "pageNum":"1",
            "pageSize":"10",
            "userName":user_name
        }
    ).json()["rows"]

    new_nick = f"修改用户名称_{random.randint(10000,99999)}"
    req_body = change_data(
        userId=user_id,
        userName=detail[0]["userName"],
        nickName=new_nick,
        sex="0",
        status="0",
        deptId=101
    )
    resp = api_request(
        session=user_client,
        method="put",
        url="/system/user",
        json_data=req_body
    )
    assert resp.json()["code"] == 200,f"修改用户失败：{resp.json()}"

    # 修改后校验：再查详情，确认真的改成功了
    after = api_request(
        session=user_client,
        method="get",
        url=f"/system/user/{user_id}"
    ).json()["data"]
    assert after["nickName"] == new_nick



#删除
def test_delete_user(user_client,create_user):
   user_id,user_name = create_user
   resp = api_request(
        session=user_client,
        method="delete",
        url=f"/system/user/{user_id}"
   )
   assert resp.json()["code"] == 200,f"删除用户失败：{resp.json()}"

   #删除后校验
   resp_del_list = api_request(
       session=user_client,
       method="get",
       url="/system/user/list",
       params={
           "userName":user_name
       }
   )
   body = resp_del_list.json()
   assert body["msg"] == "查询成功",f"查询失败：{body}"
   assert body["total"] == 0,f"删除后用户依然存在！{body}"


def make_user_payload(**overrides):
    """现造一份随机唯一的用户数据；overrides 用来把其中某个字段改成非法值"""
    suffix = random.randint(10000, 99999)
    payload = {
        "userName": f"自动化用户_{suffix}",
        "nickName": f"自动化用户_{suffix}",
        "password": "123456",
    }
    for k, v in overrides.items():
        if v is None:
            payload.pop(k,None)
        else:
            payload[k] = v
    return payload

@pytest.mark.parametrize("overrides, expect_msg",
    [({"userName": "admin"},   "登录账号已存在"),
    ({"userName": None},      "用户账号不能为空"),
    ({"userName": "a" * 31},  "长度不能超过30个字符"),],
    ids=["用户名重复", "缺userName", "userName超30位"])
def test_add_user_invalid(user_client, overrides, expect_msg):
    payload = make_user_payload(**overrides)
    print("=====本次发送payload=====", payload)  # 新增打印
    body = api_request(
        session=user_client,
        method="post",
        url="/system/user",
        json_data=payload
    ).json()
    try:
        assert body["code"] == 500, f"预期被拒绝，实际却成功了：{body}"
        assert expect_msg in body["msg"], f"报错原因不是预期的那一种：{body}"
    finally:
        # 兜底(如果后端改了行为，比如就像手机号那样不校验，这里会真的建成用户，必须清掉)
        if body.get("code") == 200 and payload.get("userName"):
            rows = api_request(
                session=user_client,
                method="get",
                url="/system/user/list",
                params={
                    "userName": payload["userName"]}
            ).json().get("rows") or []
            for row in rows:
                if row["userName"] == payload["userName"]:
                    api_request(
                        session=user_client,
                        method="delete",
                        url=f"/system/user/{row['userId']}"
                    )

