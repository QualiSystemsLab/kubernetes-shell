from cloudshell.shell.core.driver_context import ResourceCommandContext, AutoLoadDetails, AutoLoadAttribute, \
    AutoLoadResource
from collections import defaultdict


class LegacyUtils(object):
    def __init__(self):
        self._datamodel_clss_dict = self.__generate_datamodel_classes_dict()

    def migrate_autoload_details(self, autoload_details, context):
        model_name = context.resource.model
        root_name = context.resource.name
        root = self.__create_resource_from_datamodel(model_name, root_name)
        attributes = self.__create_attributes_dict(autoload_details.attributes)
        self.__attach_attributes_to_resource(attributes, '', root)
        self.__build_sub_resoruces_hierarchy(root, autoload_details.resources, attributes)
        return root

    def __create_resource_from_datamodel(self, model_name, res_name):
        return self._datamodel_clss_dict[model_name](res_name)

    def __create_attributes_dict(self, attributes_lst):
        d = defaultdict(list)
        for attribute in attributes_lst:
            d[attribute.relative_address].append(attribute)
        return d

    def __build_sub_resoruces_hierarchy(self, root, sub_resources, attributes):
        d = defaultdict(list)
        for resource in sub_resources:
            splitted = resource.relative_address.split('/')
            parent = '' if len(splitted) == 1 else resource.relative_address.rsplit('/', 1)[0]
            rank = len(splitted)
            d[rank].append((parent, resource))

        self.__set_models_hierarchy_recursively(d, 1, root, '', attributes)

    def __set_models_hierarchy_recursively(self, dict, rank, manipulated_resource, resource_relative_addr, attributes):
        if rank not in dict: # validate if key exists
            pass

        for (parent, resource) in dict[rank]:
            if parent == resource_relative_addr:
                sub_resource = self.__create_resource_from_datamodel(
                    resource.model.replace(' ', ''),
                    resource.name)
                self.__attach_attributes_to_resource(attributes, resource.relative_address, sub_resource)
                manipulated_resource.add_sub_resource(
                    self.__slice_parent_from_relative_path(parent, resource.relative_address), sub_resource)
                self.__set_models_hierarchy_recursively(
                    dict,
                    rank + 1,
                    sub_resource,
                    resource.relative_address,
                    attributes)

    def __attach_attributes_to_resource(self, attributes, curr_relative_addr, resource):
        for attribute in attributes[curr_relative_addr]:
            setattr(resource, attribute.attribute_name.lower().replace(' ', '_'), attribute.attribute_value)
        del attributes[curr_relative_addr]

    def __slice_parent_from_relative_path(self, parent, relative_addr):
        if parent is '':
            return relative_addr
        return relative_addr[len(parent) + 1:] # + 1 because we want to remove the seperator also

    def __generate_datamodel_classes_dict(self):
        return dict(self.__collect_generated_classes())

    def __collect_generated_classes(self):
        import sys, inspect
        return inspect.getmembers(sys.modules[__name__], inspect.isclass)


class Kubernetes(object):
    def __init__(self, name):
        """
        
        """
        self.attributes = {}
        self.resources = {}
        self._cloudshell_model_name = 'Kubernetes'
        self._name = name

    def add_sub_resource(self, relative_path, sub_resource):
        self.resources[relative_path] = sub_resource

    @classmethod
    def create_from_context(cls, context):
        """
        Creates an instance of NXOS by given context
        :param context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :return:
        :rtype Kubernetes
        """
        result = Kubernetes(name=context.resource.name)
        for attr in context.resource.attributes:
            result.attributes[attr] = context.resource.attributes[attr]
        return result

    def create_autoload_details(self, relative_path=''):
        """
        :param relative_path:
        :type relative_path: str
        :return
        """
        resources = [AutoLoadResource(model=self.resources[r].cloudshell_model_name,
            name=self.resources[r].name,
            relative_address=self._get_relative_path(r, relative_path))
            for r in self.resources]
        attributes = [AutoLoadAttribute(relative_path, a, self.attributes[a]) for a in self.attributes]
        autoload_details = AutoLoadDetails(resources, attributes)
        for r in self.resources:
            curr_path = relative_path + '/' + r if relative_path else r
            curr_auto_load_details = self.resources[r].create_autoload_details(curr_path)
            autoload_details = self._merge_autoload_details(autoload_details, curr_auto_load_details)
        return autoload_details

    def _get_relative_path(self, child_path, parent_path):
        """
        Combines relative path
        :param child_path: Path of a model within it parent model, i.e 1
        :type child_path: str
        :param parent_path: Full path of parent model, i.e 1/1. Might be empty for root model
        :type parent_path: str
        :return: Combined path
        :rtype str
        """
        return parent_path + '/' + child_path if parent_path else child_path

    @staticmethod
    def _merge_autoload_details(autoload_details1, autoload_details2):
        """
        Merges two instances of AutoLoadDetails into the first one
        :param autoload_details1:
        :type autoload_details1: AutoLoadDetails
        :param autoload_details2:
        :type autoload_details2: AutoLoadDetails
        :return:
        :rtype AutoLoadDetails
        """
        for attribute in autoload_details2.attributes:
            autoload_details1.attributes.append(attribute)
        for resource in autoload_details2.resources:
            autoload_details1.resources.append(resource)
        return autoload_details1

    @property
    def cloudshell_model_name(self):
        """
        Returns the name of the Cloudshell model
        :return:
        """
        return 'Kubernetes'

    @property
    def config_file_path(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Config File Path'] if 'Kubernetes.Config File Path' in self.attributes else None

    @config_file_path.setter
    def config_file_path(self, value):
        """
        Path to a standalone kubernetes config file containing all the relevant information for authentication. To get a portable config file run command 'kubectl config view --flatten'
        :type value: str
        """
        self.attributes['Kubernetes.Config File Path'] = value

    @property
    def external_service_type(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.External Service Type'] if 'Kubernetes.External Service Type' in self.attributes else None

    @external_service_type.setter
    def external_service_type(self, value='LoadBalancer'):
        """
        The service type the shell will create for external services. LoadBalander type should be used when the Kuberentes cluster is hosted on a supported public cloud provider like GCP, AWS or Azure. Use NodePort when the cluster is self hosted.
        :type value: str
        """
        self.attributes['Kubernetes.External Service Type'] = value

    @property
    def networking_type(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Networking type'] if 'Kubernetes.Networking type' in self.attributes else None

    @networking_type.setter
    def networking_type(self, value):
        """
        networking type that the cloud provider implements- L2 networking (VLANs) or L3 (Subnets)
        :type value: str
        """
        self.attributes['Kubernetes.Networking type'] = value

    @property
    def region(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Region'] if 'Kubernetes.Region' in self.attributes else None

    @region.setter
    def region(self, value=''):
        """
        The public cloud region to be used by this cloud provider.
        :type value: str
        """
        self.attributes['Kubernetes.Region'] = value

    @property
    def networks_in_use(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Networks in use'] if 'Kubernetes.Networks in use' in self.attributes else None

    @networks_in_use.setter
    def networks_in_use(self, value=''):
        """
        Reserved network ranges to be excluded when allocated sandbox networks (for cloud providers with L3 networking). The syntax is a comma separated CIDR list. For example "10.0.0.0/24, 10.1.0.0/26"
        :type value: str
        """
        self.attributes['Kubernetes.Networks in use'] = value

    @property
    def vlan_type(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.VLAN Type'] if 'Kubernetes.VLAN Type' in self.attributes else None

    @vlan_type.setter
    def vlan_type(self, value='VLAN'):
        """
        whether to use VLAN or VXLAN (for cloud providers with L2 networking)
        :type value: str
        """
        self.attributes['Kubernetes.VLAN Type'] = value

    @property
    def name(self):
        """
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        
        :type value: str
        """
        self._name = value

    @property
    def cloudshell_model_name(self):
        """
        :rtype: str
        """
        return self._cloudshell_model_name

    @cloudshell_model_name.setter
    def cloudshell_model_name(self, value):
        """
        
        :type value: str
        """
        self._cloudshell_model_name = value


class KubernetesService(object):
    def __init__(self, name):
        """
        
        """
        self.attributes = {}
        self.resources = {}
        self._cloudshell_model_name = 'Kubernetes.Kubernetes Service'
        self._name = name

    def add_sub_resource(self, relative_path, sub_resource):
        self.resources[relative_path] = sub_resource

    @classmethod
    def create_from_context(cls, context):
        """
        Creates an instance of NXOS by given context
        :param context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :type context: cloudshell.shell.core.driver_context.ResourceCommandContext
        :return:
        :rtype Kubernetes Service
        """
        result = KubernetesService(name=context.resource.name)
        for attr in context.resource.attributes:
            result.attributes[attr] = context.resource.attributes[attr]
        return result

    def create_autoload_details(self, relative_path=''):
        """
        :param relative_path:
        :type relative_path: str
        :return
        """
        resources = [AutoLoadResource(model=self.resources[r].cloudshell_model_name,
            name=self.resources[r].name,
            relative_address=self._get_relative_path(r, relative_path))
            for r in self.resources]
        attributes = [AutoLoadAttribute(relative_path, a, self.attributes[a]) for a in self.attributes]
        autoload_details = AutoLoadDetails(resources, attributes)
        for r in self.resources:
            curr_path = relative_path + '/' + r if relative_path else r
            curr_auto_load_details = self.resources[r].create_autoload_details(curr_path)
            autoload_details = self._merge_autoload_details(autoload_details, curr_auto_load_details)
        return autoload_details

    def _get_relative_path(self, child_path, parent_path):
        """
        Combines relative path
        :param child_path: Path of a model within it parent model, i.e 1
        :type child_path: str
        :param parent_path: Full path of parent model, i.e 1/1. Might be empty for root model
        :type parent_path: str
        :return: Combined path
        :rtype str
        """
        return parent_path + '/' + child_path if parent_path else child_path

    @staticmethod
    def _merge_autoload_details(autoload_details1, autoload_details2):
        """
        Merges two instances of AutoLoadDetails into the first one
        :param autoload_details1:
        :type autoload_details1: AutoLoadDetails
        :param autoload_details2:
        :type autoload_details2: AutoLoadDetails
        :return:
        :rtype AutoLoadDetails
        """
        for attribute in autoload_details2.attributes:
            autoload_details1.attributes.append(attribute)
        for resource in autoload_details2.resources:
            autoload_details1.resources.append(resource)
        return autoload_details1

    @property
    def cloudshell_model_name(self):
        """
        Returns the name of the Cloudshell model
        :return:
        """
        return 'Kubernetes Service'

    @property
    def docker_image_name(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Kubernetes Service.Docker Image Name'] if 'Kubernetes.Kubernetes Service.Docker Image Name' in self.attributes else None

    @docker_image_name.setter
    def docker_image_name(self, value):
        """
        
        :type value: str
        """
        self.attributes['Kubernetes.Kubernetes Service.Docker Image Name'] = value

    @property
    def docker_image_tag(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Kubernetes Service.Docker Image Tag'] if 'Kubernetes.Kubernetes Service.Docker Image Tag' in self.attributes else None

    @docker_image_tag.setter
    def docker_image_tag(self, value):
        """
        
        :type value: str
        """
        self.attributes['Kubernetes.Kubernetes Service.Docker Image Tag'] = value

    @property
    def internal_ports(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Kubernetes Service.Internal Ports'] if 'Kubernetes.Kubernetes Service.Internal Ports' in self.attributes else None

    @internal_ports.setter
    def internal_ports(self, value):
        """
        
        :type value: str
        """
        self.attributes['Kubernetes.Kubernetes Service.Internal Ports'] = value

    @property
    def external_ports(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Kubernetes Service.External Ports'] if 'Kubernetes.Kubernetes Service.External Ports' in self.attributes else None

    @external_ports.setter
    def external_ports(self, value):
        """
        
        :type value: str
        """
        self.attributes['Kubernetes.Kubernetes Service.External Ports'] = value

    @property
    def replicas(self):
        """
        :rtype: float
        """
        return self.attributes['Kubernetes.Kubernetes Service.Replicas'] if 'Kubernetes.Kubernetes Service.Replicas' in self.attributes else None

    @replicas.setter
    def replicas(self, value='1'):
        """
        
        :type value: float
        """
        self.attributes['Kubernetes.Kubernetes Service.Replicas'] = value

    @property
    def start_command(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Kubernetes Service.Start Command'] if 'Kubernetes.Kubernetes Service.Start Command' in self.attributes else None

    @start_command.setter
    def start_command(self, value):
        """
        
        :type value: str
        """
        self.attributes['Kubernetes.Kubernetes Service.Start Command'] = value

    @property
    def environment_variables(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Kubernetes Service.Environment Variables'] if 'Kubernetes.Kubernetes Service.Environment Variables' in self.attributes else None

    @environment_variables.setter
    def environment_variables(self, value):
        """
        Comma separated list of 'key=value' environment variables
        :type value: str
        """
        self.attributes['Kubernetes.Kubernetes Service.Environment Variables'] = value

    @property
    def cpu_request(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Kubernetes Service.CPU Request'] if 'Kubernetes.Kubernetes Service.CPU Request' in self.attributes else None

    @cpu_request.setter
    def cpu_request(self, value):
        """
        
        :type value: str
        """
        self.attributes['Kubernetes.Kubernetes Service.CPU Request'] = value

    @property
    def ram_request(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Kubernetes Service.RAM Request'] if 'Kubernetes.Kubernetes Service.RAM Request' in self.attributes else None

    @ram_request.setter
    def ram_request(self, value):
        """
        
        :type value: str
        """
        self.attributes['Kubernetes.Kubernetes Service.RAM Request'] = value

    @property
    def wait_for_replicas(self):
        """
        :rtype: float
        """
        return self.attributes['Kubernetes.Kubernetes Service.Wait for Replicas'] if 'Kubernetes.Kubernetes Service.Wait for Replicas' in self.attributes else None

    @wait_for_replicas.setter
    def wait_for_replicas(self, value='120'):
        """
        Wait X number of seconds during power on for all replicas to be in ready state. When the value is zero or less the shell will not wait for replicas to be ready.
        :type value: float
        """
        self.attributes['Kubernetes.Kubernetes Service.Wait for Replicas'] = value

    @property
    def cpu_limit(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Kubernetes Service.CPU Limit'] if 'Kubernetes.Kubernetes Service.CPU Limit' in self.attributes else None

    @cpu_limit.setter
    def cpu_limit(self, value):
        """
        
        :type value: str
        """
        self.attributes['Kubernetes.Kubernetes Service.CPU Limit'] = value

    @property
    def ram_limit(self):
        """
        :rtype: str
        """
        return self.attributes['Kubernetes.Kubernetes Service.RAM Limit'] if 'Kubernetes.Kubernetes Service.RAM Limit' in self.attributes else None

    @ram_limit.setter
    def ram_limit(self, value):
        """
        
        :type value: str
        """
        self.attributes['Kubernetes.Kubernetes Service.RAM Limit'] = value

    @property
    def wait_for_ip(self):
        """
        :rtype: bool
        """
        return self.attributes['Kubernetes.Kubernetes Service.Wait for IP'] if 'Kubernetes.Kubernetes Service.Wait for IP' in self.attributes else None

    @wait_for_ip.setter
    def wait_for_ip(self, value=False):
        """
        if set to false the deployment will not wait for the VM to get an IP address
        :type value: bool
        """
        self.attributes['Kubernetes.Kubernetes Service.Wait for IP'] = value

    @property
    def autoload(self):
        """
        :rtype: bool
        """
        return self.attributes['Kubernetes.Kubernetes Service.Autoload'] if 'Kubernetes.Kubernetes Service.Autoload' in self.attributes else None

    @autoload.setter
    def autoload(self, value=True):
        """
        Whether to call the autoload command during Sandbox setup
        :type value: bool
        """
        self.attributes['Kubernetes.Kubernetes Service.Autoload'] = value

    @property
    def name(self):
        """
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        
        :type value: str
        """
        self._name = value

    @property
    def cloudshell_model_name(self):
        """
        :rtype: str
        """
        return self._cloudshell_model_name

    @cloudshell_model_name.setter
    def cloudshell_model_name(self, value):
        """
        
        :type value: str
        """
        self._cloudshell_model_name = value



