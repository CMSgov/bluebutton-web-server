import uuid
from django.db.utils import IntegrityError
from oauth2_provider.models import get_application_model
from .models import AuthFlowUuid

"""
  Logger related functions for dot_ext/mymedicare_cb modules and auth flow trace logging.
"""

SESSION_AUTH_FLOW_TRACE_KEYS = ['auth_uuid', 'auth_client_id', 'auth_app_id', 'auth_app_name']


def cleanup_session_auth_flow_trace(request=None):
    '''
    Function for cleaning up auth flow related items
    in session.
    '''
    if request:
        # We are done using auth flow trace values, clear them from the session.
        for k in SESSION_AUTH_FLOW_TRACE_KEYS:
            try:
                del request.session[k]
            except KeyError:
                pass


def create_session_auth_flow_trace(request):
    '''
    Function for creating auth flow log tracing related items.

    - Creates a new AuthFlowUuid instance.
    - Sets new auth flow values in session.

    Returns an AuthFlowUuid instance or None.
    '''
    if request:
        auth_flow_uuid = None
        application = None

        # Create new authorization flow trace UUID.
        new_auth_uuid = str(uuid.uuid4())

        request.session['auth_uuid'] = new_auth_uuid

        client_id_param = request.GET.get("client_id", None)

        if client_id_param:
            # Get the application.
            Application = get_application_model()
            try:
                application = get_application_model().objects.get(client_id=client_id_param)

                # Set values in session.
                auth_flow_dict = {"auth_uuid": new_auth_uuid,
                                  "auth_app_id": str(application.id),
                                  "auth_app_name": str(application.name),
                                  "auth_client_id": str(application.client_id),
                                  }
                set_session_auth_flow_trace(request, auth_flow_dict)
            except Application.DoesNotExist:
                # Clear values in session. Set to empty value to denote not found.
                auth_flow_dict = {"auth_uuid": new_auth_uuid,
                                  "auth_app_id": "",
                                  "auth_app_name": "",
                                  "auth_client_id": "",
                                  }
                set_session_auth_flow_trace(request, auth_flow_dict)
                application = None

        if application:
            # Create and return AuthFlowUuid instance for tracking.
            auth_flow_uuid = AuthFlowUuid.objects.create(auth_uuid=new_auth_uuid, client_id=application.client_id)

    return auth_flow_uuid


def get_session_auth_flow_trace(request):
    '''
    Function to get auth flow related items from the
    session.

    Returns a auth_flow_dict type DICT of values for logging.
    '''
    if request:
        auth_flow_dict = {}
        for k in SESSION_AUTH_FLOW_TRACE_KEYS:
            auth_flow_dict[k] = request.session.get(k, None)
        return auth_flow_dict
    else:
        return {}


def set_session_auth_flow_trace(request, auth_flow_dict):
    '''
    Function to set auth flow related items in the
    session from a dictionary.
    '''
    if request:
        for k in SESSION_AUTH_FLOW_TRACE_KEYS:
            request.session[k] = auth_flow_dict.get(k, None)


def set_session_values_from_auth_flow_uuid(request, auth_flow_uuid):
    '''
    Function to set auth flow related items in the
    session given an AuthFlowUuid instance.
    '''
    application = None
    if auth_flow_uuid:
        request.session['auth_uuid'] = str(auth_flow_uuid.auth_uuid)

        # Get the application.
        Application = get_application_model()
        try:
            application = Application.objects.get(client_id=auth_flow_uuid.client_id)
        except Application.DoesNotExist:
            pass

    if application:
        # Set values in session.
        request.session['auth_app_id'] = str(application.id)
        request.session['auth_app_name'] = str(application.name)
        request.session['auth_client_id'] = str(application.client_id)


def update_session_auth_flow_trace(request=None, auth_uuid=None, state=None, code=None):
    '''
    Function for updating auth flow related items in the
    AuthFlowUuid tracking object and session.

    Summary of cases based on arguments passed in:

    - auth_uuid and code = Update previously created AuthFlowUuid instance with code.
    - code =  Get session values from AuthFlowUuid via code.
    - auth_uuid = Get session values from AuthFlowUuid.
    - state = Update or set state in session.
    '''
    if auth_uuid and code:
        # Get and update previously created AuthFlowUuid instance with code.
        try:
            auth_flow_uuid = AuthFlowUuid.objects.get(auth_uuid=auth_uuid)
            # Set code.
            auth_flow_uuid.code = code
            auth_flow_uuid.save()
        except AuthFlowUuid.DoesNotExist:
            # Create AuthFlowUuid instance, if it doesn't exist.
            if auth_uuid:
                try:
                    auth_flow_uuid = AuthFlowUuid.objects.create(auth_uuid=auth_uuid, code=code, state=None)
                except IntegrityError:
                    pass

    elif code:
        # Get session values from AuthFlowUuid via code.
        try:
            # Get previously created AuthFlowUuid with code.
            auth_flow_uuid = AuthFlowUuid.objects.get(code=code)
            set_session_values_from_auth_flow_uuid(request, auth_flow_uuid)

            # Delete the no longer needed instance
            auth_flow_uuid.delete()
            auth_flow_uuid = None
        except AuthFlowUuid.DoesNotExist:
            pass

    elif auth_uuid:
        # Get session values from AuthFlowUuid.
        request.session['auth_uuid'] = str(auth_uuid)

        try:
            auth_flow_uuid = AuthFlowUuid.objects.get(auth_uuid=auth_uuid)
            set_session_values_from_auth_flow_uuid(request, auth_flow_uuid)
        except AuthFlowUuid.DoesNotExist:
            pass

    elif state:
        # Update AuthFlowUuid instance to pass along auth_uuid using state.
        auth_uuid = request.session.get('auth_uuid', None)

        if auth_uuid:
            # Store state in AuthFlowUuid if auth_uuid exists.
            try:
                auth_flow_uuid = AuthFlowUuid.objects.get(auth_uuid=auth_uuid)
                auth_flow_uuid.state = state
                auth_flow_uuid.save()
            except AuthFlowUuid.DoesNotExist:
                auth_flow_uuid = None

        if not auth_flow_uuid:
            # Retreive auth flow session values using previous state in AuthFlowUuid.
            try:
                auth_flow_uuid = AuthFlowUuid.objects.get(state=state)
                set_session_values_from_auth_flow_uuid(request, auth_flow_uuid)
            except AuthFlowUuid.DoesNotExist:
                pass
