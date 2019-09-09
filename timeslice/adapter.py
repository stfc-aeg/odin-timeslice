"""Demo adapter for ODIN control Timeslice

This class implements a simple adapter used for demonstration purposes in a

Cat Carrigan, STFC Application Engineering
"""
import logging
import tornado
import time
import os
from os import path
from concurrent import futures
import smtplib
import email
import ssl

from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor
from tornado.escape import json_decode

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin._version import get_versions

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class TimesliceAdapter(ApiAdapter):
    """System info adapter class for the ODIN server.

    This adapter provides ODIN clients with information about the server and the system that it is
    running on.
    """

    def __init__(self, **kwargs):
        """Initialize the TimesliceAdapter object.

        This constructor initializes the TimesliceAdapter object.

        :param kwargs: keyword arguments specifying options
        """
        # Intialise superclass
        super(TimesliceAdapter, self).__init__(**kwargs)

        rendered_files = (self.options.get('rendered_files'))
        self.timeslice = Timeslice (rendered_files)

        logging.debug('TimesliceAdapter loaded')

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        try:
            response = self.timeslice.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400

        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """

        content_type = 'application/json'

        try:
            data = json_decode(request.body)
            self.timeslice.set(path, data)
            response = self.timeslice.get(path)
            status_code = 200
        except TimesliceError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = 'TimesliceAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)


class TimesliceError(Exception):
    """Simple exception class for PSCUData to wrap lower-level exceptions."""

    pass


class Timeslice():
    """Timeslice - class that extracts and stores information about system-level parameters."""

    # Thread executor used for background tasks
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self, rendered_files):
        """Initialise the Timeslice object.

        This constructor initlialises the Timeslice object, building a parameter tree and
        launching a background task if enabled
        """
        self.rendered_files = rendered_files
        self.access_codes = []
        self.files = []
        self.email_address = ""

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        # Store all information in a parameter tree
        self.param_tree = ParameterTree({
            'odin_version': version_info['version'],
            'tornado_version': tornado.version,
            'server_uptime': (self.get_server_uptime, None),
            'access_codes': (lambda: self.access_codes, None),
            'add_access_code': ("", self.add_task_access_code),
            'rendered_files': (lambda: self.rendered_files,None),
            'clear_access_codes' : (False, self.clear_access_codes),
            'clear_email' : (False, self.clear_email),
            'email_address' : (lambda: self.email_address, None),
            'add_email_address' : ("", self.add_email_address),
            'send_email_new' : (False, self.send_email_new),
            'files': (lambda: self.files, None),

        })     


    def get_server_uptime(self):
        """Get the uptime for the ODIN server.

        This method returns the current uptime for the ODIN server.
        """
        return time.time() - self.init_time

    def get(self, path):
        """Get the parameter tree.

        This method returns the parameter tree for use by clients via the Timeslice adapter.

        :param path: path to retrieve from tree
        """
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree.

        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate TimesliceError.

        :param path: path of parameter tree to set values for
        :param data: dictionary of new data values to set in the parameter tree
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise TimesliceError(e)

    def add_task_access_code(self, access_code):
        """Validate and store entered access codes to be sent in an email

        When an access code is entered, first the code checks that the entered access code 
        isn't already in the access codes list in order to avoid duplication of attachments
        in the email.
        If the code isn't a duplicate the system then checks that it relates to an existing
        file. If the file exists then the code is added to the list of access codes being stored
        and the files list recieves both the access code and the file path in order to attach 
        the mp4 file to the email.
        Otherwise the system sends out an error message
        """

        if access_code in self.access_codes: 
            raise TimesliceError("This code is already stored")
        
        file_path = os.path.join(self.rendered_files, access_code + '.mp4')
        logging.debug("Testing if file {} exists".format(file_path))
        if os.path.isfile(os.path.join(file_path)):
            logging.debug("adding access code %s", access_code)

            self.access_codes.append(access_code)
            self.files.append(file_path)
            logging.debug(self.access_codes)
            logging.debug(self.files)
        else:
            raise TimesliceError("This access code does not match any stored videos, please try again")
    
    
    def clear_access_codes(self, clear):
        """ This empties both the access codes list and the files list used for attaching mp4
        files.
        """
        logging.debug("Setting list clear to %s", clear)

        self.access_codes = []
        self.files = []

        logging.debug(self.access_codes)

    def clear_email(self, clear):
        """ This empties the stored email address when the page loads"""
        self.email_address = None
        logging.debug("clearing email: %s",clear)

    
    def add_email_address(self, email_address):
        """This sets the email address for videos to be sent to
        """
        self.email_address = email_address

        logging.debug("Email address recieved: %s", email_address)

    
    def send_email_new(self, send):
        """This is the code that actually collects the various pieces of entered information
        and uses them to send an email out to the timeslice user
        """
        subject = "Timeslice videos"
        body = """To: <{0}>
Subject: SMTP test

Hello,

Here are the access codes you entered during your visit:
{1}

Their corresponding timeslice videos are attached to this email.

Please enjoy,
STFC
""".format(self.email_address, self.access_codes)
        sender_email = "Catherine Carrigan <catherine.carrigan@stfc.ac.uk>"
        receiver_email = '{0}'.format(self.email_address)

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))
        files_list = self.access_codes
        logging.debug(files_list)
        
        for a_file in files_list:
            a_file = os.path.join(self.rendered_files, a_file + '.mp4')
            attachment = open(a_file, "rb")
            filename = os.path.basename(a_file)
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )

            message.attach(part)

        try:
            smtp_obj = smtplib.SMTP('outbox.rl.ac.uk')
            smtp_obj.sendmail(sender_email, receiver_email, message.as_string())
            logging.debug("Yay, we sent mail")
        except smtplib.SMTPException as error:
            logging.debug("Boo, emailing failed: {}".format(str(error)))
    