"""
haven_research/editor/document_editor.py - Artifacts 智能文档协同编辑器

【多轮 Agent 核心组件】:
针对 EDIT_DOC 意图，结合当前已有的 Markdown 大文档、用户指令、持久化项目背景与历史对话，
生成流畅修订后的全新版本文档 (v1.1, v1.2 等)，支持 SSE 逐字打字机推流。
"""

import json
from typing import AsyncGenerator, Dict, Any, Optional, List
from openai import AsyncOpenAI
from haven_research.config import settings
from haven_research.core import logger


class DocumentEditor:
    """Artifacts 文档编辑与修订引擎"""

    def __init__(self):
        self.client = None
        if getattr(settings, "openai_api_key", None):
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=getattr(settings, "openai_base_url", "https://api.deepseek.com")
            )

    async def edit_document_stream(
        self,
        current_document: str,
        edit_instruction: str,
        background_context: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        current_version: str = "v1.0"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式对已有文档进行局部修订与全量平滑重构
        yield 事件格式与 HavenResearcher 保持统一 (type: persona / chunk / complete)
        """
        yield {
            "type": "persona",
            "content": f"[Artifact Editor] 正在依据修改指令与上下文背景，增量修订文档 ({current_version} ➔ 下一版本)..."
        }

        # 计算下一个版本号 (如 v1.0 -> v1.1)
        next_version = self._calculate_next_version(current_version)

        system_prompt = f"""你是一位专业的资深技术文档编辑与架构师。
你的任务是根据用户的修改指令，对已有的技术文档进行精准的局部修饰、补全或格式优化，并输出【完全修改更新后的完整 Markdown 文档】。

【全局约束原则】：
1. 保持未受影响章节的结构与专业内容基本不变，仅对用户要求的段落/章节进行增删或重写。
2. 结合用户的全局项目背景与要求进行针对性优化。
3. 必须输出一份排版完整、可直接阅读的 Markdown 格式文档，不要添加任何开场白或“好的，我已为您修改”等系统客套话。

【全局项目背景 & 限制条件】：
{background_context or '暂无特殊全局背景'}

【当前最新文档原稿 ({current_version})】：
```markdown
{current_document}
```
"""

        user_prompt = f"用户的修改指令: {edit_instruction}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            if self.client:
                response = await self.client.chat.completions.create(
                    model=getattr(settings, "llm_model", "deepseek-chat"),
                    messages=messages,
                    temperature=0.3,
                    stream=True
                )

                full_chunks = []
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        delta = chunk.choices[0].delta.content
                        full_chunks.append(delta)
                        yield {
                            "type": "chunk",
                            "content": delta
                        }

            full_revised_doc = "".join(full_chunks)
            yield {
                "type": "complete",
                "version": next_version,
                "document": full_revised_doc,
                "sources": []
            }

        except Exception as e:
            logger.error(f"[DocumentEditor Error] 编辑流式生成失败: {e}")
            yield {
                "type": "chunk",
                "content": f"\n\n> ⚠️ 文档修订异常: {str(e)}"
            }
            yield {
                "type": "complete",
                "version": current_version,
                "document": current_document,
                "sources": []
            }

    def _calculate_next_version(self, version_str: str) -> str:
        """计算小版本号增长 (如 v1.0 -> v1.1, v1.9 -> v2.0)"""
        try:
            if not version_str or not version_str.startswith("v"):
                return "v1.1"
            parts = version_str[1:].split(".")
            major, minor = int(parts[0]), int(parts[1])
            minor += 1
            if minor >= 10:
                major += 1
                minor = 0
            return f"v{major}.{minor}"
        except Exception:
            return "v1.1"
