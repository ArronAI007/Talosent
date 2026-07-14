"""Composition root for Talosent runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable
from typing import Any

from talosent.agent.workflows import ChatWorkflow, DEFAULT_SYSTEM_PROMPT, WorkflowSpec
from talosent.config import Settings, load_settings
from talosent.gateway import GatewayAdapter, GatewayRegistry
from talosent.memory import MemoryStore, build_memory_store as _build_memory_store
from talosent.plugins import PluginRegistry, PluginSpec
from talosent.providers import ChatProvider, build_provider
from talosent.skills import SkillRegistry, SkillSpec
from talosent.storage import StorageBackend, build_storage_backend as _build_storage_backend
from talosent.tools import ToolRegistry, build_tool_registry


@dataclass(slots=True)
class TalosentRuntime:
    settings: Settings
    provider: ChatProvider
    tools: ToolRegistry
    storage_backend: StorageBackend
    memory_store: MemoryStore
    skills: SkillRegistry
    plugins: PluginRegistry
    gateways: GatewayRegistry
    workflow: ChatWorkflow

    @property
    def provider_name(self) -> str:
        return getattr(self.provider, "name", self.provider.__class__.__name__)

    @property
    def tool_names(self) -> tuple[str, ...]:
        return self.tools.names()

    def summary(self) -> dict[str, Any]:
        return {
            "app_name": self.settings.app_name,
            "provider": self.provider_name,
            "model": self.settings.default_model,
            "tools": list(self.tool_names),
            "skills": list(self.skills.names()),
            "plugins": list(self.plugins.names()),
            "gateways": list(self.gateways.names()),
            "memory_backend": self.settings.memory_backend,
            "storage_backend": self.settings.storage_backend,
            "memory_entries": len(self.memory_store.items()),
            "storage_objects": len(self.storage_backend.items()),
        }


def build_storage_backend(
    settings: Settings | None = None,
    *,
    kind: str | None = None,
    root_path: str | Path | None = None,
) -> StorageBackend:
    runtime_settings = settings or load_settings()
    storage_kind = kind or runtime_settings.storage_backend
    return _build_storage_backend(storage_kind, root_path=root_path)


def build_memory_store(
    settings: Settings | None = None,
    *,
    kind: str | None = None,
    storage_backend: StorageBackend | None = None,
    namespace: str = "memory",
) -> MemoryStore:
    runtime_settings = settings or load_settings()
    memory_kind = kind or runtime_settings.memory_backend
    runtime_storage_backend = storage_backend
    normalized_kind = memory_kind.replace("-", "_").strip().lower()
    if runtime_storage_backend is None and normalized_kind in {
        "filesystem",
        "file_system",
        "persistent",
        "storage",
    }:
        runtime_storage_backend = build_storage_backend(runtime_settings, kind="filesystem")
    return _build_memory_store(memory_kind, storage_backend=runtime_storage_backend, namespace=namespace)


def build_skill_registry(specs: Iterable[SkillSpec] | None = None) -> SkillRegistry:
    registry = SkillRegistry()
    if specs is not None:
        registry.register_many(specs)
    return registry


def build_plugin_registry(specs: Iterable[PluginSpec] | None = None) -> PluginRegistry:
    registry = PluginRegistry()
    if specs is not None:
        registry.register_many(specs)
    return registry


def build_gateway_registry(adapters: Iterable[GatewayAdapter] | None = None) -> GatewayRegistry:
    registry = GatewayRegistry()
    if adapters is not None:
        registry.register_many(adapters)
    return registry


def build_runtime(
    settings: Settings | None = None,
    *,
    provider: ChatProvider | None = None,
    tools: ToolRegistry | None = None,
    storage_backend: StorageBackend | None = None,
    memory_store: MemoryStore | None = None,
    skills: SkillRegistry | None = None,
    plugins: PluginRegistry | None = None,
    gateways: GatewayRegistry | None = None,
    max_turns: int = 4,
    compression_max_messages: int = 24,
    compression_keep_messages: int = 12,
    compression_summary_items: int = 8,
    compression_summary_chars: int = 2000,
) -> TalosentRuntime:
    runtime_settings = settings or load_settings()
    runtime_provider = provider or build_provider(runtime_settings)
    runtime_tools = tools or build_tool_registry()
    runtime_storage = storage_backend or build_storage_backend(runtime_settings)
    normalized_memory_kind = runtime_settings.memory_backend.replace("-", "_").strip().lower()
    if storage_backend is None and normalized_memory_kind in {
        "filesystem",
        "file_system",
        "persistent",
        "storage",
    }:
        runtime_storage = build_storage_backend(runtime_settings, kind="filesystem")
    runtime_memory = memory_store or build_memory_store(
        runtime_settings,
        storage_backend=runtime_storage,
    )
    runtime_skills = skills or build_skill_registry()
    runtime_plugins = plugins or build_plugin_registry()
    runtime_gateways = gateways or build_gateway_registry()
    workflow = ChatWorkflow(
        spec=WorkflowSpec(name="chat", summary="Interactive chat workflow."),
        provider=runtime_provider,
        tools=runtime_tools,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        max_turns=max_turns,
        memory_store=runtime_memory,
        compression_max_messages=compression_max_messages,
        compression_keep_messages=compression_keep_messages,
        compression_summary_items=compression_summary_items,
        compression_summary_chars=compression_summary_chars,
    )
    return TalosentRuntime(
        settings=runtime_settings,
        provider=runtime_provider,
        tools=runtime_tools,
        storage_backend=runtime_storage,
        memory_store=runtime_memory,
        skills=runtime_skills,
        plugins=runtime_plugins,
        gateways=runtime_gateways,
        workflow=workflow,
    )


def build_chat_workflow(
    settings: Settings | None = None,
    *,
    provider: ChatProvider | None = None,
    tools: ToolRegistry | None = None,
    max_turns: int = 4,
    memory_store: MemoryStore | None = None,
    compression_max_messages: int = 24,
    compression_keep_messages: int = 12,
    compression_summary_items: int = 8,
    compression_summary_chars: int = 2000,
) -> ChatWorkflow:
    runtime = build_runtime(
        settings,
        provider=provider,
        tools=tools,
        memory_store=memory_store,
        max_turns=max_turns,
        compression_max_messages=compression_max_messages,
        compression_keep_messages=compression_keep_messages,
        compression_summary_items=compression_summary_items,
        compression_summary_chars=compression_summary_chars,
    )
    return runtime.workflow


__all__ = [
    "TalosentRuntime",
    "build_chat_workflow",
    "build_gateway_registry",
    "build_memory_store",
    "build_provider",
    "build_runtime",
    "build_plugin_registry",
    "build_storage_backend",
    "build_skill_registry",
    "build_tool_registry",
]
