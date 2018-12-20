from logging import Logger

from domain.services.deployment import KubernetesDeploymentService
from model.clients import KubernetesClients
from model.deployed_app import DeployedAppResource


class PowerOperation(object):

    def __init__(self, deployment_service):
        """
        :param KubernetesDeploymentService deployment_service:
        """
        self.deployment_service = deployment_service

    def power_on(self, logger, clients, deployed_app):
        """
        :param Logger logger:
        :param KubernetesClients clients:
        :param DeployedAppResource deployed_app:
        :return:
        """
        deployment = self.deployment_service.get_deployment_by_name(clients,
                                                                    deployed_app.namespace,
                                                                    deployed_app.kubernetes_name)

        # set the replicas count to the original number in order to "power on" the app
        deployment.spec.replicas = deployed_app.replicas

        self.deployment_service.update_deployment(logger=logger,
                                                  clients=clients,
                                                  namespace=deployed_app.namespace,
                                                  app_name=deployed_app.kubernetes_name,
                                                  updated_deployment=deployment)

        logger.info("Replicas number set to {} for app {}".format(str(deployed_app.replicas),
                                                                  deployed_app.cloudshell_resource_name))

        if deployed_app.wait_for_replicas_to_be_ready > 0:
            logger.info("Waiting for all replicas of app {} to be ready. Timeout set to: {}"
                        .format(deployed_app.cloudshell_resource_name, str(deployed_app.wait_for_replicas_to_be_ready)))
            self.deployment_service.wait_until_all_replicas_ready(
                logger=logger,
                clients=clients,
                namespace=deployed_app.namespace,
                app_name=deployed_app.kubernetes_name,
                deployed_app_name=deployed_app.cloudshell_resource_name,
                timeout=deployed_app.wait_for_replicas_to_be_ready)

        logger.info("App {} powered on.".format(deployed_app.cloudshell_resource_name))

    def power_off(self, logger, clients, deployed_app):
        """
        :param Logger logger:
        :param KubernetesClients clients:
        :param DeployedAppResource deployed_app:
        :return:
        """
        deployment = self.deployment_service.get_deployment_by_name(clients,
                                                                    deployed_app.namespace,
                                                                    deployed_app.kubernetes_name)

        # set the replicas count to 0 in order to "power off" the app
        deployment.spec.replicas = 0

        self.deployment_service.update_deployment(logger=logger,
                                                  clients=clients,
                                                  namespace=deployed_app.namespace,
                                                  app_name=deployed_app.kubernetes_name,
                                                  updated_deployment=deployment)

        logger.info("App {}({}) powered off. Replicas count set to 0".format(deployed_app.cloudshell_resource_name,
                                                                             deployed_app.kubernetes_name))
