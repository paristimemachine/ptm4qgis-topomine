# -*- coding: utf-8 -*-

from qgis.core import QgsProcessingAlgorithm
from qgis.PyQt.QtCore import QCoreApplication

# from processing.algs.help import shortHelp


class PTM4QgisAlgorithm(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()

    def shortHelpString(self):
        # TODO TO IMPROVE
        # return shortHelp.get(self.id(), None)
        return self.help()

    def tr(self, string, context=""):
        if context == "":
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)

    def trAlgorithm(self, string, context=""):
        if context == "":
            context = self.__class__.__name__
        return string, QCoreApplication.translate(context, string)

    def createInstance(self):
        return type(self)()
