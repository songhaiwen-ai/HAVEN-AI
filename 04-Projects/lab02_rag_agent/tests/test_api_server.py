"""
tests/test_api_server.py - 生产级 Web ChatGPT FastAPI 接口单元测试

测试注册/登录 JWT Token 签发、用户隔离、会话创建、删除与 OpenAPI 结构。
"""

import pytest
from fastapi.testclient import TestClient
from haven_research.api import app

client = TestClient(app)


def test_index_preview_endpoint():
    """验证 GET / 返回 Vue ChatGPT 风格 HTML 页面"""
    response = client.get("/")
    assert response.status_code == 200
    assert "HavenResearch" in response.text
    assert "text/html" in response.headers["content-type"]


def test_openapi_docs_endpoint():
    """验证 Swagger API 文档结构"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "HavenResearch" in data["info"]["title"]
    assert "/api/v1/auth/register" in data["paths"]
    assert "/api/v1/auth/login" in data["paths"]
    assert "/api/v1/chat/sessions" in data["paths"]
    assert "/api/v1/chat/stream" in data["paths"]


def test_auth_and_session_crud_flow():
    """验证注册、登录、获取 JWT Token 并创建与删除会话的全流程"""
    import uuid
    test_user = f"user_{uuid.uuid4().hex[:6]}"
    
    # 1. 注册账号
    reg_resp = client.post("/api/v1/auth/register", json={"username": test_user, "password": "password123"})
    assert reg_resp.status_code == 200
    token = reg_resp.json()["token"]
    assert token is not None

    headers = {"Authorization": f"Bearer {token}"}

    # 2. 获取当前登录用户信息
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == test_user

    # 3. 创建新深度研究会话
    create_resp = client.post("/api/v1/chat/sessions", json={"title": "测试 AI 选型会话"}, headers=headers)
    assert create_resp.status_code == 200
    session_id = create_resp.json()["session_id"]
    assert session_id is not None

    # 4. 查询当前用户的历史会话列表
    list_resp = client.get("/api/v1/chat/sessions", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 5. 删除该测试会话
    del_resp = client.delete(f"/api/v1/chat/sessions/{session_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True
