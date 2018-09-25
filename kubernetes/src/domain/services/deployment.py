import json
from logging import Logger
from typing import List, Dict

from kubernetes.client import V1ObjectMeta, AppsV1beta1Deployment, AppsV1beta1Api, AppsV1beta1DeploymentSpec, \
    V1PodTemplateSpec, V1PodSpec, V1Container, V1ContainerPort, V1EnvVar

from aws.cloudformation.sidecar_userdata import SidecarUserDataService
from common.config import Config
from common.requests.create_sandbox_request import CreateSandboxAppRequest, CreateSandboxAppComputeSpec, \
    CreateSandboxAppInputParameter
from common.tags import DevboxTags, Const
from common.utils import Utils
from domain.bash_command_builder import BashCommandBuilder, ArtifactsCommandBuilder, \
    KubernetesAppContainerCommandBuilder, \
    CommonAppInstanceCommandBuilder, CommonBuilder
from domain.bash_command_builder import GithubCommandBuilder
from domain.bash_commands_log_scope import BashCommandsLogScope, SimpleCommandsContainer
from domain.convertors.kubernetes.kubernetes_converter import KubernetesConverter
from domain.request_objects import AppDeploymentRequest, ApplicationImage
from domain.sidecar import SidecarFilesStructure, SidecarCommander, SidecarApiConfigBuilder, \
    MessagingConnectionProperties
from domain.sidecar_logs_command_builder import SidecarLogsCommandBuilder
from domain.userdata.common.userdata_builder import UserDataBuilder
from domain.userdata.linux.instance_userdata_linux import InstanceUserDataLinux


class KubernetesDeploymentService:
    def __init__(self,
                 apps_api: AppsV1beta1Api,
                 bash_command_builder: BashCommandBuilder,
                 artifacts_command_builder: ArtifactsCommandBuilder,
                 github_command_builder: GithubCommandBuilder,
                 config: Config,
                 api_hostname: str,
                 space_id: str,
                 queue_name: str,
                 queue_expires,
                 queue_url_parts: str,
                 logger: Logger
                 ):
        self._logger = logger
        self.github_command_builder = github_command_builder
        self.api_hostname = api_hostname
        self.config = config
        self.artifacts_command_builder = artifacts_command_builder
        self.bash_command_builder = bash_command_builder
        self.apps_api = apps_api
        self.space_id = space_id
        self.queue_name = queue_name
        self.expires = queue_expires
        self.queue_url_parts = queue_url_parts

    def create_app(self,
                   namespace,
                   name,
                   labels,
                   app: AppDeploymentRequest,
                   app_request: CreateSandboxAppRequest):
        """

        :param str namespace:
        :param str name:
        :param Dict labels:
        :param app:
        :param app_request:
        :rtype: AppsV1beta1Deployment
        """

        meta = V1ObjectMeta(name=name)

        annotations = {}
        self.set_apps_info([name], annotations)
        self.set_apps_debugging_protocols([app_request], annotations)
        template_meta = V1ObjectMeta(labels=labels, annotations=annotations)

        container = self._prepare_app_container(image=app.image,
                                                compute_spec=app.compute_spec,
                                                name=app.name,
                                                start_command=app.start_command,
                                                start_command_script_name=app.start_command_script_name,
                                                internal_ports=app.internal_ports,
                                                external_ports=app.external_ports,
                                                script_name=app.config_script_name,
                                                healthcheck_script_name=app.health_check_script_name,
                                                namespace=namespace,
                                                inputs=app.inputs,
                                                has_artifacts=app.has_artifacts)

        pod_spec = V1PodSpec(containers=[container])
        app_template = V1PodTemplateSpec(metadata=template_meta, spec=pod_spec)
        app_spec = AppsV1beta1DeploymentSpec(replicas=app.replicas, template=app_template)
        deployment = AppsV1beta1Deployment(metadata=meta, spec=app_spec)

        return Utils.run_and_log_time(func=lambda: self.apps_api.create_namespaced_deployment(namespace=namespace,
                                                                                              body=deployment,
                                                                                              pretty='true'),
                                      logger=self._logger)

    def create_apps_on_single_pod(self, namespace: str,
                                  name: str,
                                  labels: [Dict],
                                  apps: List[AppDeploymentRequest],
                                  app_requests: List[CreateSandboxAppRequest]) -> AppsV1beta1Deployment:

        meta = V1ObjectMeta(name=name)
        annotations = {}
        self.set_apps_info([app.name for app in apps], annotations)
        self.set_apps_debugging_protocols(app_requests, annotations)
        template_meta = V1ObjectMeta(labels=labels, annotations=annotations)

        containers = list()
        for app in apps:
            container = self._prepare_app_container(image=app.image,
                                                    compute_spec=app.compute_spec,
                                                    name=app.name,
                                                    start_command=app.start_command,
                                                    start_command_script_name=app.start_command_script_name,
                                                    internal_ports=app.internal_ports,
                                                    external_ports=app.external_ports,
                                                    script_name=app.config_script_name,
                                                    healthcheck_script_name=app.health_check_script_name,
                                                    namespace=namespace,
                                                    inputs=app.inputs,
                                                    has_artifacts=app.has_artifacts)
            containers.append(container)

        pod_spec = V1PodSpec(containers=containers)
        app_template = V1PodTemplateSpec(metadata=template_meta, spec=pod_spec)
        app_spec = AppsV1beta1DeploymentSpec(replicas=1, template=app_template)
        deployment = AppsV1beta1Deployment(metadata=meta, spec=app_spec)

        return Utils.run_and_log_time(func=lambda: self.apps_api.create_namespaced_deployment(namespace=namespace,
                                                                                              body=deployment,
                                                                                              pretty='true'),
                                      logger=self._logger)

    @staticmethod
    def _get_download_package_command():
        user_data_builder = UserDataBuilder(use_line_separator=False)
        InstanceUserDataLinux.get_update_and_install_download_multioptions(user_data_builder)
        return user_data_builder.get_user_data()

    @staticmethod
    def _get_user_data(name: str, script_name: str, healthcheck_script_name: str, namespace: str,
                       start_command: str, start_command_script_name: str, has_artifacts: bool):

        files_root_folder = KubernetesAppContainerCommandBuilder.get_app_files_path()
        app_folder = KubernetesAppContainerCommandBuilder.get_application_path(name)

        sidecar_hostname = '{sidecar_service}.{namespace}'.format(
            namespace=namespace,
            sidecar_service=DevboxTags.SIDECAR_SERVICE)

        sidecar_api_address = "{HOSTNAME}:{PORT}".format(HOSTNAME=sidecar_hostname, PORT=Const.SIDECAR_API_PORT)

        test_directory_permissions_command = KubernetesAppContainerCommandBuilder.get_test_directory_permissions(
            path="~/")
        create_local_folders_command = KubernetesAppContainerCommandBuilder \
            .get_create_folder_structure_command(path=app_folder)

        get_prerequisites_command = KubernetesDeploymentService._get_download_package_command()

        wait_for_sidecar_ftp_ready_command = SidecarCommander.get_wait_for_ftp(ftp_host_name=sidecar_hostname)

        wait_for_sidecar_api_ready_command = \
            CommonAppInstanceCommandBuilder.get_wait_hello_world_command(
                sidecar_api_address=sidecar_api_address)

        download_artifacts_and_scripts_command = SidecarCommander.get_wget_download_command(
            ftp_host_name=sidecar_hostname,
            source='{ftp_folder}'.format(ftp_folder=name),
            target=files_root_folder)

        artifacts_path_env_var = ''
        if has_artifacts:
            artifacts_path_env_var = KubernetesDeploymentService._construct_artifacts_path_env_var(app_folder)

        run_healthcheck_command = SidecarCommander.get_healthcheck_command(
            api_address=sidecar_api_address,
            app_home_dir=files_root_folder,
            healthcheck_script_name=healthcheck_script_name,
            app_name=name)

        run_cm_script_command = None
        if script_name:
            local_cm_script_path = '{local_path}/{scripts}/{script_name}'.format(
                local_path=app_folder,
                scripts=DevboxTags.DEFAULT_SCRIPTS_FOLDER,
                script_name=script_name)

            run_cm_script_command = \
                KubernetesAppContainerCommandBuilder.get_run_cm_script_command(
                    hostname=namespace,
                    local_cm_script_path=local_cm_script_path,
                    artifacts_path_env_var=artifacts_path_env_var, app_name=name)

        run_cm_start_command = start_command

        if not start_command and start_command_script_name:
            local_cm_start_command_path = '{local_path}/{scripts}/{script_name}'.format(
                local_path=app_folder,
                scripts=DevboxTags.DEFAULT_SCRIPTS_FOLDER,
                script_name=start_command_script_name)
            run_cm_start_command = \
                KubernetesAppContainerCommandBuilder.get_run_cm_script_command(
                    hostname=namespace,
                    local_cm_script_path=local_cm_start_command_path,
                    artifacts_path_env_var=artifacts_path_env_var, app_name=name)

        wait_to_start_configuration_command = \
            CommonAppInstanceCommandBuilder.get_wait_to_start_configuration_command(
                sidecar_api_address=sidecar_api_address,
                app_name=name)

        ftp_url = "ftp://{HOSTNAME}/sandbox/logs".format(HOSTNAME=sidecar_hostname)

        download_cli_script_command = \
            CommonAppInstanceCommandBuilder.get_cli_script_command(sidecar_api=sidecar_api_address, ftp_url=ftp_url, app_name=name)

        args = [test_directory_permissions_command,
                create_local_folders_command,
                get_prerequisites_command,
                wait_for_sidecar_api_ready_command,
                wait_for_sidecar_ftp_ready_command,
                download_artifacts_and_scripts_command,
                download_cli_script_command,
                wait_to_start_configuration_command
                ]

        if run_cm_script_command:
            args.append(run_cm_script_command)
        args.append(run_healthcheck_command)
        if run_cm_start_command:
            args.append(run_cm_start_command)

        return [''.join(args)]

    @staticmethod
    def _construct_artifacts_path_env_var(local_path: str) -> str:
        return 'ARTIFACTS_PATH={local_path}/{artifacts}'.format(
            local_path=local_path,
            artifacts=DevboxTags.DEFAULT_ARTIFACTS_FOLDER)

    @staticmethod
    def _prepare_app_container(image: ApplicationImage,
                               compute_spec: CreateSandboxAppComputeSpec,
                               name: str,
                               internal_ports: List[int],
                               external_ports: List[int],
                               script_name: str,
                               start_command_script_name: str,
                               healthcheck_script_name: str,
                               start_command: str,
                               namespace: str,
                               inputs: List[CreateSandboxAppInputParameter],
                               has_artifacts: bool) -> V1Container:

        container_ports = list()
        for port in internal_ports:
            container_ports.append(V1ContainerPort(name='{}{}'.format(DevboxTags.INTERNAL_PORT_PREFIX, port),
                                                   container_port=port))

        for port in external_ports:
            container_ports.append(V1ContainerPort(name='{}{}'.format(DevboxTags.EXTERNAL_PORT_PREFIX, port),
                                                   container_port=port))

        env_list = [V1EnvVar(name=i.name, value=i.value) for i in inputs] if inputs else []
        env_list.append(V1EnvVar(name="SANDBOX_ID", value=namespace))

        user_data_str = KubernetesDeploymentService._get_user_data(
            name=name,
            start_command=start_command,
            script_name=script_name,
            healthcheck_script_name=healthcheck_script_name,
            namespace=namespace,
            start_command_script_name=start_command_script_name,
            has_artifacts=has_artifacts)

        command = ['/bin/bash', '-c']

        if image.tag == 'latest' or image.tag == '':
            full_image_name = image.name
        else:
            full_image_name = "{name}:{tag}".format(name=image.name, tag=image.tag)

        if compute_spec and compute_spec.k8s:
            resources = {
                "requests": {
                    "cpu": compute_spec.k8s.requests.cpu,
                    "memory": compute_spec.k8s.requests.ram
                },
                "limits": {
                    "cpu": compute_spec.k8s.limits.cpu,
                    "memory": compute_spec.k8s.limits.ram
                }
            }

            return V1Container(name=name,
                               image=full_image_name,
                               resources=resources,
                               command=command,
                               args=user_data_str,
                               ports=container_ports,
                               env=env_list)
        else:
            return V1Container(name=name,
                               image=full_image_name,
                               command=command,
                               args=user_data_str,
                               ports=container_ports,
                               env=env_list)

    @staticmethod
    def set_apps_info(app_names: [], annotations: {}):
        app_name_to_status_map = {app_name: '' for app_name in app_names}
        annotations[DevboxTags.APPS] = KubernetesConverter.format_apps_status_annotation_value(app_name_to_status_map)

    @staticmethod
    def set_apps_debugging_protocols(apps: [CreateSandboxAppRequest], annotations: {}):
        debugging_protocols = list(set([p for a in apps for p in a.debugging_protocols]))
        annotations[DevboxTags.DEBUGGING_PROTOCOLS] = KubernetesConverter.format_annotation_value(debugging_protocols)

