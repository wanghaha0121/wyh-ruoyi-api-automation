import requests

# 常量：基础域名，统一管理
BASE_URL = "http://localhost:5173/dev-api"
#默认接口走10s
TIMEOUT = 10

def api_request(session, method, url, params=None, json_data=None, headers=None,timeout=TIMEOUT):
    # 1.拼接完整接口地址
    full_url = BASE_URL + url
    # 2.发起请求
    response = session.request(
        method=method,
        url=full_url,
        params=params,
        json=json_data,
        headers=headers,
        timeout=TIMEOUT#普通接口走10s，个别慢接口在自己所在的代码中自己定义，此为处理接口超时
    )
    # 3.直接返回response对象，交给测试用例做业务断言
    return response
