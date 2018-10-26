import traceback

from cloudshell.cp.core.models import DeployApp, DeployAppResult
from cloudshell.shell.core.driver_context import CancellationContext

from domain.common.additional_data_keys import DeployedAppAdditionalDataKeys
from domain.common.utils import convert_to_int_list, create_deployment_model_from_action, \
    convert_app_name_to_valide_kubernetes_name
from domain.services.tags import TagsService
from model.clients import KubernetesClients
import data_model
from domain.services.networking import KubernetesNetworkingService
from domain.services.namespace import KubernetesNamespaceService
from domain.services.deployment import KubernetesDeploymentService
from domain.services.vm_details import VmDetailsProvider
from logging import Logger
from typing import Dict

from model.deployment_requests import AppDeploymentRequest, ApplicationImage


class DeployOperation(object):
    def __init__(self, networking_service, namespace_service, deployment_service, vm_details_provider):
        """
        :param VmDetailsProvider vm_details_provider:
        :param KubernetesNetworkingService networking_service:
        :param KubernetesNamespaceService namespace_service:
        :param KubernetesDeploymentService deployment_service:
        """
        self.vm_details_provider = vm_details_provider
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

        try:
            created_services = self.networking_service \
                .create_internal_external_set(namespace=namespace,
                                              name=kubernetes_app_name,
                                              labels=dict(sandbox_tag),
                                              internal_ports=internal_ports,
                                              external_ports=external_ports,
                                              external_service_type=cloud_provider_resource.external_service_type,
                                              clients=clients,
                                              logger=logger)

            deployment_labels = dict(sandbox_tag)
            for created_service in created_services:
                deployment_labels.update(created_service.spec.selector)

            image = ApplicationImage(deployment_model.docker_image_name,
                                     deployment_model.docker_image_tag)

            compute_spec = None
            # todo - alexaz - add 4 attributes: "cpu request", "ram request", "cpu limit" & "ram limit" and init AppComputeSpecKubernetes object accordingly

            replicas = self._get_and_validate_replicas_number(deployment_model)
            environment_variables = self._get_environment_variables_dict(logger, deployment_model.environment_variables)

            deployment_request = AppDeploymentRequest(name=kubernetes_app_name,
                                                      image=image,
                                                      start_command=deployment_model.start_command,
                                                      environment_variables=environment_variables,
                                                      compute_spec=compute_spec,
                                                      internal_ports=internal_ports,
                                                      external_ports=external_ports,
                                                      replicas=replicas)

            created_deplomyent = self.deployment_service.create_app(logger=logger,
                                                                    clients=clients,
                                                                    namespace=namespace,
                                                                    name=kubernetes_app_name,
                                                                    labels=deployment_labels,
                                                                    app=deployment_request)

            vm_details = self.vm_details_provider.create_vm_details(created_services, created_deplomyent)

            additional_data = self._create_additional_data(namespace, replicas, deployment_model.wait_for_replicas)

            # prepare result
            return DeployAppResult(deploy_action.actionId,
                                   vmUuid=kubernetes_app_name,
                                   vmName=deploy_action.actionParams.appName,
                                   vmDetailsData=vm_details,
                                   deployedAppAdditionalData=additional_data,
                                   deployedAppAddress=kubernetes_app_name)  # todo - what address to use here?
        except:
            self._do_rollback_safely(logger=logger,
                                     clients=clients,
                                     namespace=namespace,
                                     cs_app_name=deploy_action.actionParams.appName,
                                     kubernetes_app_name=kubernetes_app_name)
            # raise the original exception to log it properly
            raise

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

    def _create_additional_data(self, namespace, replicas, wait_for_replicas_to_be_ready):
        """
        :param str namespace:
        :param int replicas:
        :param int wait_for_replicas_to_be_ready
        :rtype: Dict
        """
        return {
            DeployedAppAdditionalDataKeys.NAMESPACE: namespace,
            DeployedAppAdditionalDataKeys.REPLICAS: replicas,
            DeployedAppAdditionalDataKeys.WAIT_FOR_REPLICAS_TO_BE_READY: wait_for_replicas_to_be_ready
        }

    def _get_environment_variables_dict(self, logger, environment_variables):
        """
        :param Logger logger:
        :param str environment_variables:
        :rtype: Dict[str, str]
        """
        if not environment_variables or not environment_variables.strip():
            return None

        env_list = environment_variables.strip().split(',')

        env_dict = {}

        for env_str in env_list:
            try:
                key, value = env_str.split('=', 2)
                env_dict.update({key.strip(): value.strip()})
            except ValueError:
                logger.exception("Cannot unpack env var '{}' to key value pair. Missing '=' sign?".format(env_str))
                raise ValueError("Cannot parse environment variable '{}'. Expected format: key=value".format(env_str))

        return env_dict

    def _do_rollback_safely(self, logger, clients, namespace, cs_app_name, kubernetes_app_name):
        """
        :param str cs_app_name: object
        :param logging.Logger logger:
        :param KubernetesClients clients:
        :param str namespace:
        :param str kubernetes_app_name:
        :return:
        """
        logger.info('Doing rollback for app {} in ns/{}'.format(cs_app_name, namespace))

        try:
            self.networking_service.delete_internal_external_set(logger, clients, kubernetes_app_name, namespace)
            self.deployment_service.delete_app(logger, clients, app_name_to_delete=kubernetes_app_name, namespace=namespace)
        except:
            logger.error('Failed to do rollback for app {} in ns/{}. Error:'
                         .format(cs_app_name, namespace, traceback.format_exc()))
