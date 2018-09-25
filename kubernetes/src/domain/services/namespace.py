from kubernetes.client import V1Namespace, V1ObjectMeta
from model.clients import KubernetesClients


class KubernetesNamespaceService(object):
    def __init__(self):
        pass

    def create(self, clients, name, labels, annotations):
        """
        :param KubernetesClients clients:
        :param str name:
        :param Dict labels:
        :param Dict annotations:
        :rtype: V1Namespace
        """
        # enable_network_policy = {'net.beta.kubernetes.io/network-policy': '{"ingress": {"isolation": "DefaultDeny"}}'}
        # namespace_meta = V1ObjectMeta(name=name, labels=labels, annotations={**enable_network_policy})
        namespace_meta = V1ObjectMeta(name=name, labels=labels, annotations=annotations)
        namespace = V1Namespace(metadata=namespace_meta)

        return clients.core_api.create_namespace(body=namespace, pretty='true')

    def get_namespace_name_for_sandbox(self, sandbox_id):
        """
        :param str sandbox_id:
        :rtype: str
        """
        # return "cloudshell-{}".format(sandbox_id)
        return "default"  # todo - alexaz - change this after implementing PrepreSandboxInfra

    # def get_all(self, space_id: str = None, cloud_account_id: str = None) -> V1NamespaceList:
    #     filter_query = '{sandbox_id_tag}'.format(sandbox_id_tag=DevboxTags.SANDBOX_ID)
    #     if space_id:
    #         filter_query += ',{tag}={value}'.format(tag=DevboxTags.SPACE_ID, value=space_id)
    #     if cloud_account_id:
    #         filter_query += ',{tag}={value}'.format(tag=DevboxTags.CLOUD_ACCOUNT_ID, value=cloud_account_id)
    #
    #     return Utils.run_and_log_time(func=lambda: self.core_v1_api.list_namespace(label_selector=filter_query),
    #                                   logger=self._logger)
    #
    # def get_by_id(self, filter_query) -> V1NamespaceList:
    #     return Utils.run_and_log_time(func=lambda: self.core_v1_api.list_namespace(label_selector=filter_query),
    #                                   logger=self._logger)
    #
    # def terminate(self, sandbox_id: str, space_id: str) -> Optional[TerminateSandboxResponse]:
    #     namespaces = self.get_all(space_id=space_id)
    #     tag = DevboxTags.SANDBOX_ID
    #     namespace_to_delete = next(iter([namespace for namespace in namespaces.items
    #                                      if namespace.metadata.labels[tag] == sandbox_id]), None)
    #     if namespace_to_delete:
    #         if self.get_status(sandbox_id) == SandboxStatus.TERMINATING:
    #             return TerminateSandboxResponse(success=True)
    #
    #         body = V1DeleteOptions(grace_period_seconds=5, orphan_dependents=False)
    #         Utils.run_and_log_time(
    #             func=lambda: self.core_v1_api.delete_namespace(name=namespace_to_delete.metadata.name, body=body,
    #                                                            pretty='true'),
    #             logger=self._logger)
    #
    #         return TerminateSandboxResponse(success=True)
    #     else:
    #         return None
    #
    # def get_status(self, sandbox_id: str) -> str:
    #     try:
    #         response = Utils.run_and_log_time(func=lambda: self.core_v1_api.read_namespace_status(name=sandbox_id),
    #                                           logger=self._logger)
    #         return response.status.phase
    #     except ApiException as aex:
    #         if aex.reason == 'Not Found' and aex.status == 404:
    #             return SandboxStatus.TERMINATING
    #         raise
    #
    # def update_annotation(self, namespace, key: str, value: str):
    #     namespace_meta = V1ObjectMeta(annotations={key: value})
    #     patched_namespace = V1Namespace(metadata=namespace_meta)
    #     Utils.run_and_log_time(func=lambda: self.core_v1_api.patch_namespace(name=namespace.metadata.name,
    #                                                                          body=patched_namespace),
    #                            logger=self._logger)
