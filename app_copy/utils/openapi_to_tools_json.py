import copy
import json

def openapi_to_mcp_tools(openapi_spec: dict) -> dict:
    """
    将 OpenAPI 文档转换为 MCP tool 描述（支持 3.0/3.1，$ref 解引用，allOf 合并）
    返回形如：{"tools": [ {name, description, input_schema}, ... ]}
    """

    # ---------- 基础取值 ----------
    paths = openapi_spec.get("paths", {}) or {}
    components = openapi_spec.get("components", {}) or {}
    schemas = components.get("schemas", {}) or {}

    # ---------- 工具函数：$ref 解引用 ----------
    def resolve_ref(ref: str):
        # 仅处理 "#/components/schemas/Name" 这种
        if not ref.startswith("#/"):
            raise ValueError(f"不支持的 $ref：{ref}")
        parts = ref.lstrip("#/").split("/")
        node = openapi_spec
        for p in parts:
            node = node[p]
        return node

    def deep_resolve(schema: dict) -> dict:
        """递归解引用 + 处理 allOf 合并；保留 anyOf/oneOf 原样"""
        if not isinstance(schema, dict):
            return schema

        # $ref 优先
        if "$ref" in schema:
            resolved = deep_resolve(resolve_ref(schema["$ref"]))
            # 合并当前 schema 的其余键（比如加了 description 等）
            merged = copy.deepcopy(resolved)
            for k, v in schema.items():
                if k == "$ref":
                    continue
                merged[k] = deep_resolve(v)
            return merged

        # 处理 allOf 合并（浅合并 properties / required）
        if "allOf" in schema and isinstance(schema["allOf"], list):
            base = {"type": "object", "properties": {}, "required": []}
            # 如果原 schema 里有其他键，保留
            other_keys = {k: v for k, v in schema.items() if k != "allOf"}
            for sub in schema["allOf"]:
                sub_resolved = deep_resolve(sub)
                # 合并 type/object 属性
                if sub_resolved.get("type") == "object":
                    base.setdefault("properties", {})
                    base.setdefault("required", [])
                    base["properties"].update(sub_resolved.get("properties", {}))
                    if "required" in sub_resolved:
                        base["required"].extend(sub_resolved["required"])
                else:
                    # 若不是 object，就直接浅合并（保留 anyOf/oneOf 等）
                    for k, v in sub_resolved.items():
                        if k in ("properties", "required") and isinstance(v, dict):
                            base.setdefault(k, {})
                            base[k].update(v)
                        else:
                            base[k] = v
            # 去重 required
            if "required" in base:
                base["required"] = sorted(set(base["required"]))
            # 合并外层其他键
            base.update(other_keys)
            return base

        # 递归处理嵌套
        out = {}
        for k, v in schema.items():
            if isinstance(v, dict):
                out[k] = deep_resolve(v)
            elif isinstance(v, list):
                out[k] = [deep_resolve(i) for i in v]
            else:
                out[k] = v
        return out

    # ---------- 将 body schema 展平为 properties/required ----------
    def extract_body_params(op_details: dict):
        props = {}
        req = []
        rb = op_details.get("requestBody") or {}
        content = rb.get("content") or {}
        # 只处理 application/json；其他可按需扩展
        app_json = content.get("application/json")
        if not app_json:
            return props, req
        schema = app_json.get("schema") or {}
        schema = deep_resolve(schema)

        # 如果 body 顶层就是对象
        if schema.get("type") == "object" or "properties" in schema or "allOf" in schema or "anyOf" in schema or "oneOf" in schema:
            # 已经在 deep_resolve 里展开了 allOf/$ref
            body_props = schema.get("properties", {}) or {}
            # 补齐属性的 description（用 title 兜底）
            for k, v in body_props.items():
                if isinstance(v, dict) and "description" not in v and "title" in v:
                    v = copy.deepcopy(v)
                    v["description"] = v.get("description") or v.get("title")
                    body_props[k] = v
            props.update(body_props)
            if "required" in schema and isinstance(schema["required"], list):
                req.extend(schema["required"])

        # 如果 requestBody 标记为 required=True，但 schema 未列出 required，
        # 一般不强制所有属性为 required，这里不额外处理，保持 schema 的语义。
        return props, req

    # ---------- 提取 query/path 参数 ----------
    def extract_qp_params(op_details: dict):
        props = {}
        req = []
        for p in op_details.get("parameters", []) or []:
            pname = p["name"]
            pschema = deep_resolve(p.get("schema") or {})
            if not pschema:
                pschema = {"type": "string"}
            # 用 description 或 title
            if "description" not in p and "title" in pschema:
                pschema = copy.deepcopy(pschema)
                pschema["description"] = pschema.get("description") or pschema.get("title")
            if "description" not in pschema and "description" in p:
                pschema = copy.deepcopy(pschema)
                pschema["description"] = p["description"]
            props[pname] = pschema
            if p.get("required"):
                req.append(pname)
        return props, req

    tools = []

    for path, methods in paths.items():
        for method, details in methods.items():
            # 名称与描述
            name = details.get("operationId") or f"{method}_{path}".replace("/", "_")
            desc = details.get("summary") or details.get("description") or ""

            # 合并 query/path 参数 与 body 参数
            qp_props, qp_req = extract_qp_params(details)
            body_props, body_req = extract_body_params(details)

            properties = {}
            properties.update(qp_props)
            properties.update(body_props)

            required = []
            required.extend(qp_req)
            required.extend(body_req)
            required = sorted(set(required))

            # 若既无参数也无 body，就给一个空对象
            input_schema = {
                "type": "object",
                "properties": properties,
            }
            if required:
                input_schema["required"] = required

            # 为每个属性补一个描述兜底
            for k, v in list(properties.items()):
                if isinstance(v, dict) and "description" not in v:
                    vv = copy.deepcopy(v)
                    if "title" in vv and not vv.get("description"):
                        vv["description"] = vv["title"]
                    properties[k] = vv

            tools.append({
                "name": name,
                "description": desc,
                "input_schema": input_schema
            })

    return {"tools": tools}


# ----------------- 简单自测（用你给的 openapi 片段） -----------------
if __name__ == "__main__":
    # 将你的 JSON 粘到 openapi_json 变量即可
    openapi_json = "YOUR_OPENAPI_DICT"  # <- 用你的字典替换

    mcp_tools = openapi_to_mcp_tools(openapi_json)
    print(json.dumps(mcp_tools, ensure_ascii=False, indent=2))
