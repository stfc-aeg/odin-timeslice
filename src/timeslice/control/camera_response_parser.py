import logging

class CameraResponseParser(object):

    def __init__(self, camera_controller):

        self.camera_controller = camera_controller

        # Define dictionary of legal responses and assoicated methods
        self.responses = { 'PING_ACK'       : self.ping_ack_response,
                           'VERSION_ACK'    : self.version_ack_response,
                           'CAPTURE_ACK'    : self.capture_ack_response,
                           'CAPTURE_NACK'   : self.capture_nack_response,
                           'RETRIEVE_ACK'   : self.retrieve_ack_response,
                           'RETRIEVE_NACK'  : self.retrieve_nack_response,
                           'PREVIEW_ACK'    : self.preview_ack_response,
                           'PREVIEW_NACK'   : self.preview_nack_response,
                           'CONFIGURE_ACK'  : self.configure_ack_response,
                           'CONFIGURE_NACK' : self.configure_nack_response,
                        }

    def parse_response(self, response_data):

        response_ok = True

        # If response has raw_data parameter at end, remove it and capture in raw_data
        raw_data=None
        raw_data_key='raw_data='

        if isinstance(response_data, bytes):
            raw_data_key = raw_data_key.encode('utf-8')

        raw_data_idx = response_data.find(raw_data_key)
        if raw_data_idx > 0:
            raw_data = response_data[raw_data_idx+len(raw_data_key):]
            response_data=response_data[:raw_data_idx]

        if isinstance(response_data, bytes):
            response_data = response_data.decode('utf-8')

        # Split response into space separated list
        response_words = response_data.split()

        # Decode response from first word and test if it is a legal response
        response = response_words[0].upper()
        if response in self.responses:

            # If so, split remaining words into key-value pairs separated by '=''
            try:
                args = dict(item.split("=") for item in response_words[1:])

                if 'id' in args:
                    try:
                        # Decode the id parameter
                        id = int(args['id'])
                        response_ok = self.responses[response](id, args, raw_data)

                    except ValueError:
                        response_ok = False
                        logging.error("Non-integer ID parameter specified on response: {}".format(args['id']))
                else:
                    response_ok = False
                    logging.error("No ID parameter present in command")

            except ValueError:
                response_ok = False
                logging.error("Illegal parameter format: {}".format(response_data))

        else:
            response_ok = False
            logging.error("Unrecognised response : {}".format(response))

        return response_ok

    def ping_ack_response(self, id, args, raw_data):

        logging.debug("Got ping response from camera {}, args={}".format(id, args))
        self.camera_controller.update_camera_last_ping_time(id)

    def version_ack_response(self, id, args, raw_data):

        logging.debug("Got version response from camera {}, args={}".format(id, args))

        if 'commit' in args:
            commit = args['commit']
        else:
            commit = 'unknown'

        if 'time' in args:
            time = args['time']
        else:
            time = '0'

        self.camera_controller.update_camera_version_info(id, commit, time)

    def capture_ack_response(self, id, args, raw_data):

        logging.debug("Got capture acknowledge from camera {}, args={}".format(id, args))
        # self.camera_controller.update_camera_capture_state(id, True)

    def capture_nack_response(self, id, args, raw_data):

        logging.error("Got capture no-acknowledge for camera {}, args={}".format(id, args))
        # self.camera_controller.update_camera_capture_state(id, False)

    def retrieve_ack_response(self, id, args, raw_data):

        image_len = len(raw_data)

        if image_len:
            logging.debug("Got retrieve acknowledge from camera {}, image length={}".format(id,image_len))
        else:
            logging.error("Got retrieve acknowledge from camera {} but with no image data".format(id))

        # self.camera_controller.update_camera_retrieve_state(id, True, raw_data)

    def retrieve_nack_response(self, id, args, raw_data):

        logging.error("Got retrieve no-acknowledge for camera {}, args={}".format(id, args))
        # self.camera_controller.update_camera_retrieve_state(id, False, None)

    def preview_ack_response(self, id, args, raw_data):

        image_len = len(raw_data)

        if image_len:
            logging.debug("Got preview acknowledge from camera {}, image length={}".format(id,image_len))
            self.camera_controller.update_preview_image(id, raw_data)
        else:
            logging.error("Got preview acknowledge from camera {} but with no image data".format(id))


    def preview_nack_response(self, id, args, raw_data):

        logging.error("Got preview no-acknowledge for camera {}, args={}".format(id, args))

    def configure_ack_response(self, id, args, raw_data):

        logging.debug("Got configure acknowledge from camera {}, args={}".format(id, args))
        # self.camera_controller.update_camera_configure_state(id, True)

    def configure_nack_response(self, id, args, raw_data):

        logging.debug("Got configure no-acknowledge from camera {}, args={}".format(id, args))
        # self.camera_controller.update_camera_configure_state(id, False)
