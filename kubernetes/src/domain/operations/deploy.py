from cloudshell.cp.core.models import DeployApp, DeployAppResult
from cloudshell.shell.core.driver_context import CancellationContext

from domain.common.utils import convert_to_int_list, create_deployment_model_from_action, \
    convert_app_name_to_valide_kubernetes_name
from domain.services.tags import TagsService
from model.clients import KubernetesClients
import data_model
from domain.services.networking import KubernetesNetworkingService
from domain.services.namespace import KubernetesNamespaceService
from logging import Logger

class DeployOperation(object):
    def __init__(self, networking_service, namespace_service):
        """
        :param KubernetesNetworkingService networking_service:
        :param KubernetesNamespaceService namespace_service:
        """
        self.networking_service = networking_service
        self.namespace_service = namespace_service

    def deploy_app(self, logger, sandbox_id, cloud_provider_resource, deploy_action, clients, cancellation_context):
        """
        :param Logger logger:
        :param str sandbox_id:
        :param data_model.Kubernetes cloud_provider_resource:
        :param DeployApp deploy_action:
        :param KubernetesClients clients:
        :param CancellationContext cancellation_context:
        :rtype: DeployAppResult
        """
        sandbox_tag = {TagsService.SANDBOX_ID: sandbox_id}

        deployment_model = create_deployment_model_from_action(deploy_action)

        namespace = self.namespace_service.get_namespace_name_for_sandbox(sandbox_id)
        kubernetes_app_name = convert_app_name_to_valide_kubernetes_name(deploy_action.actionParams.appName)

        # todo create annotations

        internal_ports = convert_to_int_list(deployment_model.internal_ports)
        external_ports = convert_to_int_list(deployment_model.external_ports)

        created_services = self.networking_service \
            .create_internal_external_set(namespace=namespace,
                                          name=kubernetes_app_name,
                                          labels=dict(sandbox_tag),
                                          internal_ports=internal_ports,
                                          external_ports=external_ports,
                                          clients=clients,
                                          logger=logger)

        deployment_labels = dict(sandbox_tag)
        for created_service in created_services:
            logger.info(created_service.spec.selector)
            deployment_labels.update(created_service.spec.selector)




