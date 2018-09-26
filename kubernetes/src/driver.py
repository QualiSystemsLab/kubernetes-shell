from cloudshell.core.context.error_handling_context import ErrorHandlingContext
from cloudshell.cp.core import DriverRequestParser
from cloudshell.cp.core.utils import single
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.cp.core.models import DriverResponse, DeployApp, CleanupNetwork
from cloudshell.shell.core.driver_context import InitCommandContext, AutoLoadCommandContext, ResourceCommandContext, \
    AutoLoadAttribute, AutoLoadDetails, CancellationContext, ResourceRemoteCommandContext

from cloudshell.shell.core.session.logging_session import LoggingSessionContext

import data_model
from domain.operations.autoload import AutolaodOperation
from domain.operations.cleanup import CleanupSandboxInfraOperation
from domain.operations.deploy import DeployOperation
from domain.operations.prepare import PrepareSandboxInfraOperation
from domain.services.clients import ApiClientsProvider
from domain.services.namespace import KubernetesNamespaceService
from domain.services.networking import KubernetesNetworkingService


class KubernetesDriver (ResourceDriverInterface):

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.request_parser = DriverRequestParser()

        # services
        self.api_clients_provider = ApiClientsProvider()
        self.networking_service = KubernetesNetworkingService()
        self.namespace_service = KubernetesNamespaceService()

        # operations
        self.autoload_operation = AutolaodOperation(api_clients_provider=self.api_clients_provider)
        self.deploy_operation = DeployOperation(self.networking_service,
                                                self.namespace_service)
        self.prepare_operation = PrepareSandboxInfraOperation(self.namespace_service)
        self.cleanup_operation = CleanupSandboxInfraOperation(self.namespace_service)

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        pass

    # <editor-fold desc="Discovery">

    def get_inventory(self, context):
        """
        Discovers the resource structure and attributes.
        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """
        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            cloud_provider_resource = data_model.Kubernetes.create_from_context(context)
            self.autoload_operation.validate_config(cloud_provider_resource)

        return AutoLoadDetails([], [])

    # </editor-fold>

    # <editor-fold desc="Mandatory Commands">

    def Deploy(self, context, request=None, cancellation_context=None):
        """
        Deploy
        :param ResourceCommandContext context:
        :param str request: A JSON string with the list of requested deployment actions
        :param CancellationContext cancellation_context:
        :return:
        :rtype: str
        """
        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            # parse the json strings into action objects
            actions = self.request_parser.convert_driver_request_to_actions(request)

            # extract DeployApp action
            deploy_action = single(actions, lambda x: isinstance(x, DeployApp))

            # if we have multiple supported deployment options use the 'deploymentPath' property
            # to decide which deployment option to use.
            # deployment_name = deploy_action.actionParams.deployment.deploymentPath

            cloud_provider_resource = data_model.Kubernetes.create_from_context(context)
            clients = self.api_clients_provider.get_api_clients(cloud_provider_resource.cluster_name)

            deploy_result = self.deploy_operation.deploy_app(logger,
                                                             context.reservation.reservation_id,
                                                             cloud_provider_resource,
                                                             deploy_action,
                                                             clients,
                                                             cancellation_context)

            return DriverResponse(deploy_result).to_driver_response_json()

    def PowerOn(self, context, ports):
        """
        Will power on the compute resource
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        pass

    def PowerOff(self, context, ports):
        """
        Will power off the compute resource
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        pass

    def PowerCycle(self, context, ports, delay):
        pass

    def DeleteInstance(self, context, ports):
        """
        Will delete the compute resource
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        pass

    def GetVmDetails(self, context, requests, cancellation_context):
        """

        :param ResourceCommandContext context:
        :param str requests:
        :param CancellationContext cancellation_context:
        :return:
        """
        pass

    def remote_refresh_ip(self, context, ports, cancellation_context):
        """
        Will update the address of the computer resource on the Deployed App resource in cloudshell
        :param ResourceRemoteCommandContext context:
        :param ports:
        :param CancellationContext cancellation_context:
        :return:
        """
        pass

    # </editor-fold>


    ### NOTE: According to the Connectivity Type of your shell, remove the commands that are not
    ###       relevant from this file and from drivermetadata.xml.

    # <editor-fold desc="Mandatory Commands For L2 Connectivity Type">

    def ApplyConnectivityChanges(self, context, request):
        """
        Configures VLANs on multiple ports or port-channels
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param str request: A JSON string with the list of requested connectivity changes
        :return: a json object with the list of connectivity changes which were carried out by the driver
        :rtype: str
        """
        pass

    # </editor-fold> 

    # <editor-fold desc="Mandatory Commands For L3 Connectivity Type">

    def PrepareSandboxInfra(self, context, request, cancellation_context):
        """

        :param ResourceCommandContext context:
        :param str request:
        :param CancellationContext cancellation_context:
        :return:
        :rtype: str
        """
        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            actions = self.request_parser.convert_driver_request_to_actions(request)

            cloud_provider_resource = data_model.Kubernetes.create_from_context(context)
            clients = self.api_clients_provider.get_api_clients(cloud_provider_resource.cluster_name)

            action_results = self.prepare_operation.prepare(logger,
                                                            context.reservation.reservation_id,
                                                            clients,
                                                            actions)

            return DriverResponse(action_results).to_driver_response_json()

    def CleanupSandboxInfra(self, context, request):
        """

        :param ResourceCommandContext context:
        :param str request:
        :return:
        :rtype: str
        """
        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            actions = self.request_parser.convert_driver_request_to_actions(request)
            cleanup_action = single(actions, lambda x: isinstance(x, CleanupNetwork))

            cloud_provider_resource = data_model.Kubernetes.create_from_context(context)
            clients = self.api_clients_provider.get_api_clients(cloud_provider_resource.cluster_name)

            action_result = self.cleanup_operation.cleanup(logger,
                                                           clients,
                                                           context.reservation.reservation_id,
                                                           cleanup_action)

            return DriverResponse([action_result]).to_driver_response_json()

    # </editor-fold>

    # <editor-fold desc="Optional Commands For L3 Connectivity Type">

    def SetAppSecurityGroups(self, context, request):
        """

        :param ResourceCommandContext context:
        :param str request:
        :return:
        :rtype: str
        """
        pass

    # </editor-fold>

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files, etc.
        """
        pass