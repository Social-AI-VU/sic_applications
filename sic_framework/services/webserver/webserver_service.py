import threading
from sic_framework import SICComponentManager, SICService
from sic_framework.core.actuator_python2 import SICActuator
from sic_framework.core.message_python2 import SICConfMessage, SICMessage, SICRequest

import os  
from flask import Flask, render_template, render_template_string
import threading


class GetWebText(SICMessage):
    def __init__(self, text):
        self.text = text



class WebserverConf(SICConfMessage):
    def __init__(self, host, port):
        """
        :param host         the hostname that a server listens on
        :param port         the port to listen on 
        """
        SICConfMessage.__init__(self)

        self.host = host
        self.port = port

class WebserverService(SICService):

    def __init__(self, *args, **kwargs):

        super(WebserverService, self).__init__(*args, **kwargs)
        # self.input_text = "Initial text"
        #FIXME this getcwd depends on where the program is executed so it's not flexible. 
        template_dir = os.path.join(os.path.abspath(os.getcwd()), "webserver/templates")
        
        # create the web app
        self.app = Flask(__name__, template_folder=template_dir)
        thread = threading.Thread(target=self.start_web_app)
        # app should be terminated automatically when the main thread exits
        thread.daemon = True
        thread.start()
     
    def start_web_app(self):
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


    def render_template_string_routes(self):
        # render a html with bootstrap and a css file
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

        


if __name__ == '__main__':
    SICComponentManager([WebserverService], "web")
