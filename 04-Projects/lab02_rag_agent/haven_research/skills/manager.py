"""
haven_research/skills/manager.py - Agent Skills 技能管理与动态发现引擎

【大厂 Agent 扩展规范】:
自动扫描 haven_research/skills/ 目录下的 SKILL.md 技能说明书与 Python 工具脚本，
提取技能元数据 (YAML Frontmatter)，并为 Agent 动态注册与执行专属 Skills 技能。
"""

import os
import yaml
import importlib.util
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from haven_research.core import logger


class SkillMetadata(BaseModel):
    """Skill 技能元数据 DTO"""
    name: str = Field(..., description="技能唯一标识名称")
    description: str = Field(..., description="技能功能描述 (用于 LLM 意图匹配)")
    skill_dir: str = Field(..., description="技能所在的绝对目录路径")
    instructions: str = Field(default="", description="SKILL.md 正文提示词指导")


class SkillManager:
    """Agent Skills 技能管理器"""

    def __init__(self, skills_dir: Optional[str] = None):
        self.skills_dir = skills_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")
        self._loaded_skills: Dict[str, SkillMetadata] = {}
        self.discover_skills()

    def discover_skills(self) -> Dict[str, SkillMetadata]:
        """扫描技能目录并加载所有 SKILL.md 元数据"""
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir, exist_ok=True)
            logger.info(f"[SkillManager] 创建 Skills 技能目录: {self.skills_dir}")
            return {}

        self._loaded_skills.clear()
        logger.info(f"[SkillManager] 开始扫描 Skills 技能目录: {self.skills_dir}")

        for item in os.listdir(self.skills_dir):
            sub_dir = os.path.join(self.skills_dir, item)
            skill_md_path = os.path.join(sub_dir, "SKILL.md")
            
            if os.path.isdir(sub_dir) and os.path.exists(skill_md_path):
                try:
                    meta = self._parse_skill_md(skill_md_path, sub_dir)
                    if meta:
                        self._loaded_skills[meta.name] = meta
                        logger.info(f"[SkillManager] 成功注册 Skill 技能: 【{meta.name}】 - {meta.description}")
                except Exception as e:
                    logger.error(f"[SkillManager Error] 加载技能 '{item}' 失败: {e}")

        logger.info(f"[SkillManager] 技能扫描完毕，共加载 {len(self._loaded_skills)} 个可用 Skill。")
        return self._loaded_skills

    def _parse_skill_md(self, md_path: str, skill_dir: str) -> Optional[SkillMetadata]:
        """解析 SKILL.md 文件的 YAML Frontmatter 头部与正文"""
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_str = parts[1]
            body_str = parts[2].strip()
            data = yaml.safe_load(yaml_str) or {}
            
            name = data.get("name")
            desc = data.get("description", "")
            
            if name:
                return SkillMetadata(
                    name=name,
                    description=desc,
                    skill_dir=skill_dir,
                    instructions=body_str
                )
        return None

    def get_skill_instructions_prompt(self) -> str:
        """格式化所有可用技能指令，供注入大模型 System Prompt"""
        if not self._loaded_skills:
            return ""

        lines = ["【可选 Agent Skills 技能库】:"]
        for name, meta in self._loaded_skills.items():
            lines.append(f"- 技能 [{name}]: {meta.description}")
        return "\n".join(lines)
