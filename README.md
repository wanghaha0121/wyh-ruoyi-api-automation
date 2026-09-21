# 若依接口自动化测试

针对若依（RuoYi-Vue）管理后台系统管理模块的接口自动化测试，覆盖 **4 条业务链、18 条用例**。

## 技术栈

Python 3.12 / requests / pytest / pytest-html

## 前置条件

1. 本地启动若依后端（默认 `http://localhost:8080`）与前端（`http://localhost:5173`）
2. 确认配置为 `sys.account.captchaEnabled = false`，否则 `/login` 会卡在验证码
3. 本项目 `BASE_URL` 走前端代理 `http://localhost:5173/dev-api`；若只跑后端，
   在 `utils/api_request.py` 里改成 `http://localhost:8080` 即可

## 怎么跑

```bash
pip install requests pytest pytest-html
pytest -v --html=report.html --self-contained-html
```

浏览器打开 `report.html` 查看报告。

## 项目结构

```
├── conftest.py          # fixture：三种会话 / 造数据 / 收尾清理
├── pytest.ini           # pythonpath 配置
├── test_cases/
│   ├── test_login.py    # 链路1 登录鉴权
│   ├── test_user.py     # 链路2 用户 CRUD
│   ├── test_role.py     # 链路3 角色分配
│   └── test_dept.py     # 链路4 部门管理
└── utils/
    └── api_request.py   # 请求封装（统一 BASE_URL / timeout）
```

## 用例规模

共 **18 条**。最后一次本地运行：18 passed in 2.62s

| 文件 | 业务链 | 用例数 | 覆盖点 |
|---|---|---|---|
| test_login.py | 登录鉴权 | 4 | 登录取 token、登录后取用户信息、登出、登出后 token 失效 |
| test_user.py | 用户 CRUD | 7 | 新增 → 查询 → 修改 → 删除（4 条链式，同一条数据走完整生命周期）+ 参数化异常场景 3 条（用户名重复 / 缺 userName / userName 超 30 位） |
| test_role.py | 角色分配 | 3 | 建角色并分配给用户、回查详情确认关系、按业务顺序清理（先删用户后删角色） |
| test_dept.py | 部门管理 | 4 | 层级 ancestors、exclude 排除自身（防环形父子）、创建时归属部门、删除约束 601 |

> 说明：以上都是**链式**设计——每条链共用同一份数据（`role_chain` / `dept_chain` 容器传递 id），
> 数据在链尾才清理，中间用例不删自己建的数据。
> 因此用例之间有顺序依赖，按文件内定义顺序执行。

## 关键设计

- **三种会话分离**：`user_client`（session 级，复用登录 token）/ `client`（匿名，测未授权）/
  `fresh_client`（独立登录，测登出——token 作废后不能污染其他用例）
- **yield 型 fixture 管数据生命周期**：建数据 → 交给用例 → 收尾自动清理，
  用例失败时 teardown 照常执行
- **module 级 dict 容器把多条用例串成一条链**：`role_chain` / `dept_chain` 跨用例传递 id
- **断言业务码而非 HTTP 码**：若依所有响应都是 HTTP 200，真实结果在 body 的 `code` 里
  （401 / 500 / 601 都见过，删部门被拦是 **601** 不是 500）
- **参数化异常场景**：用 `pytest.mark.parametrize` 一张表驱动 3 条非法输入用例，
  且不只断言 `code`，还断言 `msg` 关键字——否则后端因别的原因报 500 也会"假通过"
- **每条用例现造随机唯一数据**：避开用户名 / 手机号 / 邮箱的全局唯一约束，
  否则第二条用例会被"XX已存在"抢先拦下，造成假失败
- **改类用例必回查**：不只断言接口返回 200，还要回列表 / 详情确认数据真的变了

## 测试中发现的缺陷

1. `GET /system/dept/treeselect` → 500「参数[deptId]要求类型为 Long」，
   实为端点不存在、被 `/{deptId}` 兜底命中，错误文案完全掩盖真因 → 前端"选择上级部门"下拉不可用
2. `GET /system/dept/roleDeptTreeselect/{roleId}` → 500「No static resource」，同上
3. `POST /system/role` 不传 `menuIds` → 后端空指针，Java 内部异常信息直接返回给前端
4. `POST /system/user` 不传 `password` → 仍返回 200 创建成功，产生永远无法登录的废号
5. `PUT /system/user` 不传 `deptId` → 用户部门被静默清成 NULL；不传 `roleIds` → 角色关联被清空
   （改一个字段丢一片关联）
6. `PUT /system/user` 的 `userName` 传新值返回 200，但库内不变（改名无效却报成功）
7. 未授权访问返回 HTTP 200 + 业务码 401，而非 HTTP 401
8. `POST /system/user` 的 `phonenumber` 传任意非法值（如 `"12345"`）仍返回 200 创建成功
   → 手机号格式无任何校验，脏数据可以进库
