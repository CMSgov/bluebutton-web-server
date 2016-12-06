from django import forms
from django.utils.translation import ugettext_lazy as _
import uuid
import json
from collections import OrderedDict
import jwt
from poetri.sign_poet import sign_poet
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

GRANT_TYPE_CHOICES = (("authorization_code", "authorization_code"),
                      ("implicit", "implicit"),
                      ("password", "password"),
                      ("client_credentials", "client_credentials"),
                      ("refresh_token", "refresh_token"))

TOKEN_ENDPOINT_AUTH_METHOD_CHOICES = (
                                     ("", "none"),
                                     ("client_secret_post", "client_secret_post"),
                                     ("client_secret_basic", "client_secret_basic"))


EXPIRE_CHOICES = ((31536000, "1 Year"),
                  (63072000, "2 Years"),
                  (86400, "1 Day"),
                  (1, "1 Second"))


# This key is for testing and the CN is "transparenthealth.org"
test_private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQComk77MDN73N/w
FphyPbL0uc0jzKvSI8qK/TGvDx+9ygPFzYq6RdsgNE5cOHdtXk6/ukaMt7ssmvRU
zyqKtx4033MssEvDlmYIrE1dvquiPg2CSIMxCsyny7191rLPN3iANC3a/39OBOg+
pBev6S+k9hQcV00j0oxfC9Aof8aT1f9P+l6gu3n3y9OTDcrz3hSv4dONDOxnKWiD
JG26Myuvap0+AP84Qa2WwNWJR0mwXAR5q9RuCG3IoIWuBUTKIDbe79Favy7R15Fc
B7atsd7KSnpyhSwwWp85OcMpQPSiUNCTNHgLl9WqdZxD1LFCR2WkUbMDtYZx1Yw+
vP0qE+3ZAgMBAAECggEAS566IetijAFq5zIbOdH2e9EB8zaPMfcfluss54lvAR6k
RomD2TwPpggPxUkGN6V+yHtxvReC+eSeBZPNTt4GzEwUSkzgDl9ccDNnl843CNOw
F2kSfmKLnA7DdLdhB5OnlkjQ8FJ79LA6wi2y+hEqb2B3cKavUIvUraSMvj1hAVjV
hu0Dh6RvpMwDKRk5R74EEbBRfV4kX6qNjOaGFw9siwtp5qSY17eSbBCsBOMQHe9U
t1nG5Fu/ChgOpUOjCsKtGPgl7H/6BfZjtLiP7xaoxRySfSbnpyu+Sxqofwa8mnjE
qdQTONkR7GztnaL/+2LHeLrCyDtklwptzeNuVKf6AQKBgQDQX3M/mfh1tCe9pZVi
+APDRVGw1ofsUQXOAHmY9eEwmIjmkV2HCHue3zwehzeLcmEeeI1Ozxi0JBsCsb+l
vb4m9AvEJkz6BaUCclqD6lcfcgiQbtSEsdQTS35aZSu8Woa0OGt4zDrSLB4jLrPR
EFdpA2FxcZMoNqbHMbF0B+9TYQKBgQDPI8krEwZT+mG0PCEIFiBFv5jMvOXd8qZE
Rq1iDVfI3iHta5fs7D0KzQVQqSFqCEQjPfC+dNAZL0SWHewNdf523TTZK4vOkaIB
PQEh568xk9EvV6/8QInO+4ljAM9/Kcze08SL0wj2aqa+iuys/6k1Ociz8xoEeEK0
4kEhbDileQKBgDYGiXsUELdz3lntdK4UX+VhM60F8nfzCe4/cUeXeKuA4P3m8rjw
Gh03A/9mT6B4J3YfC4RDbcRHGDm6nFX8vDCdVe+lfo/UptPbklxhhfVBO7c3BSLi
eHoIONp3IL/VONfBSRwo15dmmOnGUhkCg6dWmQ0wxVbH1LYQzFGpPQQBAoGAYoSA
r03zGonhYlme1DvByaqgv++v3GoGDj8XQ6VY9R5BQKyFq5eISNTODFkEnWulDKXv
FIZ2WyQSGNvOY3CVQG9hLVD6w5qcVL5xBXEt8AR/32ZzOyRu5tTXuRCvn6l/2RMb
Te1nO9vpxoJIotdN4RTEkmGzJCEWiPV7SKwyHPECgYEAwCdBX0pzpgAFbcX44FG8
Wo1b7C6y2vnAzm/MazBcDm9MH8X1oXdqRjKpY7kHXFYHB/fAxsUVCyOP82JVl5mq
yld/v0Z19nKV1e+rQz8DhdJtyUOOQ1szetHHvprDSK3KulBcojznIDgrRHqxSJcc
j1DFK16BeYLj88PTTKLtheE=
-----END PRIVATE KEY-----"""


class POETJWTForm(forms.Form):
    private_key = forms.CharField(max_length=4096,
                                  widget=forms.Textarea,
                                  initial=test_private_key,
                                  label=_('Private Key*'),
                                  help_text=_("The private key used for signing the JWT."))
    iss = forms.CharField(max_length=512,
                          label=_('Issuer*'),
                          help_text=_("Must contain a fully-qualified domain name (FQDN)"))
    exp = forms.ChoiceField(choices=EXPIRE_CHOICES,
                            label=_("Expires"))
    client_name = forms.CharField(max_length=255,
                                  help_text=_("The name of the application you want to endorse"))
    software_id = forms.CharField(max_length=36,
                                  initial=str(uuid.uuid4()),
                                  label=_('Software ID*'),
                                  help_text=_("A unique identifier for the client"))
    grant_types = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                            choices=GRANT_TYPE_CHOICES)
    redirect_uri = forms.CharField(max_length=2048,
                                   label=_('Redirect URI*'),
                                   help_text=_("OAuth2 redirect URI of the application you want to endorse."))

    redirect_uri_2 = forms.CharField(max_length=2048,
                                     label=_('Additional Redirect URI 2'),
                                     required=False,
                                     help_text=_("An additional OAuth2 redirect URI (if needed)."))

    redirect_uri_3 = forms.CharField(max_length=2048,
                                     label=_('Additional Redirect URI 3'),
                                     required=False,
                                     help_text=_("An additional OAuth2 redirect URI (if needed)."))

    scope = forms.CharField(max_length=255,
                            required=False,
                            help_text=_("A space-delimited string representing the OAuth2 scope(s)."))

    client_uri = forms.CharField(max_length=1024,
                                 required=False,
                                 help_text=_("The front page or home screen for the application"))

    initiate_login_uri = forms.CharField(max_length=1024, required=False,
                                         help_text=_("The login URL for the application"))

    logo_uri = forms.CharField(max_length=255, required=False,
                               help_text=_("A pointer to a logo for the client application."))

    token_endpoint_auth_method = forms.ChoiceField(required=False,
                                                   choices=TOKEN_ENDPOINT_AUTH_METHOD_CHOICES,
                                                   help_text=_("The token endpoint auth method."))
    required_css_class = 'required'

    def clean_private_key(self):
        private_key = self.cleaned_data.get('private_key')
        try:
            sign_poet({'iat': 1}, self.cleaned_data.get('private_key'),
                      self.cleaned_data.get('exp'))
        except ValueError:
            raise forms.ValidationError("The private key is invalid.")
        return private_key

    def clean_redirect_uri(self):
        redirect_uri = self.cleaned_data.get('redirect_uri')

        try:
            validate = URLValidator()
            validate(redirect_uri)
        except ValidationError:
            raise forms.ValidationError("Invalid URL")
        return redirect_uri

    def clean_redirect_uri_2(self):
        redirect_uri = self.cleaned_data.get('redirect_uri_2', '')
        if redirect_uri:
            try:
                validate = URLValidator()
                validate(redirect_uri)
            except ValidationError:
                raise forms.ValidationError("Invalid URL")
        return redirect_uri

    def clean_redirect_uri_3(self):
        redirect_uri = self.cleaned_data.get('redirect_uri_3', '')
        if redirect_uri:
            try:
                validate = URLValidator()
                validate(redirect_uri)
            except ValidationError:
                raise forms.ValidationError("Invalid URL")
        return redirect_uri

    def clean_client_uri(self):
        client_uri = self.cleaned_data.get('client_uri', '')
        if client_uri:
            try:
                validate = URLValidator()
                validate(client_uri)
            except ValidationError:
                raise forms.ValidationError("Invalid URL")
        return client_uri

    def clean_logo_uri(self):
        logo_uri = self.cleaned_data.get('logo_uri', '')
        if logo_uri:
            try:
                validate = URLValidator()
                validate(logo_uri)
            except ValidationError:
                raise forms.ValidationError("Invalid URL")
        return logo_uri

    def clean_initiate_login_uri(self):
        initiate_login_uri = self.cleaned_data.get('initiate_login_uri', '')
        if initiate_login_uri:
            try:
                validate = URLValidator()
                validate(initiate_login_uri)
            except ValidationError:
                raise forms.ValidationError("Invalid URL")
        return initiate_login_uri

    def create_payload(self):
        payload = OrderedDict()
        payload['client_name'] = self.cleaned_data.get('client_name')
        payload['software_id'] = self.cleaned_data.get('software_id')
        payload['iss'] = self.cleaned_data.get('iss')
        payload['redirect_uris'] = [self.cleaned_data.get('redirect_uri')]
        if self.cleaned_data.get('redirect_uri_2'):
            payload['redirect_uris'].append(self.cleaned_data.get('redirect_uri_2'))
        if self.cleaned_data.get('redirect_uri_3'):
            payload['redirect_uris'].append(self.cleaned_data.get('redirect_uri_3'))
        payload['grant_types'] = self.cleaned_data.get('grant_types')
        payload['scope'] = self.cleaned_data.get('scope', '')
        payload['token_endpoint_auth_method'] = self.cleaned_data.get('token_endpoint_auth_method', '')
        payload['logo_uri'] = self.cleaned_data.get('logo_uri', '')
        payload['initiate_login_uri'] = self.cleaned_data.get('initiate_login_uri', '')
        return payload

    def output_payload(self):
        payload = jwt.decode(self.create_jwt(), verify=False)
        return payload

    def create_payload_json(self):
        return json.dumps(self.output_payload(), indent=4)

    def create_jwt(self):
        return sign_poet(self.create_payload(),
                         self.cleaned_data.get('private_key'),
                         self.cleaned_data.get('iss'),
                         int(self.cleaned_data.get('exp')))
