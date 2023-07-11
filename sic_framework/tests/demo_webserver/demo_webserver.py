import io
import logging
import time

import numpy as np

from sic_framework.core.connector import SICApplication, SICActuator
from sic_framework.services.webserver.webserver_service import WebserverService, WebserverConf, GetWebText
from sic_framework.services.dialogflow.dialogflow import DialogflowComponent, DialogflowConf, GetIntentRequest, RecognitionResult, QueryResult
# from sic_framework.devices.desktop import Desktop

from sic_framework.devices.nao import Nao
from sic_framework.devices.common_naoqi.pepper_tablet import NaoqiTabletService, NaoqiLoadUrl


class DemoWebServer(SICApplication):

    # # example for rendering a dialogflow transcript to a web browser
    # def run(self) -> None:

    #     """
    #     Send a dialogflow transcript to a web browser
    #     """
    #     desktop = Desktop(device_id='desktop', application=self)
    #     web_conf = WebserverConf(host="0.0.0.0", port=8080)
    #     # web_conf = WebserverConf(websocket_host="localhost", websocket_port=8080)

    #     dialog_conf = DialogflowConf(sample_rate_hertz=44100, project_id='test-hync')

    #     dialogflow = self.connect(DialogflowService, device_id='local', inputs_to_service=[desktop.mic],
    #                               log_level=logging.INFO, conf=dialog_conf)
    #     dialogflow.register_callback(self.on_dialog)
    #     self.webserver_connector = self.connect(WebserverService, device_id='web', inputs_to_service=[self.this], log_level=logging.INFO, conf=web_conf)
    #     # text = self.get_text('Hello, world!')
    #     # button = self.get_button('Done')
    #     # html = self.get_header() + self.get_body(text + button) + self.get_footer()

    #     print(" -- Ready -- ")
    #     x = np.random.randint(10000)
    #     for i in range(10):
    #         print(" ----- Conversation turn", i)
    #         reply = dialogflow.request(GetIntentRequest(x))


    # def on_dialog(self, message):

    #     if message.response:
    #         self.webserver_connector.send_message(ImageMessage(message.response.recognition_result.transcript))
    #         print("Transcript:", message.response.recognition_result.transcript)

    def run(self) -> None:
        """
        Render an HTML file with Bootstrap and a CSS file to a web browser
        """     
        web_conf = WebserverConf(host="0.0.0.0", port=8080)
        self.webserver_connector = self.start_service(WebserverService, device_id='web', inputs_to_service=[self], log_level=logging.INFO, conf=web_conf)
        self.pepper_tablet_connector = self.start_service(NaoqiTabletService, device_id='marvin_tab', inputs_to_service=[self])
        # the HTML file (a sign-in page with VU logo) to be rendered
        html_file = "sign_in.html"
        web_url = "http://10.15.3.224:8080/"

        # send html to WebserverService
        with open(html_file) as file:
            data = file.read()
            self.webserver_connector.send_message(GetWebText(data))

        # send url to NaoqiTabletService in order to display it on a pepper's tablet
        self.pepper_tablet_connector.send_message(NaoqiLoadUrl(web_url))


    # TODO texts that should be input for a webserver
    @staticmethod
    def get_header() -> str:
        """
        A header (navbar) with a listening icon on the left and a VU logo on the right.
        """
        return '<nav class="navbar mb-5">' \
               '<div class="navbar-brand listening_icon"></div>' \
               '<div class="navbar-nav vu_logo"></div>' \
               '</nav>'

    @staticmethod
    def get_body(contents: str) -> str:
        """
        The given contents in a centered container.
        """
        return '<main class="container text-center">' + contents + '</main>'

    @staticmethod
    def get_footer() -> str:
        """
        A footer that shows the currently recognized spoken text (if any).
        """
        return '<footer class="fixed-bottom">' \
               '<p class="lead bg-light text-center speech_text"></p>' \
               '</footer>'

    @staticmethod
    def get_text(txt: str) -> str:
        """
        A simple text display.
        """
        return '<h1>' + txt + '</h1>'

    @staticmethod
    def get_button(label: str) -> str:
        """
        A clickable button.
        """
        return '<button class="btn btn-primary btn-lg mt-5 ml-3">' + label + '</button>'


if __name__ == '__main__':
    test_app = DemoWebServer()

    test_app.run()
