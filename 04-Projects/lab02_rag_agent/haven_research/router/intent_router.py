"""
haven_research/router/intent_router.py - 智能意图路由与隐式背景萃取器

【多轮 Agent 核心组件】:
1. 意图分类: 将用户输入精准划分为 CHAT_ONLY (纯对话/问答), GENERATE_DOC (新建长文档), EDIT_DOC (修改已有文档), RESEARCH_QNA (实时深度搜索问答)
2. 背景萃取: 自动提取用户聊天中补充的项目背景、技术约束和偏好，存入持久化记忆中
"""

import json
import re
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
from openai import OpenAI
from haven_research.config import settings
from haven_research.core import logger


class UserIntent(str, Enum):
    CHAT_ONLY = "CHAT_ONLY"          # 纯对话/补充背景/词条解释/简单交流 (不影响右侧文档)
    GENERATE_DOC = "GENERATE_DOC"    # 首次或重新生成全量研究/技术大文档 (创建 v1.0 胶囊)
    EDIT_DOC = "EDIT_DOC"            # 基于已有文档做局部增删/润色/修订 (更新为 v1.1, v1.2)
    RESEARCH_QNA = "RESEARCH_QNA"    # 实时深度搜索问答 (在聊天框回答，不修改文档)


class IntentRouter:
    """智能意图路由与背景抽取引擎"""

    def __init__(self):
        pass

    def route_and_extract(
        self,
        query: str,
        current_doc: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        existing_background: Optional[str] = None
    ) -> Tuple[UserIntent, Optional[str]]:
        """
        分析用户 Intent 并静默提取新的背景知识
        返回: (UserIntent, new_background_context)
        """
        query_trim = query.strip()
        has_existing_doc = bool(current_doc and len(current_doc.strip()) > 50)

        # 规则 0: 极其简短的招呼、能力询问或针对上文回答的质问/吐槽/元问题 -> 锁定判定为 CHAT_ONLY
        short_chat_patterns = [
            r"^(你好|哈喽|hello|hi|嗨|在吗|早上好|下午好|晚上好|谢谢|多谢|再见|拜拜)$",
            r"^(你是谁|介绍一下你自己|你能做什么|你有什么能力)$"
        ]
        critique_patterns = [
            r".*(我不是让你|你怎么|为什么给|为什么说|你给我的|你生成的|这不是|为什么是|你报错|出错了).*"
        ]
        for pattern in short_chat_patterns:
            if re.match(pattern, query_trim, re.IGNORECASE):
                return UserIntent.CHAT_ONLY, existing_background
        for pattern in critique_patterns:
            if re.match(pattern, query_trim, re.IGNORECASE):
                logger.info(f"[IntentRouter Rule0] 匹配到追问/质问模式: '{query_trim}', 强制判定为 CHAT_ONLY")
                return UserIntent.CHAT_ONLY, existing_background

        # 尝试调用 LLM 进行极速智能判定 (JSON mode)
        client = settings.get_llm_client()
        if client:
            try:
                system_prompt = """你是一个智能 Agent 系统的意图分类与背景萃取引擎。
请分析用户最新的输入，输出标准的 JSON 格式：

{
  "intent": "CHAT_ONLY" | "GENERATE_DOC" | "EDIT_DOC" | "RESEARCH_QNA",
  "reason": "简短判定依据",
  "extracted_background": "如果有提取到关于用户项目的最新背景、约束或偏好则写在此处，无则写为空字符串"
}

分类规则：
1. CHAT_ONLY: 
   - 用户进行简单招呼或询问 Agent 能力。
   - 对上文生成结果的质问、追问、吐槽、澄清或元问题（如“为什么生成2024年的”、“我前面说的不是这个”）。
   - 补充介绍自己的项目背景，或简单的对话交流。
   （特别注意：质问与追问绝不重新生成大文档，必须划为 CHAT_ONLY 做出解释）
2. GENERATE_DOC: 用户明确指示“生成、撰写、输出”一份全新的完整架构设计/研究报告/技术白皮书。
3. EDIT_DOC: 当前已存在文档，且用户明确要求对该【右侧画布文档】做出具体的“修改某段、润色、增加章节、删除表格、重写结论”等增量修饰指令。
4. RESEARCH_QNA: 用户希望针对特定知识或最新信息进行简短检索并回答，不需要生成排版大文档。

当前上下文信息：
- 当前是否已存在排版文档: """ + ("是 (已生成大文档)" if has_existing_doc else "否 (无文档)")

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"用户最新输入: {query_trim}"}
                ]

                response = client.chat.completions.create(
                    model=settings.get_effective_model_name(),
                    messages=messages,
                    temperature=0.1,
                    response_format={"type": "json_object"} if "deepseek" in getattr(settings, "openai_base_url", "").lower() else None
                )

                content = response.choices[0].message.content.strip()
                # 尝试解析 JSON
                # 防御性清洗 json 标签
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                data = json.loads(content)
                intent_str = data.get("intent", "CHAT_ONLY")
                new_bg = data.get("extracted_background", "").strip()

                # 合并背景
                updated_bg = existing_background or ""
                if new_bg:
                    if updated_bg:
                        updated_bg += f" | {new_bg}"
                    else:
                        updated_bg = new_bg

                try:
                    intent = UserIntent(intent_str)
                    # 纠错规则：如果判定为 EDIT_DOC 但当前根本没有已有文档，回退为 GENERATE_DOC
                    if intent == UserIntent.EDIT_DOC and not has_existing_doc:
                        intent = UserIntent.GENERATE_DOC
                    logger.info(f"[IntentRouter] 智能路由结果: {intent.value} | 原因: {data.get('reason')} | 背景提取: '{new_bg}'")
                    return intent, updated_bg
                except ValueError:
                    pass

            except Exception as e:
                logger.warning(f"[IntentRouter Warning] LLM 意图判定失败 ({e})，安全降级到规则启发式...")

        # 规则启发式降级保底逻辑
        edit_keywords = ["修改", "改下", "润色", "增加节", "删除", "重写第三章", "加入表格", "优化文档"]
        gen_keywords = ["生成", "撰写", "编写", "设计文档", "研究报告", "出个方案", "写一份", "完整文档", "深度研究报告"]
        doc_search_keywords = ["深入分析并生成", "全面检索并输出文档"]

        if has_existing_doc and any(kw in query_trim for kw in edit_keywords):
            return UserIntent.EDIT_DOC, existing_background
        elif any(kw in query_trim for kw in gen_keywords):
            return UserIntent.GENERATE_DOC, existing_background
        elif any(kw in query_trim for kw in doc_search_keywords):
            return UserIntent.RESEARCH_QNA, existing_background
        else:
            # 概念问答 (如 "transformer架构是什么架构呢") 默认为 CHAT_ONLY 快速对话答疑
            return UserIntent.CHAT_ONLY, existing_background
