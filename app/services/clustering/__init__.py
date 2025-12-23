"""
Face clustering services
"""
from .base import ClusteringService


class DummyClusteringService(ClusteringService):
    """Dummy clustering service implementation"""

    async def cluster_faces(self, faces, progress_callback=None):
        return None  # Placeholder

    def get_service_name(self) -> str:
        return "Dummy Clustering Service"

    def get_service_type(self) -> str:
        return "local"


def get_clustering_service() -> ClusteringService:
    """Get clustering service instance"""
    return DummyClusteringService()


__all__ = ["ClusteringService", "get_clustering_service"]
