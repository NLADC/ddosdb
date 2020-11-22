import os
from django.apps import AppConfig


class DdosdbConfig(AppConfig):
    name = 'ddosdb'

    def ready(self):
        # importing model classes
        # from .models import MyModel  # or...
        # MyModel = self.get_model('MyModel')
        # print("DdosdbConfig.ready() called")
        # if os.environ.get('RUN_MAIN', None) != 'true':

        # registering signals with the model's string label
        # pre_save.connect(receiver, sender='app_label.MyModel')
