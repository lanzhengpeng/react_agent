import httpx

def parse_openapi_tools(openapi_json, base_url):
    """
    解析 FastAPI 的 OpenAPI JSON，生成工具注册表
    openapi_json: FastAPI /openapi.json 返回的 JSON
    base_url: FastAPI 服务地址，例如 "http://127.0.0.1:8000"
    返回：
        tool_registry: dict {tool_name: {"func": func, "parameters": {...}, "description": str, "url": str, "method": str}}
    """
    tool_registry = {}
    paths = openapi_json.get("paths", {})
    components = openapi_json.get("components", {}).get("schemas", {})

    for path, methods in paths.items():
        for method, spec in methods.items():
            # 工具名
            tool_name = spec.get("operationId", f"{method}_{path}")
            description = spec.get("description", spec.get("summary", ""))

            # 参数解析
            parameters = {}
            request_body = spec.get("requestBody", {})
            content = request_body.get("content", {}).get("application/json", {})
            schema = content.get("schema", {})

            props = {}
            required_fields = []

            if "$ref" in schema:
                schema_name = schema["$ref"].split("/")[-1]
                schema_def = components.get(schema_name, {})
                props = schema_def.get("properties", {})
                required_fields = schema_def.get("required", [])
            elif "properties" in schema:
                props = schema.get("properties", {})
                required_fields = schema.get("required", [])

            for k, v in props.items():
                parameters[k] = {
                    "type": v.get("type", "string"),
                    "description": v.get("description", v.get("title", "")),
                    "default": v.get("default"),
                    "required": k in required_fields
                }

            # 完整 URL
            full_url = f"{base_url}{path}"

            # 生成可调用函数
            def make_func(url, method):
                def func(**kwargs):
                    if method.lower() == "get":
                        r = httpx.get(url, params=kwargs)
                    else:
                        r = httpx.post(url, json=kwargs)
                    r.raise_for_status()
                    try:
                        return r.json()
                    except:
                        return r.text
                return func

            # 注册工具，同时保存完整 URL 和 method
            tool_registry[tool_name] = {
                "func": make_func(full_url, method),
                "parameters": parameters,
                "description": description,
                "url": full_url,   # 保存完整请求 URL
                "method": method
            }

    return tool_registry


# ================== 使用示例 ==================
if __name__ == "__main__":
    import json

    with open("openapi.json", "r", encoding="utf-8") as f:
        openapi_json = json.load(f)

    base_url = "http://127.0.0.1:8000"
    tools = parse_openapi_tools(openapi_json, base_url)

    for name, info in tools.items():
        print(f"工具名: {name}")
        print(f"描述: {info['description']}")
        print(f"参数: {info['parameters']}")
        print(f"请求信息: url={info['url']}, method={info['method']}")
        print("-" * 50)

    tool_name = "compileUgCode"
    if tool_name in tools:
        func = tools[tool_name]["func"]
        result = func(code="PRINT 'Hello UG';", ugVersion="UG2306")
        print("调用结果:", result)
