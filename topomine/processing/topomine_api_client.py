import json
from urllib.parse import urlparse, urlunparse

from qgis.core import Qgis, QgsBlockingNetworkRequest
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest

from topomine.toolbelt.log_handler import PlgLogger
from topomine.toolbelt.preferences import PlgOptionsManager

log = PlgLogger().log

plg_settings = PlgOptionsManager.get_plg_settings()
API_URL = plg_settings.api_url

TOPONYME_ENDPOINT = API_URL + "toponyme/?search="
ODONYME_ENDPOINT = API_URL + "odonyme/?search="
HYDRONYME_ENDPOINT = API_URL + "hydronyme/?search="
FANTOIR_COMM_ENDPOINT = API_URL + "fantoir/commune/?search="
FANTOIR_VOIE_ENDPOINT = API_URL + "fantoir/voie/?search="
CASSINI_ENDPOINT = API_URL + "cassini/?search="


def generic_topomine_client(
    endpoint: str,
    search: str = ...,
    squelette=False,
    regex=False,
    limit=100000000,
    offset=0,
) -> dict:

    search_query = (
        endpoint + str(search) + "&limit=" + str(limit) + "&offset=" + str(offset)
    )

    if squelette:
        search_query += "&search_method=squelette"
    if regex:
        search_query += "&search_method=regex"

    ntwk_requester = QgsBlockingNetworkRequest()
    qurl = QUrl(search_query)
    qreq = QNetworkRequest(qurl)

    # headers (HTTP content type and user agent)
    headers = {
        b"Accept": bytes(plg_settings.http_content_type, "utf8"),
        b"User-Agent": bytes(plg_settings.http_user_agent, "utf8"),
    }
    for k, v in headers.items():
        qreq.setRawHeader(k, v)

    # send request
    try:
        req_status = ntwk_requester.get(
            request=qreq,
            forceRefresh=False,
        )

        # check if request is fine
        if req_status != QgsBlockingNetworkRequest.ErrorCode.NoError:
            err_msg = f"{ntwk_requester.errorMessage()}."

            # get the API response error to log it
            req_reply = ntwk_requester.reply()
            if req_reply and b"application/json" in req_reply.rawHeader(
                b"Content-Type"
            ):
                api_response_error = json.loads(str(req_reply.content(), "UTF8"))
                if "message" in api_response_error:
                    err_msg += f"API error message: {api_response_error.get('message')}"
                if "message" in api_response_error:
                    err_msg += f"API error message: {api_response_error.get('message')}"

            raise ConnectionError(err_msg)

        log(
            message=f"DEBUG - Request to {qurl} succeeded.",
            log_level=Qgis.MessageLevel.NoLevel,
        )

        # check reply
        req_reply = ntwk_requester.reply()
        if b"application/json" not in req_reply.rawHeader(b"Content-Type"):
            raise TypeError(
                "Response mime-type is '{}' not 'application/json' as required.".format(
                    req_reply.rawHeader(b"Content-type")
                )
            )

        return json.loads(bytes(req_reply.content()))

    except Exception as err:
        err_msg = "Houston, we've got a problem: {}".format(err)
        log(message=err_msg, log_level=Qgis.MessageLevel.Critical, push=False)
        raise err


def get_topomine_toponyme(
    search: str = ..., squelette=False, regex=False, limit=100000000, offset=0
) -> dict:

    return generic_topomine_client(
        TOPONYME_ENDPOINT, search, squelette, regex, limit, offset
    )


def get_topomine_odonyme(
    search: str = ..., squelette=False, regex=False, limit=100000000, offset=0
) -> dict:

    return generic_topomine_client(
        ODONYME_ENDPOINT, search, squelette, regex, limit, offset
    )


def get_topomine_hydronyme(
    search: str = ..., squelette=False, regex=False, limit=100000000, offset=0
) -> dict:

    return generic_topomine_client(
        HYDRONYME_ENDPOINT, search, squelette, regex, limit, offset
    )


def get_topomine_fantoir_commune(
    search: str = ..., squelette=False, regex=False, limit=100000000, offset=0
) -> dict:

    return generic_topomine_client(
        FANTOIR_COMM_ENDPOINT, search, squelette, regex, limit, offset
    )


def get_topomine_fantoir_voie(
    search: str = ..., squelette=False, regex=False, limit=100000000, offset=0
) -> dict:

    return generic_topomine_client(
        FANTOIR_VOIE_ENDPOINT, search, squelette, regex, limit, offset
    )


def get_topomine_cassini(
    search: str = ..., squelette=False, regex=False, limit=100000000, offset=0
) -> dict:

    return generic_topomine_client(
        CASSINI_ENDPOINT, search, squelette, regex, limit, offset
    )
