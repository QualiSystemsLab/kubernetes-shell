from cloudshell.cp.core.models import DeployApp, DeployAppResult
from cloudshell.shell.core.driver_context import CancellationContext

from domain.common.utils import convert_to_int_list, create_deployment_model_from_action, \
    convert_app_name_to_valide_kubernetes_name
from domain.services.tags import TagsService
from model.clients import KubernetesClients
import data_model
from domain.services.networking import KubernetesNetworkingService
from domain.services.namespace import KubernetesNamespaceService
from domain.services.deployment import KubernetesDeploymentService
from logging import Logger

from model.deployment_requests import AppDeploymentRequest, ApplicationImage


class DeployOperation(object):
    def __init__(self, networking_service, namespace_service, deployment_service):
        """
        :param KubernetesNetworkingService networking_service:
        :param KubernetesNamespaceService namespace_service:
        :param KubernetesDeploymentService deployment_service
        """
        self.networking_service = networking_service
        self.namespace_service = namespace_service
        self.deployment_service = deployment_service

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
        kubernetes_app_name = convert_app_name_to_valide_kubernetes_name(deploy_action.actionParams.appName)

        namespace_obj = self.namespace_service.get_single_by_id(clients, sandbox_id)
        self._validate_namespace(namespace_obj, sandbox_id)
        namespace = namespace_obj.metadata.name

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

        image = ApplicationImage(deployment_model.docker_image_name,
                                 deployment_model.docker_image_tag)

        compute_spec = None
        # todo - alexaz - add 4 attributes: "cpu request", "ram request", "cpu limit" & "ram limit" and init
        # AppComputeSpecKubernetes object accordingly

        replicas = self._get_and_validate_replicas_number(deployment_model)

        deployment_request = AppDeploymentRequest(name=kubernetes_app_name,
                                                  image=image,
                                                  compute_spec=compute_spec,
                                                  internal_ports=internal_ports,
                                                  external_ports=external_ports,
                                                  replicas=replicas)

        self.deployment_service.create_app(logger=logger,
                                           clients=clients,
                                           namespace=namespace,
                                           name=kubernetes_app_name,
                                           labels=deployment_labels,
                                           app=deployment_request)

        # prepare result
        return DeployAppResult(deploy_action.actionId,
                               vmUuid=kubernetes_app_name,
                               vmName=deploy_action.actionParams.appName,
                               deployedAppAddress=kubernetes_app_name)  # todo - what address to use here?

    def _validate_namespace(self, namespace_obj, sandbox_id):
        if not namespace_obj:
            raise ValueError("Namespace for sandbox '{}' not found".format(sandbox_id))

    def _get_and_validate_replicas_number(self, deployment_model):
        """
        :param data_model.KubernetesService deployment_model:
        :rtype: int
        """
        replicas = int(deployment_model.replicas)
        if replicas < 1:
            raise ValueError("The number of replicas for the application must be 1 or greater")
        return replicas
