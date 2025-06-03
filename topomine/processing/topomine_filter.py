import json

import qgis.processing as processing
from qgis.core import (
    QgsJsonUtils,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingMultiStepFeedback,
    QgsProcessingOutputVectorLayer,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterEnum,
    QgsProcessingParameterExtent,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QTextCodec

from topomine.ptm4qgis_algorithm import PTM4QgisAlgorithm

from .topomine_api_client import (
    get_topomine_cassini,
    get_topomine_fantoir_commune,
    get_topomine_fantoir_voie,
    get_topomine_hydronyme,
    get_topomine_odonyme,
    get_topomine_toponyme,
)


class TopomineSearchAlgorithm(PTM4QgisAlgorithm):

    LIMIT = 100000000
    OFFSET = 0

    TOPONYME = "TOPONYME"
    ODONYME = "ODONYME"
    FANTOIR_VOIE = "FANTOIR_VOIE"
    HYDRONYME = "HYDRONYME"
    FANTOIR_COMM = "FANTOIR_COMM"
    CASSINI = "CASSINI"

    SEARCH_METHOD_OPTION = "SEARCH_METHOD_OPTION"
    SEARCH = "SEARCH"
    SQUELETTE = "SQUELETTE"
    REGEX = "REGEX"

    OUTPUT_TOPONYME = "OUTPUT_TOPONYME"
    OUTPUT_ODONYME = "OUTPUT_ODONYME"
    OUTPUT_FANTOIR_VOIE = "OUTPUT_FANTOIR_VOIE"
    OUTPUT_HYDRONYME = "OUTPUT_HYDRONYME"
    OUTPUT_FANTOIR_COMM = "OUTPUT_FANTOIR_COMM"
    OUTPUT_CASSINI = "OUTPUT_CASSINI"

    def help(self):
        return self.tr(
            "Search for toponyms, odonyms, hydronyms, and communes in France from "
            "various databases.\n"
            "Write a search term, select a search option and at least one database "
            "to search from.\n"
            "The search term must be at least one character long.\n"
            "The search method can be either a simple search, a search based on consonants "
            "(squeletisation) or a regular expression search.\n"
            "The results will be displayed in the map canvas as temporary layers.\n"
            "For more information, see the online documentation easily accessible "
            "via the Topomine plugin menu in QGIS."
        )

    # def shortHelpString(self):
    #     return self.tr(
    #         "Recherche de toponymes, odonymes, hydronymes et communes en France à partir "
    #         "de différentes bases de données. Saisissez un terme de recherche, sélectionnez une option de recherche "
    #         "et au moins une base de données à interroger. "
    #         "Le terme de recherche doit comporter au moins un caractère. "
    #         "La méthode de recherche peut être une recherche simple, une recherche basée sur les consonnes "
    #         "(squelettisation) ou une recherche par expression régulière. "
    #         "Les résultats seront affichés dans le canevas cartographique sous forme de couches temporaires. "
    #         "Pour plus d'informations, consultez la documentation en ligne accessible via le menu du plugin Topomine dans QGIS."
    #     )

    def __init__(self):
        super().__init__()
        self.distance_area = None
        self.search_method = [
            self.tr("Simple search"),
            self.tr("Squeletisation (only based on consonants)"),
            self.tr("Regular expresssion"),
        ]

        self.descr_topomyne = self.tr("Toponyms (IGN / BD TOPO)")
        self.descr_odonyme = self.tr("Odonyms (IGN / BD TOPO)")
        self.descr_fantoir_voie = self.tr("Odonyms (FANTOIR)")
        self.descr_hydronyme = self.tr("Hydronyms (SANDRE)")
        self.descr_fantoir_comm = self.tr("Current Communes (FANTOIR)")
        self.descr_cassini = self.tr("Historical Communes (EHESS / Cassini)")

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterString(
                name=self.SEARCH,
                description=self.tr("Search term"),  # Therme de recherche
                defaultValue="",
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.SEARCH_METHOD_OPTION,
                description=self.tr("Search method"),  # Méthode de recherche
                options=self.search_method,
                defaultValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.TOPONYME,
                description=self.descr_topomyne,
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.ODONYME,
                description=self.descr_odonyme,
                defaultValue=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.FANTOIR_VOIE,
                description=self.descr_fantoir_voie,
                defaultValue=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.HYDRONYME,
                description=self.descr_hydronyme,
                defaultValue=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.FANTOIR_COMM,
                description=self.descr_fantoir_comm,
                defaultValue=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.CASSINI,
                description=self.descr_cassini,
                defaultValue=False,
            )
        )

        # self.addParameter(
        #     QgsProcessingParameterBoolean(
        #         name=self.SQUELETTE, description="Squelettisation", defaultValue=False
        #     )
        # )

        # self.addParameter(
        #     QgsProcessingParameterBoolean(
        #         name=self.REGEX, description="Regex", defaultValue=False
        #     )
        # )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                name=self.OUTPUT_TOPONYME,
                description=self.descr_topomyne,
                type=QgsProcessing.TypeVectorPoint,
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                name=self.OUTPUT_ODONYME,
                description=self.descr_odonyme,
                type=QgsProcessing.TypeVectorLine,
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                name=self.OUTPUT_FANTOIR_VOIE,
                description=self.descr_fantoir_voie,
                type=QgsProcessing.TypeVectorPoint,
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                name=self.OUTPUT_HYDRONYME,
                description=self.descr_hydronyme,
                type=QgsProcessing.TypeVectorPoint,
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                name=self.OUTPUT_FANTOIR_COMM,
                description=self.descr_fantoir_comm,
                type=QgsProcessing.TypeVectorPoint,
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                name=self.OUTPUT_CASSINI,
                description=self.descr_cassini,
                type=QgsProcessing.TypeVectorPoint,
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports
        # are adjusted for the overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        search = self.parameterAsString(parameters, self.SEARCH, context)

        if search is None or len(search) == 0:
            raise QgsProcessingException("TypeError: a search parameter is required.")

        toponyme = self.parameterAsBoolean(parameters, self.TOPONYME, context)
        odonyme = self.parameterAsBoolean(parameters, self.ODONYME, context)
        fantoir_voie = self.parameterAsBoolean(parameters, self.FANTOIR_VOIE, context)
        hydronyme = self.parameterAsBoolean(parameters, self.HYDRONYME, context)
        fantoir_comm = self.parameterAsBoolean(parameters, self.FANTOIR_COMM, context)
        cassini = self.parameterAsBoolean(parameters, self.CASSINI, context)

        # squelette = self.parameterAsBoolean(parameters, self.SQUELETTE, context)
        # regex = self.parameterAsBoolean(parameters, self.REGEX, context)
        search_method = self.parameterAsEnum(
            parameters, self.SEARCH_METHOD_OPTION, context
        )

        squelette = False
        regex = False
        if search_method == 1:
            squelette = True
            regex = False
        elif search_method == 2:
            squelette = False
            regex = True
        elif search_method == 0:
            squelette = False
            regex = False
        else:
            raise QgsProcessingException(
                "TypeError: a search method parameter is required."
            )

        codec = QTextCodec.codecForName("UTF-8")

        if toponyme:
            toponyme_response = get_topomine_toponyme(
                search=search, squelette=squelette, regex=regex
            )

            toponyme_layer = QgsVectorLayer(
                "Point?crs=EPSG:4326",
                f"{self.descr_topomyne} - {search}",
                "memory",
            )

            fields = QgsJsonUtils.stringToFields(json.dumps(toponyme_response), codec)
            features = QgsJsonUtils.stringToFeatureList(
                json.dumps(toponyme_response), fields, codec
            )
            toponyme_layer_pr = toponyme_layer.dataProvider()
            toponyme_layer_pr.addAttributes(fields)
            toponyme_layer.updateFields()
            toponyme_layer_pr.addFeatures(features)

        if odonyme:
            odonyme_response = get_topomine_odonyme(
                search=search, squelette=squelette, regex=regex
            )

            odonyme_layer = QgsVectorLayer(
                "LineString?crs=EPSG:4326",
                f"{self.descr_odonyme} - {search}",
                "memory",
            )

            fields = QgsJsonUtils.stringToFields(json.dumps(odonyme_response), codec)
            features = QgsJsonUtils.stringToFeatureList(
                json.dumps(odonyme_response), fields, codec
            )
            odonyme_layer_pr = odonyme_layer.dataProvider()
            odonyme_layer_pr.addAttributes(fields)
            odonyme_layer.updateFields()
            odonyme_layer_pr.addFeatures(features)

        if fantoir_voie:
            fantoir_voie_response = get_topomine_fantoir_voie(
                search=search, squelette=squelette, regex=regex
            )

            fantoir_voie_layer = QgsVectorLayer(
                "Point?crs=EPSG:4326",
                f"{self.descr_fantoir_voie} - {search}",
                "memory",
            )

            fields = QgsJsonUtils.stringToFields(
                json.dumps(fantoir_voie_response), codec
            )
            features = QgsJsonUtils.stringToFeatureList(
                json.dumps(fantoir_voie_response), fields, codec
            )
            fantoir_voie_layer_pr = fantoir_voie_layer.dataProvider()
            fantoir_voie_layer_pr.addAttributes(fields)
            fantoir_voie_layer.updateFields()
            fantoir_voie_layer_pr.addFeatures(features)

        if hydronyme:
            hydronyme_response = get_topomine_hydronyme(
                search=search, squelette=squelette, regex=regex
            )

            hydronyme_layer = QgsVectorLayer(
                "Point?crs=EPSG:4326",
                f"{self.descr_hydronyme} - {search}",
                "memory",
            )

            fields = QgsJsonUtils.stringToFields(json.dumps(hydronyme_response), codec)
            features = QgsJsonUtils.stringToFeatureList(
                json.dumps(hydronyme_response), fields, codec
            )
            hydronyme_layer_pr = hydronyme_layer.dataProvider()
            hydronyme_layer_pr.addAttributes(fields)
            hydronyme_layer.updateFields()
            hydronyme_layer_pr.addFeatures(features)

        if fantoir_comm:
            fantoir_comm_response = get_topomine_fantoir_commune(
                search=search, squelette=squelette, regex=regex
            )

            fantoir_comm_layer = QgsVectorLayer(
                "Point?crs=EPSG:4326",
                f"{self.descr_fantoir_comm} - {search}",
                "memory",
            )

            fields = QgsJsonUtils.stringToFields(
                json.dumps(fantoir_comm_response), codec
            )
            features = QgsJsonUtils.stringToFeatureList(
                json.dumps(fantoir_comm_response), fields, codec
            )
            fantoir_comm_layer_pr = fantoir_comm_layer.dataProvider()
            fantoir_comm_layer_pr.addAttributes(fields)
            fantoir_comm_layer.updateFields()
            fantoir_comm_layer_pr.addFeatures(features)

        if cassini:
            cassini_response = get_topomine_cassini(
                search=search, squelette=squelette, regex=regex
            )

            cassini_layer = QgsVectorLayer(
                "Point?crs=EPSG:4326",
                f"{self.descr_cassini} - {search}",
                "memory",
            )

            fields = QgsJsonUtils.stringToFields(json.dumps(cassini_response), codec)
            features = QgsJsonUtils.stringToFeatureList(
                json.dumps(cassini_response), fields, codec
            )
            cassini_layer_pr = cassini_layer.dataProvider()
            cassini_layer_pr.addAttributes(fields)
            cassini_layer.updateFields()
            cassini_layer_pr.addFeatures(features)

        temp = []
        # Create layers for each type of search result
        feedback.pushInfo(
            "-------------------------------------------------\n"
            + self.tr("Search results")
            + "\n"
            + "-------------------------------------------------"
        )
        # toponyme
        if toponyme:
            if toponyme_layer.hasFeatures():
                toponyme_layer.updateExtents()
                context.temporaryLayerStore().addMapLayer(toponyme_layer)
                temp.append(
                    (
                        self.descr_topomyne + " - " + search,
                        self.OUTPUT_TOPONYME,
                        toponyme_layer.id(),
                    )
                )
                feedback.pushInfo(
                    (
                        f"{toponyme_layer.featureCount()} "
                        + self.tr("search results based on Toponyms (IGN / BD TOPO) - ")
                        + f"{search}"
                    )
                )
            else:
                feedback.pushWarning(
                    self.tr("No search results based on Toponyms (IGN / BD TOPO) - ")
                    + f"{search}"
                )

        # odonyme
        if odonyme:
            if odonyme_layer.hasFeatures():
                odonyme_layer.updateExtents()
                context.temporaryLayerStore().addMapLayer(odonyme_layer)
                temp.append(
                    (
                        self.descr_odonyme + " - " + search,
                        self.OUTPUT_ODONYME,
                        odonyme_layer.id(),
                    )
                )
                feedback.pushInfo(
                    (
                        f"{odonyme_layer.featureCount()} "
                        + self.tr("search results based on Odonyms (IGN / BD TOPO) - ")
                        + f"{search}"
                    )
                )
            else:
                feedback.pushWarning(
                    self.tr("No search results based on Odonyms (IGN / BD TOPO) - ")
                    + f"{search}"
                )

        # fantoir_voie
        if fantoir_voie:
            if fantoir_voie_layer.hasFeatures():
                fantoir_voie_layer.updateExtents()
                context.temporaryLayerStore().addMapLayer(fantoir_voie_layer)
                temp.append(
                    (
                        self.descr_fantoir_voie + " - " + search,
                        self.OUTPUT_FANTOIR_VOIE,
                        fantoir_voie_layer.id(),
                    )
                )
                feedback.pushInfo(
                    (
                        f"{fantoir_voie_layer.featureCount()} "
                        + self.tr("search results based on Odonyms (FANTOIR) - ")
                        + f"{search}"
                    )
                )
            else:
                feedback.pushWarning(
                    self.tr("No search results based on Odonyms (FANTOIR) - ")
                    + f"{search}"
                )

        # hydronyme
        if hydronyme:
            if hydronyme_layer.hasFeatures():
                hydronyme_layer.updateExtents()
                context.temporaryLayerStore().addMapLayer(hydronyme_layer)
                temp.append(
                    (
                        self.descr_hydronyme + " - " + search,
                        self.OUTPUT_HYDRONYME,
                        hydronyme_layer.id(),
                    )
                )
                feedback.pushInfo(
                    (
                        f"{hydronyme_layer.featureCount()} "
                        + self.tr("search results based on Hydronyms (SANDRE) - ")
                        + f"{search}"
                    )
                )
            else:
                feedback.pushWarning(
                    self.tr("No search results based on Hydronyms (SANDRE) - ")
                    + f"{search}"
                )

        # fantoir_comm
        if fantoir_comm:
            if fantoir_comm_layer.hasFeatures():
                fantoir_comm_layer.updateExtents()
                context.temporaryLayerStore().addMapLayer(fantoir_comm_layer)
                temp.append(
                    (
                        self.descr_fantoir_comm + " - " + search,
                        self.OUTPUT_FANTOIR_COMM,
                        fantoir_comm_layer.id(),
                    )
                )
                feedback.pushInfo(
                    (
                        f"{fantoir_comm_layer.featureCount()} "
                        + self.tr(
                            "search results based on current Communes (FANTOIR) - "
                        )
                        + f"{search}"
                    )
                )
            else:
                feedback.pushWarning(
                    self.tr("No search results based on current Communes (FANTOIR) - ")
                    + f"{search}"
                )

        # cassini
        if cassini:
            if cassini_layer.hasFeatures():
                cassini_layer.updateExtents()
                context.temporaryLayerStore().addMapLayer(cassini_layer)
                temp.append(
                    (
                        self.descr_cassini + " - " + search,
                        self.OUTPUT_CASSINI,
                        cassini_layer.id(),
                    )
                )
                feedback.pushInfo(
                    (
                        f"{cassini_layer.featureCount()} "
                        + self.tr(
                            "search results based on historical Communes (Cassini-EHESS) - "
                        )
                        + f"{search}"
                    )
                )
            else:
                feedback.pushWarning(
                    self.tr(
                        "No search results based on historical Communes (Cassini-EHESS) - "
                    )
                    + f"{search}"
                )

        feedback.pushInfo("\n-------------------------------------------------")

        for l_name, e_id, l_id in temp:
            results[e_id] = l_id
            context.addLayerToLoadOnCompletion(
                l_id,
                QgsProcessingContext.LayerDetails(l_name, context.project(), l_name),
            )

        return results

    def name(self):
        return "search_topomine"

    def displayName(self):
        return self.tr("Search for toponyms")

    def group(self):
        return ""

    def groupId(self):
        return ""

    def createInstance(self):
        return TopomineSearchAlgorithm()
