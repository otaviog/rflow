"""
Common shell workflow interfaces.
"""

import os
import string
import shutil
from urllib.parse import urlparse

import requests
from tqdm import tqdm

from .common import Uninit
from .node import Node
from .interface import Interface
from .resource import FSResource, NilResource

from ._argument import ArgNamespace

# pylint: disable=unused-argument,no-self-use


class Shell(Interface):
    """Interface for calling shell commands:

    Attributes:

        resource (:obj:`shaperetrieval.workflow.FSResource`): Generate
         resource. None if no resource are generated.

        args.commands (List[str]): List of commands.

    """

    def __init__(self, commands=Uninit, resource=NilResource()):
        super(Shell, self).__init__()
        self.args.commands = commands
        self.resource = resource

    def evaluate(self, resource, commands):
        """
        Run the command
        """

        exit_code = 0
        for command in commands:
            exit_code = os.system(command)
            if exit_code != 0:
                self.fail(
                    'Error while executing comand: {}'.format(command))

        return exit_code

    def load(self):
        """
        Always returns none. Kept to avoid rerun evaluate.
        """
        return None


class Download(Interface):
    """Inferface for downloading a file.

    Attributes:

        args.url (str): The URL to download the file.

        resource (:obj:`shaperetrieval.workflow.FSResource`): The
         generated file by the download. Required.

    """

    def __init__(self, url=Uninit,
                 resource=None):
        super(Download, self).__init__()
        self.args.url = url
        if url is not Uninit:
            self.resource = FSResource(os.path.basename(
                urlparse(url).path))
        else:
            self.resource = resource

    def evaluate(self, url, resource):
        """
        Executes the file download.
        """

        try:
            output_dir = os.path.dirname(
                os.path.abspath(resource.filepath))

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            response = requests.get(url, stream=True)
            file_size = int(response.headers['Content-Length'])

            temp_filepath = resource.filepath + '.temp'
            with open(temp_filepath, 'wb') as local_stream:
                prog_bar = tqdm(total=file_size)
                for data in response.iter_content():
                    local_stream.write(data)
                    prog_bar.update(len(data))
            shutil.move(temp_filepath, resource.filepath)
            return resource.filepath
        except requests.exceptions.RequestException as error:
            self.fail(error)

    def load(self, resource):
        """
        Returns the resource's filepath. Kept to avoid re-evaluation.
        """

        return resource.filepath


class TemplateFile(Node):
    """
    """

    def evaluate(self, resource, template_resource, *template_value):
        subs = dict(zip(self.template_vars, template_value))
        with open(str(template_resource), 'r') as text_file:
            input_string = text_file.read()

        str_template = string.Template(input_string)
        with open(resource.filepath, 'w') as text_file:
            text_file.write(str_template.substitute(subs))
            text_file.flush()
        return resource.filepath

    def load(self, resource):
        return resource.filepath

    def __init__(self, template_vars):
        self.template_vars = template_vars
        args = ArgNamespace(
            ['resource', 'template_resource'] + template_vars, {})

        super(TemplateFile, self).__init__(
            None,
            self.__class__.__name__,
            self.evaluate, args, self.load, ['resource'])


class Uncompress(Interface):
    def evaluate(self, resource, in_resource):
        filepart, ext = os.path.splitext(in_resource.filepath)
        ext = ext.lower().strip()
        if ext == '.zip':
            os.system('unzip {}'.format(in_resource.filepath))
        elif ext in ('.gz', '.bz2'):
            filepart, pre_ext = os.path.splitext(filepart)
            pre_ext = pre_ext.lower().strip()
            is_tar = pre_ext == '.tar'
            if ext == '.gz':
                if is_tar:
                    os.system('tar xzvf {}'.format(in_resource.filepath))
                else:
                    os.system('gunzip {}'.format(in_resource.filepath))
            elif ext == '.bz2':
                if is_tar:
                    os.system('tar xjvf {}'.format(in_resource.filepath))
                else:
                    os.system('bunzip2 {}'.format(in_resource.filepath))
        return resource

    def load(self, resource):
        return resource


class ShowMessageIfNotExists(Interface):
    """This node just shows a message if the associated resource doesn't exists.

    Useful to guide users to download datasets from a given address.

    """

    def evaluate(self, resource, message):
        """Args:

            resource (:obj:`shrkit.workflow.Resource`): Which resource
            to check.

            message (str): Message to display when the resource
            doesn't exists.

        Returns:
            :obj:`shrkit.workflow.Resource`: The same given resource.
        """

        if not resource.exists():
            print(message)
            self.fail("Resource {} doesn't exists".format(resource))
        return resource

    def load(self, resource):
        """Returns:
            :obj:`shrkit.workflow.Resource`: The same given resource.
        """
        return resource
