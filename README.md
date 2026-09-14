# 若依接口自动化测试

针对若依（RuoYi-Vue）管理后台的接口自动化测试。

## 技术栈
Python 3.12 / requests / pytest 8.x / pytest-html

## 怎么跑
```bash
pip install requests pytest pytest-html
pytest -v --html=report.html --self-contained-html
```
浏览器打开 `report.html` 看报告。

## 用例规模
- 总用例 23 条（按你实际数填）
- 业务链 4 条：登录鉴权 / 用户CRUD / 角色分配 / 部门管理
- 通过率 XX%（跑完填真实数字）

## 关键设计
- `conftest.py` 用 session 级 fixture 复用登录后的 token
- `test_dept.py` 用 yield 型 fixture 管理"建部门→查列表→取 deptId→删除"完整生命周期
- `test_user.py` 用 parametrize 一张数据表驱动用户 CRUD 的多种异常场景
