"""反思库 - 存储和检索历史反思经验"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib
from pathlib import Path


class ErrorType(Enum):
    """错误类型分类"""
    PARAMETER_ERROR = "parameter_error"
    TOOL_SELECTION_ERROR = "tool_selection_error"
    LOGIC_ERROR = "logic_error"
    ENVIRONMENT_ERROR = "environment_error"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ReflectionEntry:
    """反思条目"""
    id: str
    error_pattern: str
    error_type: ErrorType
    reflection: str
    suggested_actions: List[str]
    success_rate: float = 0.0
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "error_pattern": self.error_pattern,
            "error_type": self.error_type.value,
            "reflection": self.reflection,
            "suggested_actions": self.suggested_actions,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ReflectionEntry":
        """从字典创建"""
        return cls(
            id=data["id"],
            error_pattern=data["error_pattern"],
            error_type=ErrorType(data["error_type"]),
            reflection=data["reflection"],
            suggested_actions=data["suggested_actions"],
            success_rate=data.get("success_rate", 0.0),
            usage_count=data.get("usage_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_used_at=datetime.fromisoformat(data["last_used_at"]) if data.get("last_used_at") else None,
            metadata=data.get("metadata", {}),
        )

    def record_usage(self, success: bool) -> None:
        """
        记录使用情况

        Args:
            success: 是否成功
        """
        self.usage_count += 1
        self.last_used_at = datetime.now()

        # 更新成功率（使用指数移动平均）
        alpha = 0.3  # 学习率
        current_rate = 1.0 if success else 0.0
        self.success_rate = alpha * current_rate + (1 - alpha) * self.success_rate


class ReflectionLibrary:
    """
    反思库 - 存储和检索历史反思经验

    功能：
    - 错误模式识别和匹配
    - 反思建议检索
    - 成功率追踪
    - 自动优化和淘汰
    - 持久化存储
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        enable_persistence: bool = True,
        similarity_threshold: float = 0.7,
    ):
        """
        初始化反思库

        Args:
            storage_path: 存储文件路径
            enable_persistence: 是否启用持久化
            similarity_threshold: 相似度阈值
        """
        self.storage_path = storage_path or "reflexion_reflections.json"
        self.enable_persistence = enable_persistence
        self.similarity_threshold = similarity_threshold

        self.reflections: Dict[str, ReflectionEntry] = {}

        # 预定义的常见错误模式
        self._predefined_reflections = self._init_predefined_reflections()

        if enable_persistence:
            self.load()

    def _init_predefined_reflections(self) -> List[ReflectionEntry]:
        """初始化预定义的反思条目"""
        return [
            ReflectionEntry(
                id="pred_001",
                error_pattern="json decode",
                error_type=ErrorType.PARAMETER_ERROR,
                reflection="JSON解析失败，通常是因为格式错误或引号未闭合",
                suggested_actions=[
                    "检查JSON字符串的引号是否闭合",
                    "使用JSON验证工具验证格式",
                    "尝试使用更简单的字符串格式",
                ],
            ),
            ReflectionEntry(
                id="pred_002",
                error_pattern="key error",
                error_type=ErrorType.PARAMETER_ERROR,
                reflection="字典键不存在，可能是参数名称错误",
                suggested_actions=[
                    "检查参数名称是否正确",
                    "查看工具的参数定义",
                    "使用get()方法提供默认值",
                ],
            ),
            ReflectionEntry(
                id="pred_003",
                error_pattern="permission denied",
                error_type=ErrorType.PERMISSION_ERROR,
                reflection="权限不足，无法访问资源",
                suggested_actions=[
                    "检查文件/目录权限",
                    "使用管理员权限运行",
                    "选择其他可访问的路径",
                ],
            ),
            ReflectionEntry(
                id="pred_004",
                error_pattern="timeout",
                error_type=ErrorType.TIMEOUT_ERROR,
                reflection="操作超时，可能是网络问题或资源不可用",
                suggested_actions=[
                    "增加超时时间",
                    "检查网络连接",
                    "重试操作",
                ],
            ),
            ReflectionEntry(
                id="pred_005",
                error_pattern="argument",
                error_type=ErrorType.PARAMETER_ERROR,
                reflection="函数参数错误，类型或数量不匹配",
                suggested_actions=[
                    "检查参数类型",
                    "检查必需参数是否提供",
                    "查看函数签名确认参数列表",
                ],
            ),
        ]

    def add_reflection(
        self,
        error_pattern: str,
        error_type: ErrorType,
        reflection: str,
        suggested_actions: List[str],
        metadata: Optional[Dict] = None,
    ) -> ReflectionEntry:
        """
        添加反思条目

        Args:
            error_pattern: 错误模式
            error_type: 错误类型
            reflection: 反思内容
            suggested_actions: 建议的行动
            metadata: 元数据

        Returns:
            创建的反思条目
        """
        entry_id = self._generate_id(error_pattern, reflection)

        entry = ReflectionEntry(
            id=entry_id,
            error_pattern=error_pattern,
            error_type=error_type,
            reflection=reflection,
            suggested_actions=suggested_actions,
            metadata=metadata or {},
        )

        self.reflections[entry_id] = entry

        if self.enable_persistence:
            self.save()

        return entry

    def find_reflection(
        self,
        error_message: str,
        error_type: Optional[ErrorType] = None,
    ) -> Optional[ReflectionEntry]:
        """
        查找匹配的反思

        Args:
            error_message: 错误消息
            error_type: 可选的错误类型过滤

        Returns:
            匹配的反思条目或None
        """
        # 首先检查预定义反思
        for entry in self._predefined_reflections:
            if entry.error_pattern.lower() in error_message.lower():
                if error_type is None or entry.error_type == error_type:
                    return entry

        # 检查自定义反思
        candidates = []

        for entry in self.reflections.values():
            if error_type and entry.error_type != error_type:
                continue

            similarity = self._calculate_similarity(
                error_message,
                entry.error_pattern,
            )

            if similarity >= self.similarity_threshold:
                candidates.append((similarity, entry))

        # 返回最相似的反思
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]

        return None

    def get_top_reflections(
        self,
        error_type: Optional[ErrorType] = None,
        min_success_rate: float = 0.5,
        limit: int = 5,
    ) -> List[ReflectionEntry]:
        """
        获取top反思（按成功率排序）

        Args:
            error_type: 可选的错误类型过滤
            min_success_rate: 最低成功率
            limit: 返回数量限制

        Returns:
            反思条目列表
        """
        reflections = list(self.reflections.values())

        if error_type:
            reflections = [r for r in reflections if r.error_type == error_type]

        reflections = [r for r in reflections if r.success_rate >= min_success_rate]

        reflections.sort(key=lambda r: r.success_rate, reverse=True)

        return reflections[:limit]

    def update_reflection(
        self,
        entry_id: str,
        success: bool,
    ) -> bool:
        """
        更新反思使用情况

        Args:
            entry_id: 反思ID
            success: 是否成功

        Returns:
            是否成功更新
        """
        if entry_id in self.reflections:
            self.reflections[entry_id].record_usage(success)

            if self.enable_persistence:
                self.save()

            return True

        return False

    def cleanup_low_quality(self, min_usage: int = 5, max_success_rate: float = 0.3) -> int:
        """
        清理低质量反思

        Args:
            min_usage: 最小使用次数
            max_success_rate: 最大成功率阈值

        Returns:
            清理的数量
        """
        to_remove = []

        for entry_id, entry in self.reflections.items():
            if entry.usage_count >= min_usage and entry.success_rate < max_success_rate:
                to_remove.append(entry_id)

        for entry_id in to_remove:
            del self.reflections[entry_id]

        if to_remove and self.enable_persistence:
            self.save()

        return len(to_remove)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个字符串的相似度

        使用简单的词袋模型
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _generate_id(self, error_pattern: str, reflection: str) -> str:
        """生成唯一ID"""
        content = f"{error_pattern}:{reflection}"
        hash_obj = hashlib.md5(content.encode())
        return hash_obj.hexdigest()[:16]

    def save(self) -> None:
        """保存到文件"""
        if not self.enable_persistence:
            return

        data = {
            "reflections": {
                entry_id: entry.to_dict()
                for entry_id, entry in self.reflections.items()
            },
        }

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> None:
        """从文件加载"""
        if not self.enable_persistence:
            return

        path = Path(self.storage_path)
        if not path.exists():
            # 添加预定义反思
            for entry in self._predefined_reflections:
                self.reflections[entry.id] = entry
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.reflections = {
            entry_id: ReflectionEntry.from_dict(entry_data)
            for entry_id, entry_data in data.get("reflections", {}).items()
        }

    def get_stats(self) -> Dict[str, any]:
        """获取统计信息"""
        return {
            "total_reflections": len(self.reflections),
            "predefined_reflections": len(self._predefined_reflections),
            "by_error_type": {
                error_type.value: len([
                    r for r in self.reflections.values()
                    if r.error_type == error_type
                ])
                for error_type in ErrorType
            },
            "avg_success_rate": sum(
                r.success_rate for r in self.reflections.values()
            ) / len(self.reflections) if self.reflections else 0.0,
            "total_usage": sum(r.usage_count for r in self.reflections.values()),
        }

    def __len__(self) -> int:
        """返回反思数量"""
        return len(self.reflections)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"ReflectionLibrary(reflections={len(self.reflections)})"
