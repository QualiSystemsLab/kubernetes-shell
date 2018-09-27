from cloudshell.cp.core.models import PrepareCloudInfra, PrepareCloudInfraResult, PrepareSubnet, RequestActionBase, \
    PrepareSubnetActionResult, CreateKeys, CreateKeysActionResult
from cloudshell.cp.core.utils import single
from domain.services.namespace import KubernetesNamespaceService
from domain.services.tags import TagsService
from model.clients import KubernetesClients
from typing import List
from logging import Logger


class PrepareSandboxInfraOperation(object):
    def __init__(self, namespace_service):
        """
        :param KubernetesNamespaceService namespace_service:
        """
        self.namespace_service = namespace_service

    def prepare(self, logger, sandbox_id, clients, actions):
        """
        :param Logger logger:
        :param str sandbox_id:
        :param KubernetesClients clients:
        :param List[RequestActionBase] actions:
        :return:
        """

        self._validate_single_subnet_mode(actions)

        # we dont need any info from the actions at the moment so just prepare the results
        # extract actions and create results.
        prep_network_action = single(actions, lambda x: isinstance(x, PrepareCloudInfra))
        prep_network_action_result = PrepareCloudInfraResult(prep_network_action.actionId)

        prep_subnet_action = single(actions, lambda x: isinstance(x, PrepareSubnet))
        prep_subnet_action_result = PrepareSubnetActionResult(prep_subnet_action.actionId)

        # todo - alexaz - create the ssh key and returto cloudshell
        access_keys_action = single(actions, lambda x: isinstance(x, CreateKeys))
        access_keys_action_results = CreateKeysActionResult(access_keys_action.actionId)

        # generate namespace name for sandbox
        requested_namespace_name = self.namespace_service.get_namespace_name_for_sandbox(sandbox_id)
        logger.debug("Creating namespace '{}'".format(requested_namespace_name))

        # todo - alexaz - add more labels like 'createdby', 'owner', etc and add annotations
        labels = {TagsService.SANDBOX_ID: sandbox_id}

        # check if namesapce already exists
        namespace_obj = next(iter(self.namespace_service.get_by_id(clients, sandbox_id).items), None)
        if not namespace_obj:
            # create namespace for sandbox
            created_namespace = self.namespace_service.create(clients, requested_namespace_name, labels, None)
            logger.info("Created namespace '{}'".format(created_namespace.metadata.name))
        else:
            logger.info("Namespace '{}' already exists".format(requested_namespace_name))

        return [prep_network_action_result, prep_subnet_action_result, access_keys_action_results]

    def _validate_single_subnet_mode(self, actions):
        # validate single subnet mode
        if len(list(filter(lambda x: isinstance(x, PrepareSubnet), actions))) > 1:
            raise ValueError("Multiple subnets are not supported by the Kubernetes Shell")