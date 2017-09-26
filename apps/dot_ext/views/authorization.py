from __future__ import absolute_import
from __future__ import unicode_literals
import logging
from django.utils.decorators import method_decorator
from oauth2_provider.views.base import AuthorizationView as DotAuthorizationView
from oauth2_provider.models import get_application_model
from oauth2_provider.exceptions import OAuthToolkitError
from oauth2_provider.http import HttpResponseUriRedirect
from ratelimit.decorators import ratelimit
from ..forms import AllowForm
from ..models import ExpiresIn


logger = logging.getLogger('hhs_server.%s' % __name__)


@method_decorator(ratelimit(key='user_or_ip', rate='5/m', method=['GET', 'POST'], block=True), name='dispatch')
class AuthorizationView(DotAuthorizationView):
    """
    Override the base authorization view from dot to
    use the custom AllowForm.
    """
    form_class = AllowForm

    def form_valid(self, form):
        try:
            credentials = {
                'client_id': form.cleaned_data.get('client_id'),
                'redirect_uri': form.cleaned_data.get('redirect_uri'),
                'response_type': form.cleaned_data.get('response_type', None),
                'state': form.cleaned_data.get('state', None),
                'form_expires_in': form.cleaned_data.get('expires_in'),
            }

            scopes = form.cleaned_data.get('scope')
            allow = form.cleaned_data.get('allow')
            uri, headers, body, status = self.create_authorization_response(
                request=self.request, scopes=scopes, credentials=credentials, allow=allow)
            self.success_url = uri

            # here we save the expires_in choice from the allow form
            # into the expires cache table.
            expires_in = form.cleaned_data.get('expires_in')
            client_id = form.cleaned_data.get('client_id')
            user_id = self.request.user.pk
            ExpiresIn.objects.set_expires_in(client_id, user_id, expires_in)

            logger.debug("Success url for the request: {0}".format(self.success_url))
            return HttpResponseUriRedirect(self.success_url)

        except OAuthToolkitError as error:
            return self.error_response(error)

    def get_form_kwargs(self):
        kwargs = super(AuthorizationView, self).get_form_kwargs()

        # the application instance is needed by our custom AllowForm
        # to properly initialize choices for the scope field
        if self.request.method == 'GET':
            kwargs['application'] = self.oauth2_data['application']
        else:
            # in case of a PUT or POST request we must load
            # the application instance from `client_id` param in
            # the POST dict because self.oauth2_data is empty.
            client_id = self.request.POST.get('client_id')

            Application = get_application_model()
            try:
                application = Application.objects.get(client_id=client_id)
                kwargs['application'] = application
            except Application.DoesNotExist:
                logger.warning("no application found with client_id '%s'", client_id)

        return kwargs

    def create_authorization_response(self, request, scopes, credentials, allow):
        """
        A wrapper method that calls create_authorization_response on `server_class`
        instance.

        :param request: The current django.http.HttpRequest object
        :param credentials: Authorization credentials dictionary containing
                           `client_id`, `state`, `redirect_uri`, `response_type`
        :param allow: True if the user authorize the client, otherwise False
        """
        # we needed to override this method because it called
        # split(" ") on the scopes parameter to transform it into a list.
        # With our custom AllowForm, the scopes parameter is already a string
        # and we don't need to call `split` here.
        core = self.get_oauthlib_core()
        return core.create_authorization_response(request, scopes, credentials, allow)
