import random

from conftest import chain
from utils.api_request import api_request

#分配
def test_assign_user_to_role(user_client,role_chain):
    assert chain.get("user_id") and chain.get("role_id"), "链路中断，先看 role_chain 前置是否失败"

    #先看这个user有没有分配role
    detail = api_request(
        session=user_client,
        method="get",
        url=f"/system/user/{chain['user_id']}"
    ).json()
    assert detail["code"] == 200, f"查询用户详情失败：{detail}"
    assert chain["role_id"] not in (detail.get("roleIds") or []),f"前置异常：分配前就已经有这个角色了，当前 roleIds={detail.get('roleIds')}"

    #分配
    resp = api_request(
        session=user_client,
        method="put",
        url="/system/role/authUser/selectAll",
        params={
            "roleId":chain["role_id"],
            "userIds":chain["user_id"]
        }
    )
    assert resp.json()["code"] == 200, f"分配角色失败：{resp.json()}"

    # 断言详情验证，断言roleId生效
def test_assign_user_verify(user_client,role_chain):
    assert chain.get("user_id"), "链路中断，先看 test_assign_role_to_user"
    resp = api_request(
        session=user_client,
        method="get",
        url=f"/system/user/{chain['user_id']}"
    )
    body = resp.json()
    assert body["code"] == 200, f"查询用户详情失败：{body}"

    # 依据一：验证roleIds是否正确
    role_ids = body.get("roleIds") or []
    assert chain["role_id"] in role_ids,f"角色未生效：期望 roleId={chain['role_id']}，实际 roleIds={role_ids}"

    # 依据二：验证roleKey是否正确
    role_keys = [r["roleKey"] for r in ((body.get("data") or {}).get("roles") or [])]
    assert chain["role_key"] in role_keys,f"权限字符不匹配：期望 roleKey={chain['role_key']}，实际={role_keys}"


#删除角色与用户
def test_delete_user_and_role(user_client,role_chain):
    #删除用户
    resp = api_request(
        session=user_client,
        method="delete",
        url=f"/system/user/{chain['user_id']}"
    )
    assert resp.json()["code"] == 200, f"删除用户失败：{resp.json()}"
    #删除角色
    resp = api_request(
        session=user_client,
        method="delete",
        url=f"/system/role/{chain['role_id']}"
    )
    assert resp.json()["code"] == 200, f"删除角色失败：{resp.json()}"

    # 删除用户后校验
    resp_del_list_user = api_request(
        session=user_client,
        method="get",
        url="/system/user/list",
        params={
            "pageNum": 1, "pageSize": 50, "userName": chain["user_name"]
        }
    )
    body = resp_del_list_user.json()
    assert body["msg"] == "查询成功", f"查询失败：{body}"
    assert body["total"] == 0, f"删除后用户依然存在！{body.get('rows')}"

    # 删除角色后校验
    resp_del_list_role = api_request(
        session=user_client,
        method="get",
        url="/system/role/list",
        params={
            "pageNum": 1, "pageSize": 50, "roleName": chain["role_name"]
        }
    )
    body = resp_del_list_role.json()
    assert body["msg"] == "查询成功", f"查询失败：{body}"
    assert body["total"] == 0, f"删除后角色依然存在！{body.get('rows')}"





