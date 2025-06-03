#! python3  # noqa: E265

"""
    Perform network request.
"""

# ############################################################################
# ########## Imports ###############
# ##################################


# Standard library
import json
from functools import lru_cache
from urllib.parse import urlparse, urlunparse

# PyQGIS
from qgis.core import QgsBlockingNetworkRequest
from qgis.PyQt.Qt import QByteArray, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest

# project
from topomine.toolbelt.log_handler import PlgLogger
from topomine.toolbelt.preferences import PlgOptionsManager

# ############################################################################
# ########## Classes ###############
# ##################################


class NetworkRequestsManager:
    """Helper on network operations."""

    def __init__(self):
        """Initialization."""
        self.log = PlgLogger().log
        self.ntwk_requester = QgsBlockingNetworkRequest()
        self.plg_settings = PlgOptionsManager.get_plg_settings()

    @lru_cache(maxsize=128)
    def build_url(
        self, request_url: str, request_url_query: str, additional_query: str = None
    ) -> QUrl:
        """Build URL using plugin settings and returns it as QUrl.

        :return: complete URL
        :rtype: QUrl
        """
        parsed_url = urlparse(request_url)

        if additional_query:
            url_query = request_url_query + additional_query
        else:
            url_query = request_url_query

        clean_url = parsed_url._replace(query=url_query)
        return QUrl(urlunparse(clean_url))

    def build_request(
        self, request_url: str = None, request_url_query: str = None, url: QUrl = None
    ) -> QNetworkRequest:
        """Build request object from an url and a query or a already defined QUrl

        Args:
            request_url (str, optional): Request url. Defaults to None.
            request_url_query (str, optional): Request url query. Defaults to None.
            url (QUrl, optional): for url for QNetworkRequest. Request url query and request url are not used. Defaults to None.

        Returns:
            QNetworkRequest: network request object.
        """
        # if URL is not specified, let's use the default one
        if not url:
            url = self.build_url(request_url, request_url_query)

        # create network object
        qreq = QNetworkRequest(url=url)

        # headers
        headers = {
            b"Accept": bytes(self.plg_settings.http_content_type, "utf8"),
            b"User-Agent": bytes(self.plg_settings.http_user_agent, "utf8"),
        }
        for k, v in headers.items():
            qreq.setRawHeader(k, v)

        return qreq

    def get_url(self, url: QUrl = None, headers: dict = None) -> QByteArray:
        """Send a get method., using cache and plugin settings.

        :raises ConnectionError: if any problem occurs during feed fetching.
        :raises TypeError: if response mime-type is not valid

        :return: feed response in bytes
        :rtype: QByteArray

        :example:

        .. code-block:: python

            import json
            response_as_dict = json.loads(str(response, "UTF8"))
        """
        # prepare request
        try:
            req = self.build_request(url=url)
            if headers:
                for k, v in headers.items():
                    req.setRawHeader(k, v)
        except Exception as err:
            self.log(
                message=f"Something went wrong during request preparation: {err}",
                log_level=2,
                push=False,
            )
            raise err

        # send request
        try:
            req_status = self.ntwk_requester.get(
                request=req,
                forceRefresh=False,
            )

            # check if request is fine
            if req_status != QgsBlockingNetworkRequest.NoError:
                err_msg = f"{self.ntwk_requester.errorMessage()}."

                # get the API response error to log it
                req_reply = self.ntwk_requester.reply()
                if req_reply and b"application/json" in req_reply.rawHeader(
                    b"Content-Type"
                ):
                    api_response_error = json.loads(str(req_reply.content(), "UTF8"))
                    if "message" in api_response_error:
                        err_msg += (
                            f"API error message: {api_response_error.get('message')}"
                        )
                    if "message" in api_response_error:
                        err_msg += (
                            f"API error message: {api_response_error.get('message')}"
                        )

                raise ConnectionError(err_msg)

            self.log(
                message=f"DEBUG - Request to {url} succeeded.",
                log_level=4,
            )

            # check reply
            req_reply = self.ntwk_requester.reply()
            if b"application/json" not in req_reply.rawHeader(b"Content-Type"):
                raise TypeError(
                    "Response mime-type is '{}' not 'application/json' as required.".format(
                        req_reply.rawHeader(b"Content-type")
                    )
                )

            return req_reply.content()

        except Exception as err:
            err_msg = "Houston, we've got a problem: {}".format(err)
            self.log(message=err_msg, log_level=2, push=False)
            raise err
