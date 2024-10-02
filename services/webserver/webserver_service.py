from sic_framework import SICComponentManager
from sic_framework.core.connector import SICConnector
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.message_python2 import SICConfMessage, SICMessage

import os  
from flask import Flask, render_template, render_template_string
import threading


class WebText(SICMessage):
    def __init__(self, text):
        self.text = text

class WebserverConf(SICConfMessage):
    def __init__(self, host: str, port: int):
        """
        :param host         the hostname that a server listens on
        :param port         the port to listen on 
        """
        super(WebserverConf, self).__init__()
        self.host = host
        self.port = port

class WebserverComponent(SICComponent):

    def __init__(self, *args, **kwargs):

        super(WebserverComponent, self).__init__(*args, **kwargs)
        #FIXME this getcwd depends on where the program is executed so it's not flexible. 
        template_dir = os.path.join(os.path.abspath(os.getcwd()), "webserver/templates")
        
        # create the web app
        self.app = Flask(__name__, template_folder=template_dir)
        thread = threading.Thread(target=self.start_web_app)
        # app should be terminated automatically when the main thread exits
        thread.daemon = True
        thread.start()

    def start_web_app(self):
        """
        start the web server
        """
        self.render_template_string_routes()
        self.app.run(host=self.params.host, port=self.params.port)

    @staticmethod
    def get_conf():
        return WebserverConf()

    @staticmethod
    def get_inputs():
        return [GetWebText]

    @staticmethod
    def get_output():
        return SICMessage
    
    def execute(self, inputs):
        self.input_text = str(inputs.get(GetWebText).text)
        return SICMessage()

    # when the WebText message arrives, feed it to self.input_text
    def on_message(self, message):
        self.input_text = message.text

    def render_template_string_routes(self):
        # render a html with bootstrap and a css file once a client is connected
        @self.app.route("/")
        def index():
            return render_template_string(self.input_text)


    def dialogflow_routes(self):
        # dialogflow example
        # use route decorator to register the routes with Flask
        @self.app.route("/")
        def index():
            return render_template("flask.html", dialogflow=self.input_text)
        
        @self.app.route("/dialogflow")
        def dialogflow():
            dialogflow=self.input_text
            return dialogflow

class Webserver(SICConnector):
    component_class = WebserverComponent


if __name__ == '__main__':
    SICComponentManager([WebserverComponent])
