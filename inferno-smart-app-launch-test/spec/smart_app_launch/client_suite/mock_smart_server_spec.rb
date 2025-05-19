RSpec.describe SMARTAppLaunch::MockSMARTServer, :request, :runnable do
  include SMARTAppLaunch::URLs
  let(:suite_id) { 'smart_client_stu2_2' }
  let(:backend_services_access_test) { suite.children[4].children[3] } # backend services data acccess test
  let(:backend_services_reg_test) { suite.children[3].children[0] } # backend services reg test
  let(:app_launch_ca_access_test) { suite.children[4].children[0] } # app launch confidential asymmetric data acccess
  let(:app_launch_ca_reg_test) { suite.children[0].children[0]} # app launch confidential asymmetric reg test
  let(:test_session) do # overriden to add suite options
    repo_create(
      :test_session,
      suite: suite_id,
      suite_options: [Inferno::DSL::SuiteOption.new(
        id: :client_type,
        value: SMARTAppLaunch::SMARTClientOptions::SMART_APP_LAUNCH_CONFIDENTIAL_ASYMMETRIC
      )]
    )
  end
  let(:results_repo) { Inferno::Repositories::Results.new }
  let(:session_repo) { Inferno::Repositories::SessionData.new }
  let(:dummy_result) { repo_create(:result, test_session_id: test_session.id) }
  let(:client_id) { 'cid' }
  let(:jwks_valid) do
    File.read(File.join(__dir__, '..', '..', '..', 'lib', 'smart_app_launch', 'smart_jwks.json'))
  end
  let(:parsed_jwks) { JWT::JWK::Set.new(JSON.parse(jwks_valid)) }
  let(:authorization_url) { "/custom/#{suite_id}#{SMARTAppLaunch::AUTHORIZATION_PATH}" }
  let(:authorization_code_token) { described_class.client_id_to_token(client_id, 10) }
  let(:token_url) { "/custom/#{suite_id}#{SMARTAppLaunch::TOKEN_PATH}" }
  let(:base_fhir_url) { "/custom/#{suite_id}/fhir" }
  let(:access_url) { "#{base_fhir_url}/Patient/999" }
  let(:redirect_uri) { "https://inferno.healthit.gov/redirect"}
  let(:access_response) { '{"resourceType": "Patent"}' }
  let(:pkce_verifier) { 'test' }
  let(:pkce_challenge) { Base64.urlsafe_encode64(Digest::SHA256.digest(pkce_verifier), padding: false)}
  let(:pkce_method) { 'S256' }
  let(:requested_scope) { 'system/*.rs' }
  let(:state) { '1234567890' }

  let(:header_invalid) do
    {
      typ: 'JWTX',
      alg: 'RS384',
      kid: 'b41528b6f37a9500edb8a905a595bdd7'
    }
  end
  let(:payload_invalid) do
    {
      iss: 'cid',
      sub: 'cidy',
      aud: 'https://inferno-qa.healthit.gov/suites/custom/davinci_pas_v201_client/auth/token'
    }
  end
  let(:client_assertion_sig_valid) { make_jwt(payload_invalid, header_invalid, 'RS384', parsed_jwks.keys[3]) }
  let(:client_assertion_sig_invalid) { "#{make_jwt(payload_invalid, header_invalid, 'RS384', parsed_jwks.keys[3])}bad" }
  let(:token_request_body_sig_invalid) do
    { grant_type: 'client_credentials',
      client_assertion_type: 'invalid',
      client_assertion: client_assertion_sig_invalid }
  end
  let(:token_request_body_sig_valid) do
    { grant_type: 'client_credentials',
      client_assertion_type: 'invalid',
      client_assertion: client_assertion_sig_valid }
  end
  let(:token_request_auth_code_body_sig_valid) do
    { grant_type: 'authorization_code',
      client_assertion_type: 'invalid',
      client_assertion: client_assertion_sig_valid,
      code: authorization_code_token,
      code_verifier: pkce_verifier,
      redirect_uri:
    }
  end
  let(:token_request_refresh_body_sig_valid) do
    { grant_type: 'refresh_token',
      client_assertion_type: 'invalid',
      client_assertion: client_assertion_sig_valid,
      refresh_token: SMARTAppLaunch::MockSMARTServer.authorization_code_to_refresh_token(authorization_code_token)
    }
  end
  let(:token_request_refresh_body_sig_invalid) do
    { grant_type: 'refresh_token',
      client_assertion_type: 'invalid',
      client_assertion: client_assertion_sig_invalid,
      refresh_token: SMARTAppLaunch::MockSMARTServer.authorization_code_to_refresh_token(authorization_code_token)
    }
  end

  def make_jwt(payload, header, alg, jwk)
    token = JWT::Token.new(payload:, header:)
    token.sign!(algorithm: alg, key: jwk.signing_key)
    token.jwt
  end

  def create_authorization_request(query_string, response_location)
    headers ||= [
      {
        type: 'response',
        name: 'Location',
        value: response_location
      }
    ]
    repo_create(
      :request,
      direction: 'incoming',
      url: "#{authorization_url}?#{query_string}",
      result: dummy_result,
      test_session_id: test_session.id,
      status: 302,
      tags: [SMARTAppLaunch::AUTHORIZATION_TAG, SMARTAppLaunch::SMART_TAG, SMARTAppLaunch::AUTHORIZATION_CODE_TAG],
      headers:
    )
  end

  describe 'when generating authorization responses for SMART' do
    it 'can return success with get' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
       
      inputs = { client_id:}
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      query_string = Rack::Utils.build_query({client_id: , redirect_uri: })
      get("#{authorization_url}?#{query_string}")
      expect(last_response.status).to eq(302)
    end

    it 'can return success with post' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
       
      inputs = { client_id:}
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      body = URI.encode_www_form([['client_id', client_id], ['redirect_uri', redirect_uri]])
      post authorization_url, body, 'CONTENT_TYPE' => 'application/x-www-form-urlencoded'
      expect(last_response.status).to eq(302)
    end

    it 'returns 400 when no redirect url' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
       
      inputs = { client_id:}
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      query_string = Rack::Utils.build_query({client_id: })
      get("#{authorization_url}?#{query_string}")
      expect(last_response.status).to eq(400)
      expect(last_response.body).to match(/Missing required redirect_uri parameter./)
    end
  end

  describe 'when generating authorization_code token responses for SMART' do
    it 'returns 200 for a valid request' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
      
      inputs = { client_id:}
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      auth_query_string = Rack::Utils.build_query({
        response_type: 'code',
        client_id:,
        redirect_uri:,
        scope: requested_scope,
        state:,
        aud: base_fhir_url,
        code_challenge: pkce_challenge,
        code_challenge_method: pkce_method
      })
      redirect_query_string = Rack::Utils.build_query({
        code: authorization_code_token,
        state:
      })
      create_authorization_request(auth_query_string, "#{redirect_uri}?#{redirect_query_string}")

      post_json(token_url, token_request_auth_code_body_sig_valid)
      expect(last_response.status).to eq(200)

      result = results_repo.find(result.id)
      expect(result.result).to eq('wait')
    end

    it 'returns 401 when no authorization request' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
      
      inputs = { client_id:}
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      post_json(token_url, token_request_auth_code_body_sig_valid)
      expect(last_response.status).to eq(401)
      error_body = JSON.parse(last_response.body)
      expect(error_body['error']).to eq('invalid_client')
      expect(error_body['error_description']).to match(/no authorization request found/)

      result = results_repo.find(result.id)
      expect(result.result).to eq('wait')
    end

    it 'returns 401 when no authorization request with the provided code' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
      
      inputs = { client_id:}
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      auth_query_string = Rack::Utils.build_query({
        response_type: 'code',
        client_id:,
        redirect_uri:,
        scope: requested_scope,
        state:,
        aud: base_fhir_url,
        code_challenge: pkce_challenge,
        code_challenge_method: pkce_method
      })
      redirect_query_string = Rack::Utils.build_query({
        code: "#{authorization_code_token}bad",
        state:
      })
      create_authorization_request(auth_query_string, "#{redirect_uri}?#{redirect_query_string}")

      post_json(token_url, token_request_auth_code_body_sig_valid)
      expect(last_response.status).to eq(401)
      error_body = JSON.parse(last_response.body)
      expect(error_body['error']).to eq('invalid_client')
      expect(error_body['error_description']).to match(/no authorization request found/)

      result = results_repo.find(result.id)
      expect(result.result).to eq('wait')
    end

    it 'includes tester-provided context when specified' do
      inputs = { client_id:, smart_jwk_set: jwks_valid, smart_redirect_uris: redirect_uri}
      result = run(app_launch_ca_reg_test, inputs)
      expect(result.result).to eq('pass')

      launch_context = { patient: '123' }.to_json
      inputs = { client_id:, launch_context: }
      result = run(app_launch_ca_access_test, inputs)
      expect(result.result).to eq('wait')

      auth_query_string = Rack::Utils.build_query({
        response_type: 'code',
        client_id:,
        redirect_uri:,
        scope: requested_scope,
        state:,
        aud: base_fhir_url,
        code_challenge: pkce_challenge,
        code_challenge_method: pkce_method
      })
      redirect_query_string = Rack::Utils.build_query({
        code: authorization_code_token,
        state:
      })
      create_authorization_request(auth_query_string, "#{redirect_uri}?#{redirect_query_string}")

      post_json(token_url, token_request_auth_code_body_sig_valid)
      expect(last_response.status).to eq(200)
      response_body = JSON.parse(last_response.body)
      expect(response_body['patient']).to eq('123')
    end

    it 'includes a refresh token when requested as a part of the scopes' do
      inputs = { client_id:, smart_jwk_set: jwks_valid, smart_redirect_uris: redirect_uri}
      result = run(app_launch_ca_reg_test, inputs)
      expect(result.result).to eq('pass')

      inputs = { client_id:}
      result = run(app_launch_ca_access_test, inputs)
      expect(result.result).to eq('wait')

      auth_query_string = Rack::Utils.build_query({
        response_type: 'code',
        client_id:,
        redirect_uri:,
        scope: requested_scope + ' offline_access',
        state:,
        aud: base_fhir_url,
        code_challenge: pkce_challenge,
        code_challenge_method: pkce_method
      })
      redirect_query_string = Rack::Utils.build_query({
        code: authorization_code_token,
        state:
      })
      create_authorization_request(auth_query_string, "#{redirect_uri}?#{redirect_query_string}")

      post_json(token_url, token_request_auth_code_body_sig_valid)
      expect(last_response.status).to eq(200)
      response_body = JSON.parse(last_response.body)
      refresh_token = response_body['refresh_token']
      expect(described_class.refresh_token_to_authorization_code(refresh_token)).to eq(authorization_code_token)
    end

    it 'provides a id_token when requested through scopes' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid, smart_redirect_uris: redirect_uri}
      result = run(app_launch_ca_reg_test, inputs)
      expect(result.result).to eq('pass')

      fhir_user_relative_reference = 'Patient/123'
      inputs = { client_id:, fhir_user_relative_reference: }
      result = run(app_launch_ca_access_test, inputs)
      expect(result.result).to eq('wait')

      auth_query_string = Rack::Utils.build_query({
        response_type: 'code',
        client_id:,
        redirect_uri:,
        scope: requested_scope + ' openid fhirUser',
        state:,
        aud: base_fhir_url,
        code_challenge: pkce_challenge,
        code_challenge_method: pkce_method
      })
      redirect_query_string = Rack::Utils.build_query({
        code: authorization_code_token,
        state:
      })
      create_authorization_request(auth_query_string, "#{redirect_uri}?#{redirect_query_string}")

      post_json(token_url, token_request_auth_code_body_sig_valid)
      expect(last_response.status).to eq(200)
      response_body = JSON.parse(last_response.body)
      expect(response_body['id_token']).to_not be_nil
      token_body, _token_header = JWT.decode(response_body['id_token'], nil, false)
      expect(token_body['aud']).to eq(client_id)
      expect(token_body['fhirUser']).to eq("#{client_fhir_base_url}/#{fhir_user_relative_reference}")
    end

  end

  describe 'when generating client_credential token responses for SMART' do
    it 'returns 401 when the signature is bad or cannot be verified' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
      
      inputs = { client_id:}
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      post_json(token_url, token_request_body_sig_invalid)
      expect(last_response.status).to eq(401)
      error_body = JSON.parse(last_response.body)
      expect(error_body['error']).to eq('invalid_client')
      expect(error_body['error_description']).to match(/Signature verification failed/)

      result = results_repo.find(result.id)
      expect(result.result).to eq('wait')
    end

    it 'returns 200 when the signature is correct even if header is bad' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
      
      inputs = { client_id:}
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      post_json(token_url, token_request_body_sig_valid)
      expect(last_response.status).to eq(200)

      result = results_repo.find(result.id)
      expect(result.result).to eq('wait')
    end
  end

  describe 'when generating refresh token responses for SMART' do
    it 'succeeds when request is valid' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
      
      inputs = { client_id:}
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      auth_query_string = Rack::Utils.build_query({
        response_type: 'code',
        client_id:,
        redirect_uri:,
        scope: requested_scope,
        state:,
        aud: base_fhir_url,
        code_challenge: pkce_challenge,
        code_challenge_method: pkce_method
      })
      redirect_query_string = Rack::Utils.build_query({
        code: "#{authorization_code_token}",
        state:
      })
      create_authorization_request(auth_query_string, "#{redirect_uri}?#{redirect_query_string}")

      post_json(token_url, token_request_refresh_body_sig_valid)
      expect(last_response.status).to eq(200)
    end

    it 'returns 401 when no corresponding authorization request' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
      
      inputs = { client_id:}
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      post_json(token_url, token_request_refresh_body_sig_valid)
      expect(last_response.status).to eq(401)
    end

    it 'returns 401 when the client assertion is invalid' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
      
      inputs = { client_id:}
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      post_json(token_url, token_request_refresh_body_sig_invalid)
      expect(last_response.status).to eq(401)
    end
  end

  describe 'when responding to access requests' do
    it 'returns 401 when the access token has expired' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
      
      inputs = { client_id:, echoed_fhir_response: access_response }
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      expired_token = Base64.strict_encode64({
        client_id:,
        expiration: 1,
        nonce: SecureRandom.hex(8)
      }.to_json)
      header('Authorization', "Bearer #{expired_token}")
      get(access_url)
      expect(last_response.status).to eq(401)

      result = results_repo.find(result.id)
      expect(result.result).to eq('wait')
    end

    it 'returns 200 when the access token has not expired' do
      # run reg test to save smart_jwk_set input
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
      
      inputs = { client_id:, echoed_fhir_response: access_response }
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      exp_timestamp = Time.now.to_i
      unexpired_token = Base64.strict_encode64({
        client_id:,
        expiration: exp_timestamp,
        nonce: SecureRandom.hex(8)
      }.to_json)
      allow(Time).to receive(:now).and_return(Time.at(exp_timestamp - 10))
      header('Authorization', "Bearer #{unexpired_token}")
      get(access_url)
      expect(last_response.status).to eq(200)

      result = results_repo.find(result.id)
      expect(result.result).to eq('wait')
    end

    it 'returns 200 when the decoded access token has no expiration' do
      inputs = { client_id:, smart_jwk_set: jwks_valid}
      result = run(backend_services_reg_test, inputs)
      expect(result.result).to eq('pass')
      
      inputs = { client_id:, echoed_fhir_response: access_response }
      result = run(backend_services_access_test, inputs)
      expect(result.result).to eq('wait')

      token_no_exp = Base64.strict_encode64({
        client_id:,
        nonce: SecureRandom.hex(8)
      }.to_json)
      header('Authorization', "Bearer #{token_no_exp}")
      get(access_url)
      expect(last_response.status).to eq(200)

      result = results_repo.find(result.id)
      expect(result.result).to eq('wait')
    end
  end
end
