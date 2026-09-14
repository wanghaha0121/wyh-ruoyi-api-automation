import pytest
import requests

from utils.api_request import api_request


#登录，获取token
def test_login(client):
    resp = api_request(
        session=client,
        method='post',
        url='/login',
        json_data={
            "username": "admin",
            "password": "admin123"
        }
    )
    assert resp.json()["code"] == 200

#验证用户信息
def test_getinfo(user_client):
    resp = api_request(
        session=user_client,
        method='get',
        url='/getInfo'
    )
    assert resp.json()["code"] == 200

#退出登录
def test_logout(fresh_client):
    resp = api_request(
        session=fresh_client,
        method='post',
        url='/logout'
    )
    assert resp.json()["code"] == 200


#退出后token应该失效
def test_logout_invalidates_token(fresh_client):
    r1 = api_request(
        session=fresh_client,
        method='post',
        url='/logout'
    )
    assert r1.json()["code"]==200
    r2 = api_request(
        session=fresh_client,
        method='get',
        url='/getInfo'
    )
    assert r2.json()["code"]==401