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
        全量由 LLM 语义大模型驱动的智能意图分类与背景萃取引擎
        返回: (UserIntent, new_background_context)
        """
        query_trim = query.strip()
        has_existing_doc = bool(current_doc and len(current_doc.strip()) > 50)

        # 规则 0: 空输入保底
        if not query_trim:
            return UserIntent.CHAT_ONLY, existing_background

        # 全量调用大模型 (LLM) 进行高精度语义意图识别
        client = settings.get_llm_client()
        if client:
            try:
                system_prompt = f"""你是一个智能 Agent 系统的意图分类与背景萃取大模型引擎。
请深刻理解用户最新输入的语义意图，并结合上下文信息，输出标准的 JSON 格式：

{{
  "intent": "CHAT_ONLY" | "GENERATE_DOC" | "EDIT_DOC" | "RESEARCH_QNA",
  "reason": "简短分析用户的核心意图与选定逻辑",
  "extracted_background": "如果有提取到关于用户项目的最新背景、约束或偏好则写在此处，无则写为空字符串"
}}

【意图分类标准 (严格遵循语义优先原则)】：
1. CHAT_ONLY (对话与概念问答 - 绝不生成右侧画布文档)：
   - 用户咨询技术概念、原理解释（如：“Transformer架构是什么”、“什么是 RAG”、“介绍一下 CNN”）。
   - 用户进行打招呼、能力询问。
   - 对上文回答的质问、吐槽、纠错、追问或元问题（如：“为什么生成2024年的”、“你理解错了”）。
   - 补充介绍自己的项目背景，或简单的对话交流。

2. GENERATE_DOC (生成全新排版文档 - 触发右侧画布写画)：
   - 用户【明确指示】需要“生成、撰写、输出、设计”一份全新的结构化 Markdown 文档、架构报告、技术白皮书或方案全案。

3. EDIT_DOC (修改已有画布文档)：
   - 当前右侧画布已存在文档，且用户明确要求对该【右侧画布文档】做出具体的“修改某段、润色、增加章节、删除表格、重写结论”等增量修饰指令。

4. RESEARCH_QNA (深度网络检索答疑)：
   - 用户询问包含最新信息/特定链接（如 GitHub 仓库或最新新闻），希望大模型进行实时网络检索并在【聊天框】内给出深度的答疑回复，但不创建右侧画布文档。

【当前上下文状态】：
- 当前右侧画布是否已有排版文档: {"是 (已有画布文档)" if has_existing_doc else "否 (画布为空)"}"""

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
                    updated_bg = f"{updated_bg} | {new_bg}" if updated_bg else new_bg

                try:
                    intent = UserIntent(intent_str)
                    # 纠错：如果判定为 EDIT_DOC 但当前根本没有已有文档，回退为 GENERATE_DOC
                    if intent == UserIntent.EDIT_DOC and not has_existing_doc:
                        intent = UserIntent.GENERATE_DOC
                    logger.info(f"[LLM Intent Router] 🤖 LLM 语义判定结果: {intent.value} | 理由: '{data.get('reason')}' | 提取背景: '{new_bg}'")
                    return intent, updated_bg
                except ValueError:
                    pass

            except Exception as e:
                logger.warning(f"[LLM Intent Router Warning] 大模型意图判定异常 ({e})，安全保底为 CHAT_ONLY...")

        # 保底降级：默认为 CHAT_ONLY (纯对话答疑，绝不擅自动用大报告生成引擎)
        logger.info(f"[LLM Intent Router Fallback] 默认安全保底: CHAT_ONLY")
        return UserIntent.CHAT_ONLY, existing_background

    async def route_and_extract_async(
        self,
        query: Optional[str] = None,
        user_query: Optional[str] = None,
        current_doc: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        existing_background: Optional[str] = None,
        history_bg: Optional[str] = None
    ) -> Tuple[UserIntent, Optional[str]]:
        """
        全量由 LLM 语义大模型驱动的异步智能意图分类与背景萃取引擎
        """
        bg_ctx = existing_background or history_bg
        target_query = (user_query or query or "").strip()
        has_existing_doc = bool(current_doc and len(current_doc.strip()) > 50)

        if not target_query:
            return UserIntent.CHAT_ONLY, bg_ctx

        async_client = settings.get_async_llm_client()
        if async_client:
            try:
                system_prompt = f"""你是一个智能 Agent 系统的意图分类与背景萃取大模型引擎。
请深刻理解用户最新输入的语义意图，并结合上下文信息，输出标准的 JSON 格式：

{{
  "intent": "CHAT_ONLY" | "GENERATE_DOC" | "EDIT_DOC" | "RESEARCH_QNA",
  "reason": "简短分析用户的核心意图与选定逻辑",
  "extracted_background": "如果有提取到关于用户项目的最新背景、约束或偏好则写在此处，无则写为空字符串"
}}

【意图分类标准 (严格遵循语义优先原则)】：
1. CHAT_ONLY (对话与概念问答 - 绝不生成右侧画布文档)：
   - 用户咨询技术概念、原理解释（如：“Transformer架构是什么”、“什么是 RAG”、“介绍一下 CNN”）。
   - 用户进行打招呼、能力询问。
   - 对上文回答的质问、吐槽、纠错、追问或元问题（如：“为什么生成2024年的”、“你理解错了”）。
   - 补充介绍自己的项目背景，或简单的对话交流。

2. GENERATE_DOC (生成全新排版文档 - 触发右侧画布写画)：
   - 用户【明确指示】需要“生成、撰写、输出、设计”一份全新的结构化 Markdown 文档、架构报告、技术白皮书或方案全案。

3. EDIT_DOC (修改已有画布文档)：
   - 当前右侧画布已存在文档，且用户明确要求对该【右侧画布文档】做出具体的“修改某段、润色、增加章节、删除表格、重写结论”等增量修饰指令。

4. RESEARCH_QNA (深度网络检索答疑)：
   - 用户询问包含最新信息/特定链接（如 GitHub 仓库或最新新闻），希望大模型进行实时网络检索并在【聊天框】内给出深度的答疑回复，但不创建右侧画布文档。

【当前上下文状态】：
- 当前右侧画布是否已有排版文档: {"是 (已有画布文档)" if has_existing_doc else "否 (画布为空)"}"""

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"用户最新输入: {target_query}"}
                ]

                response = await async_client.chat.completions.create(
                    model=settings.get_effective_model_name(),
                    messages=messages,
                    temperature=0.1
                )

                content = response.choices[0].message.content.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                data = json.loads(content)
                intent_str = data.get("intent", "CHAT_ONLY")
                new_bg = data.get("extracted_background", "").strip()

                try:
                    intent = UserIntent(intent_str)
                    if intent == UserIntent.EDIT_DOC and not has_existing_doc:
                        intent = UserIntent.GENERATE_DOC
                    logger.info(f"[LLM Intent Router] 🤖 LLM 语义判定结果: {intent.value} | 理由: '{data.get('reason')}' | 提取背景: '{new_bg}'")
                    return intent, new_bg
                except ValueError:
                    pass

            except Exception as e:
                logger.warning(f"[LLM Intent Router Warning] 大模型意图判定异常 ({e})，安全保底为 CHAT_ONLY...")

        logger.info(f"[LLM Intent Router Fallback] 默认安全保底: CHAT_ONLY")
        return UserIntent.CHAT_ONLY, bg_ctx

    # 别名兼容
    route_intent_async = route_and_extract_async
    route_intent = route_and_extract
