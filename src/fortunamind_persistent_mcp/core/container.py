"""
Dependency Injection Container

Provides centralized dependency management for the FortunaMind Persistent MCP Server.
Enables loose coupling, easier testing, and better extensibility.
"""

import logging
from typing import Dict, Any, Optional, Type, TypeVar, Callable
from abc import ABC, abstractmethod

from fortunamind_persistent_mcp.config import Settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceRegistry:
    """Simple service registry for dependency injection"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        
    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """Register a singleton instance"""
        key = self._get_key(service_type)
        self._singletons[key] = instance
        logger.debug(f"Registered singleton: {key}")
        
    def register_factory(self, service_type: Type[T], factory: Callable[..., T]) -> None:
        """Register a factory function"""
        key = self._get_key(service_type)
        self._factories[key] = factory
        logger.debug(f"Registered factory: {key}")
        
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a specific instance"""
        key = self._get_key(service_type)
        self._services[key] = instance
        logger.debug(f"Registered instance: {key}")
        
    def get(self, service_type: Type[T]) -> Optional[T]:
        """Get a service instance"""
        key = self._get_key(service_type)
        
        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]
            
        # Check registered instances
        if key in self._services:
            return self._services[key]
            
        # Try factory
        if key in self._factories:
            instance = self._factories[key]()
            # Cache as singleton if it was registered as one
            self._singletons[key] = instance
            return instance
            
        logger.warning(f"Service not found: {key}")
        return None
        
    def _get_key(self, service_type: Type) -> str:
        """Get a consistent key for a service type"""
        return f"{service_type.__module__}.{service_type.__qualname__}"


class StorageFactory:
    """Factory for creating storage backends"""
    
    @staticmethod
    def create(storage_type: str, settings: Settings):
        """Create storage backend based on configuration"""
        if storage_type == "mock" or not settings.database_url or "mock" in settings.database_url:
            from ..persistent_mcp.storage import MockStorageBackend
            return MockStorageBackend(settings)
        elif storage_type == "supabase":
            from ..persistent_mcp.storage import SupabaseStorageBackend
            return SupabaseStorageBackend(settings)
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")


class AdapterFactory:
    """Factory for creating MCP adapters"""
    
    @staticmethod
    def create(adapter_type: str, registry, storage, auth, settings):
        """Create MCP adapter based on configuration"""
        if adapter_type == "http":
            from ..persistent_mcp.adapters import MCPHttpAdapter
            return MCPHttpAdapter(registry, storage, auth, settings)
        elif adapter_type == "stdio":
            from ..persistent_mcp.adapters import MCPStdioAdapter
            return MCPStdioAdapter(registry, storage, auth, settings)
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")


class DIContainer:
    """Main dependency injection container"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.registry = ServiceRegistry()
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the container and register services"""
        if self._initialized:
            return
            
        logger.info("Initializing dependency injection container")
        
        # Register core services
        self.registry.register_instance(Settings, self.settings)
        
        # Register storage factory
        self.registry.register_factory(
            type(None),  # We'll use string-based lookup for factories
            lambda: StorageFactory.create("auto", self.settings)
        )
        
        # Register authentication
        from ..persistent_mcp.auth import SubscriberAuth
        auth_instance = SubscriberAuth(self.settings)
        self.registry.register_singleton(SubscriberAuth, auth_instance)
        
        # Register tool registry
        try:
            # Try to use framework submodule to get ToolRegistry
            from framework.src.core.interfaces import ToolRegistry
            logger.info("Using framework ToolRegistry")
                
        except ImportError:
            # Fallback to mock registry
            from ..core.mock import ToolRegistry
            logger.warning("Using mock ToolRegistry - framework not available")
        
        tool_registry = ToolRegistry()
        self.registry.register_singleton(ToolRegistry, tool_registry)
        
        self._initialized = True
        logger.info("✅ Dependency injection container initialized")
        
    def get_storage(self):
        """Get storage backend instance"""
        # For now, create directly - will improve this
        storage_type = "mock" if "mock" in self.settings.database_url else "supabase"
        return StorageFactory.create(storage_type, self.settings)
        
    def get_adapter(self, adapter_type: str):
        """Get MCP adapter instance"""
        registry = self.registry.get(ToolRegistry)
        storage = self.get_storage()
        auth = self.registry.get(SubscriberAuth)
        
        return AdapterFactory.create(adapter_type, registry, storage, auth, self.settings)
        
    def get_service(self, service_type: Type[T]) -> Optional[T]:
        """Get a service from the container"""
        return self.registry.get(service_type)
        
    async def shutdown(self) -> None:
        """Cleanup container resources"""
        logger.info("Shutting down dependency injection container")
        
        # Cleanup storage if needed
        try:
            storage = self.get_storage()
            if hasattr(storage, 'cleanup'):
                await storage.cleanup()
        except Exception as e:
            logger.warning(f"Error during storage cleanup: {e}")
            
        self._initialized = False


# Global container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get the global container instance"""
    global _container
    if _container is None:
        raise RuntimeError("Container not initialized. Call initialize_container() first.")
    return _container


def initialize_container(settings: Settings) -> DIContainer:
    """Initialize the global container"""
    global _container
    _container = DIContainer(settings)
    return _container


async def shutdown_container() -> None:
    """Shutdown the global container"""
    global _container
    if _container:
        await _container.shutdown()
        _container = None