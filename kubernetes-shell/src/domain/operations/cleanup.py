from cloudshell.cp.core.models import CleanupNetwork, CleanupNetworkResult

from model.clients import KubernetesClients
from domain.services.namespace import KubernetesNamespaceService
from logging import Logger


class CleanupSandboxInfraOperation(object):
    def __init__(self, namespace_service):
        """
        :param KubernetesNamespaceService namespace_service:
        """
        self.namespace_service = namespace_service

    def cleanup(self, logger, clients, sandbox_id, cleanup_action):
        """
        :param Logger logger:
        :param KubernetesClients clients:
        :param str sandbox_id:
        :param CleanupNetwork cleanup_action:
        :return:
        """
        self.namespace_service.terminate(clients, sandbox_id)
        return CleanupNetworkResult(cleanup_action.actionId)
