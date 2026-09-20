import random

from conftest import dept_chain
from utils.api_request import api_request


#1、看层级有没有挂对
def test_dept_detail_and_ancestors(user_client,create_dept):
    dept_name = dept_chain["dept_name"]
    resp = api_request(
        session=user_client,
        method="get",
        url="/system/dept/list",
        params={
            "deptName":dept_name
        }
    )

    assert resp.json()["code"] == 200
    assert resp.json()["data"][0]["ancestors"] == "0,100,101"
    assert resp.json()["data"][0]["parentId"] == 101


#2、改上级时部门选择是否正确
def test_dept_exclude_self(user_client,create_dept):
    dept_id = dept_chain["dept_id"]
    resp = api_request(
        session=user_client,
        method="get",
        url=f"/system/dept/list/exclude/{dept_id}"
    )
    body = resp.json()["data"]
    id_list = [item["deptId"] for item in body]
    assert dept_id not in id_list,f"自身id也在可选父级中，会形成闭环，{id_list}"


#3、判断归属在创建时就已经建立
def test_add_user_with_dept(user_client,create_dept):
    #用新建部门的id新建一个用户
    suffix = random.randint(10000, 99999)
    userName = f"自动化用户_{suffix}"
    resp = api_request(
        session=user_client,
        method="post",
        url="/system/user",
        json_data={
            "userName":userName,
            "nickName":userName,
            "password":"123456",
            "status":0,
            "postIds":[],
            "roleIds":[],
            "deptId":dept_chain["dept_id"]
        }
    )
    body = resp.json()
    assert resp.json()["code"] == 200, f"新增用户失败：{body}"

    #取出userId
    resp_list = api_request(
        session=user_client,
        method="get",
        url="/system/user/list",
        params={
            "userName": userName
        }
    )
    rows = resp_list.json()["rows"]
    matched = [d for d in rows if d["userName"] == userName]
    assert matched, f"新增成功，但是查不到用户：{userName}"
    user_id = matched[0]["userId"]
    dept_chain["user_id"] = user_id


    #查询这个部门id下是不是只有刚刚建的那一个用户
    resp_test = api_request(
        session=user_client,
        method="get",
        url="/system/user/list",
        params={
            "pageNum":1,
            "pageSize":10,
            "deptId":dept_chain["dept_id"]
        }
    )
    rows = resp_test.json()["rows"]
    # id_list = [int(item["userId"]) for item in rows]
    # user_id = int(user_id)
    # assert user_id in id_list, f"找不到userId，预期：{user_id}，实际结果：{id_list}"#间接证据，因为子部门的userId也会显示在父部门下面，这句断言不能说明user是在父部门下面的
    assert resp_test.json()["rows"][0]["deptId"] == dept_chain["dept_id"]#直接证据，直接说明这个部门id是不是我新建的部门
    assert resp_test.json()["total"] == 1,f"部门中的用户不唯一，{rows}"




#4、删除约束
def test_dept_delete_blocked_by_user(user_client,create_dept,):
    assert dept_chain.get("user_id"), "第 3 条没跑，链路中断，先看 test_add_user_with_dept"

    #当部门中还有用户时，删除部门失败报601
    dept_id = dept_chain["dept_id"]
    resp = api_request(
        session=user_client,
        method="delete",
        url=f"/system/dept/{dept_id}"
    )
    assert resp.json()["code"] == 601,f"不能删除成功，因为该部门下还有用户"

    #删掉用户后再删,删除成功报200
    api_request(
        session=user_client,
        method="delete",
        url=f"/system/user/{dept_chain['user_id']}"
    )
    assert api_request(
        session=user_client,
        method="delete",
        url=f"/system/dept/{dept_id}"
    ).json()["code"] == 200

    #列表里查不到了
    ids = [d["deptId"] for d in api_request(
        session=user_client,
        method="get",
        url="/system/dept/list"
    ).json()["data"]]
    assert dept_id not in ids




