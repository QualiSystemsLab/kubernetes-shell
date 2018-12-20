import os
from kubernetes import config
from kubernetes.client import CoreV1Api, AppsV1beta1Api

from model.clients import KubernetesClients


class ApiClientsProvider(object):

    def get_api_clients(self, kube_clp):
        """
        :param data_model.Kubernetes kube_clp:
        :rtype: KubernetesClients
        """
        if not os.path.isfile(kube_clp.config_file_path):
            raise ValueError("Config File Path is invalid. Cannot open file '{}'.".format(kube_clp.config_file_path))

        # todo - alexaz - Need to add support for urls so that we can download a config file from a central location and
        # todo          - also have the config file password protected.
        api_client = config.new_client_from_config(config_file=kube_clp.config_file_path)
        core_api = CoreV1Api(api_client=api_client)
        apps_api = AppsV1beta1Api(api_client=api_client)

        return KubernetesClients(api_client, core_api, apps_api)


# class ConfigBuilderBase(object):
#     _config_base_template = "apiVersion: v1\n" \
#                             "clusters: \n" \
#                             "- cluster: \n" \
#                             "[[cluster_section]]" \
#                             "  name: {cluster_name}\n" \
#                             "contexts: \n" \
#                             "- context: \n" \
#                             "    cluster: {cluster_name}\n" \
#                             "    user: {username}\n" \
#                             "  name: {cluster_name}-context\n" \
#                             "current-context: {cluster_name}-context\n" \
#                             "kind: Config\n" \
#                             "preferences: {{}}\n" \
#                             "users: \n" \
#                             "- name: {username}\n" \
#                             "  user:\n"
#
#     def build(self, kube_clp):
#         raise NotImplementedError('Base class. Use a derived class instead.')
#
#     def _get_base_template(self, skip_tls_veify=True, certificate_authority=None):
#         cluster_section = self._build_cluster_section(skip_tls_veify, certificate_authority)
#         return self._config_base_template.replace("[[cluster_section]]", cluster_section)
#
#     def _build_cluster_section(self, skip_tls_veify, certificate_authority):
#         cluster_section = ""
#
#         if skip_tls_veify:
#             cluster_section += "    insecure-skip-tls-verify: true\n"
#
#         if certificate_authority:
#             cluster_section += "    certificate-authority: {}\n".format(certificate_authority)
#
#         cluster_section += "    server: {server}\n"
#
#         return cluster_section
#
#
# class BasicAuthConfigBuilder(ConfigBuilderBase):
#     def build(self, kube_clp):
#         """
#         :param data_model.Kubernetes kube_clp:
#         :rtype: str
#         """
#         config_template = super(BasicAuthConfigBuilder, self)._get_base_template()
#         config_template += "    username: {username}\n" \
#                            "    password: {password}\n"
#
#         return config_template.format(cluster_name=kube_clp.cluster_name,
#                                       server=kube_clp.server,
#                                       username=kube_clp.user,
#                                       password=kube_clp.password)
#
#
# class CertificateAuthConfigBuilder(ConfigBuilderBase):
#     def build(self, kube_clp):
#         """
#         :param data_model.Kubernetes kube_clp:
#         :rtype: str
#         """
#         config_template = super(CertificateAuthConfigBuilder, self)._get_base_template()
#         config_template += "    client-certificate-data: {certificate_data}\n" \
#                            "    client-key-data: {key_data}\n"
#
#         certificate_data = self._read_text_file(kube_clp.client_certificate_path)
#         key_data = self._read_text_file(kube_clp.client_key_path)
#
#         return config_template.format(cluster_name=kube_clp.cluster_name,
#                                       server=kube_clp.server,
#                                       certificate_data=certificate_data,
#                                       key_data=key_data,
#                                       username='cloudshell')
#
#     @staticmethod
#     def _read_text_file(file_path):
#         with open(file_path, 'r')as f:
#             return f.read()
#
#     # def _config_builder(self, cluster_name, server, username, password):
#     #     config = "apiVersion: v1\n" \
#     #              "clusters:\n" \
#     #              "- cluster:\n" \
#     #              "    insecure-skip-tls-verify: true\n" \
#     #              "    server: {server}\n" \
#     #              "  name: {cluster_name}\n" \
#     #              "contexts:\n" \
#     #              "- context:\n" \
#     #              "    cluster: {cluster_name}\n" \
#     #              "    user: {username}\n" \
#     #              "  name: {cluster_name}-context\n" \
#     #              "current-context: {cluster_name}-context\n" \
#     #              "kind: Config\n" \
#     #              "preferences: {{}}\n" \
#     #              "users:\n" \
#     #              "- name: {username}\n" \
#     #              "  user:\n" \
#     #              "    password: {password}\n" \
#     #              "    username: {username}\n".format(cluster_name=cluster_name,
#     #                                                  server=server,
#     #                                                  username=username,
#     #                                                  password=password)
#     #     return config
