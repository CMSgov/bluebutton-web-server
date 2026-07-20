# Start with building the url
# https://verified.clearme.com/integrations/oauth2/auth?response_type=code&client_id=bluebutton-sample&state=teststate&redirect_uri=http://localhost:3001/api/clear/callback&scope=offline%20openid%20offline_access&code_challenge=<insert_generated_code_challenge_here>&code_challenge_method=S256

# Get the generation of the code challenge and the code verifier
# TODO: Mimic login flow somehow for synthetic user to receive a code value

# POST to the clear token endpoint
# curl --location 'https://verified.clearme.com/integrations/oauth2/token' \
# --header 'Content-Type: application/x-www-form-urlencoded' \
# --header 'Cookie: ' \
# --data-urlencode 'client_id=bluebutton-sample' \
# --data-urlencode 'client_secret=<secret-from-aws>' \
# --data-urlencode 'scope=offline openid offline_access' \
# --data-urlencode 'grant_type=authorization_code' \
# --data-urlencode 'redirect_uri=http://localhost:3001/api/clear/callback' \
# --data-urlencode 'code=<code-from-url>' \
# --data-urlencode 'code_verifier=<generated-code-verifier>'

# Get the client secret from AWS SSM as a environment variable

# TODO: Construct this
# {
#   "iss": "<paste_client_id_here>",
#   "sub": "<paste_client_id_here>",
#   "aud": "https://<paste_env_here>.bluebutton.cms.gov/v3/o/token",
#   "jti": "<paste_jti_here>",
#   "exp": <paste_exp_here>,
#   "extensions": {
#     "cms_smart": {
#       "version": "1",
#       "purpose_of_use": "PATRQT",
#       "id_token": "<paste_id_token_here>"
#     }
#   }
# }

# Ensure the iss and sub are the client id
# jti is a randomly generated uuid
# exp must be within 5 minutes of the current timestamp from unix epoch time

# TODO: Construct the payload for algorithm and token type
# {
#   "alg": "RS384",
#   "kid": "my-key-id-1",
#   "typ": "JWT"
# }

# TODO: Get a private key to encode the jwt, possibly store this within SOPS/SSM and read it in as an environment variable
# For now, let's just pretend we have the variables read in already

# The output of after we send in the a POST request to BBAPI's token endpoint as the client_assertion
