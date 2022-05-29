import json
import socket

import grpc
import requests
from anki_vector import messaging
from anki_vector.configure import __main__ as vector_api
from requests import HTTPError

from custom_components.ddl_vector.vector.entity import VectorConfig


def get_vector_cert(vector_config: VectorConfig) -> bytes:
    response = requests.get('https://session-certs.token.global.anki-services.com/vic/{}'.format(vector_config.serial))
    if response.status_code != 200:
        raise HTTPError(response.content)

    return response.content


def get_vector_guid(vector_config: VectorConfig, username: str, password: str) -> bytes:
    token = _get_session_token(vector_api.Api(), username, password)
    if not token.get("session"):
        raise Exception("Session error: {}".format(token))

    return _user_authentication(vector_config, token["session"]["session_token"])


def _get_session_token(api: vector_api.Api, username, password):
    payload = {'username': username, 'password': password}

    response = requests.post(api.handler.url, data=payload, headers=api.handler.headers)
    if response.status_code != 200:
        raise Exception(response.content)

    return json.loads(response.content)


def _user_authentication(vector_config: VectorConfig, session_id: bytes) -> bytes:
    # Pin the robot certificate for opening the channel
    creds = grpc.ssl_channel_credentials(root_certificates=vector_config.cert.encode("utf-8"))

    channel = grpc.secure_channel("{}:443".format(vector_config.ip), creds,
                                  options=(("grpc.ssl_target_name_override", vector_config.name,),))

    # Verify the connection to Vector is able to be established (client-side)
    try:
        # Explicitly grab _channel._channel to test the underlying grpc channel directly
        grpc.channel_ready_future(channel).result(timeout=30)
    except grpc.FutureTimeoutError:
        raise Exception("Unable to connect to Vector. Please be sure to connect via the Vector companion app first, and connect your computer to the same network as your Vector.")

    try:
        interface = messaging.client.ExternalInterfaceStub(channel)
        request = messaging.protocol.UserAuthenticationRequest(
            user_session_id=session_id.encode('utf-8'),
            client_name=socket.gethostname().encode('utf-8'))

        response = interface.UserAuthentication(request)
        if response.code != messaging.protocol.UserAuthenticationResponse.AUTHORIZED:  # pylint: disable=no-member
            raise Exception("Failed to authorize request: Please be sure to first set up Vector using the companion app.")
    except grpc.RpcError as e:
        raise Exception("Failed to authorize request: An unknown error occurred '{}'".format(e))

    return response.client_token_guid