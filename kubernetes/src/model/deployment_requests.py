from typing import List, Dict


class ApplicationImage:
    def __init__(self, name, tag):
        """
        :param str name:
        :param str tag:
        """
        self.tag = tag
        self.name = name


class AppComputeSpecKubernetesResources:
    def __init__(self, cpu, ram):
        """
        :param str cpu:
        :param str ram:
        """
        self.cpu = cpu
        self.ram = ram


class AppComputeSpecKubernetes:
    def __init__(self, requests, limits):
        """
        :param AppComputeSpecKubernetesResources requests:
        :param AppComputeSpecKubernetesResources limits:
        """
        self.limits = limits
        self.requests = requests


class AppDeploymentRequest:
    def __init__(self, name, image, start_command, environment_variables, compute_spec, internal_ports, external_ports,
                 replicas=1):
        """
        :param str start_command:
        :param Dict[str, str] environment_variables:
        :param str name:
        :param ApplicationImage image:
        :param AppComputeSpecKubernetes compute_spec:
        :param List[int] internal_ports:
        :param List[int] external_ports:
        :param int replicas:
        """
        self.environment_variables = environment_variables
        self.start_command = start_command
        self.compute_spec = compute_spec
        self.replicas = replicas
        self.internal_ports = internal_ports
        self.external_ports = external_ports
        self.image = image
        self.name = name
