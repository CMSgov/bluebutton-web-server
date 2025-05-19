RSpec.describe SMARTAppLaunch::SMARTClientAccessBackendServicesConfidentialAsymmetricInteraction, :request do # rubocop:disable RSpec/SpecFilePathFormat
  let(:suite_id) { 'smart_client_stu2_2' }

  describe 'during the acess wait test' do
    let(:static_uuid) { 'f015a331-3a86-4566-b72f-b5b85902cdca' }
    let(:test) { described_class }
    let(:backend_services_reg_test) { suite.children[3].children[0] } # backend services reg test
    let(:test_session) do # overriden to add suite options
      repo_create(
        :test_session,
        suite: suite_id,
        suite_options: [Inferno::DSL::SuiteOption.new(
          id: :client_type,
          value: SMARTAppLaunch::SMARTClientOptions::SMART_BACKEND_SERVICES_CONFIDENTIAL_ASYMMETRIC
        )]
      )
    end
    let(:results_repo) { Inferno::Repositories::Results.new }
    let(:requests_repo) { Inferno::Repositories::Requests.new }
    let(:patient_id) { '999' }
    let(:patient_read_url) { "/custom/#{suite_id}/fhir/Patient/#{patient_id}" }
    let(:patient_read_response) { %({ "resourceType": "Patient", "id": "#{patient_id}" }) }
    let(:fhir_read_resources_bundle) do
      %({ "resourceType": "Bundle", "entry": [ { "resource": #{patient_read_response} } ] })
    end
    let(:token_url) { "/custom/#{suite_id}#{SMARTAppLaunch::TOKEN_PATH}" }
    let(:jwks_valid) do
      File.read(File.join(__dir__, '..', '..', '..', 'lib', 'smart_app_launch', 'smart_jwks.json'))
    end
    let(:parsed_jwks) { JWT::JWK::Set.new(JSON.parse(jwks_valid)) }
    let(:jwks_url_valid) { 'https://inferno.healthit.gov/suites/custom/smart_stu2/.well-known/jwks.json' }
    let(:token_endpoint) { 'https://inferno.healthit.gov/suites/custom/smart_client_stu2_2/auth/token' }
    let(:client_id) { 'test_client' }
    let(:header_valid) do
      {
        typ: 'JWT',
        alg: 'RS384',
        kid: 'b41528b6f37a9500edb8a905a595bdd7'
      }
    end
    let(:payload_valid) do
      {
        iss: client_id,
        sub: client_id,
        aud: token_endpoint,
        exp: 1741398050,
        jti: 'random-non-reusable-jwt-id-123'
      }
    end
    let(:client_assertion_valid) { make_jwt(payload_valid, header_valid, 'RS384', parsed_jwks.keys[3]) }
    let(:token_request_body_valid) do
      { grant_type: 'client_credentials',
        scope: 'system/*.rs',
        client_assertion_type: 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        client_assertion: client_assertion_valid }
    end

    let(:token_request_body_invalid) do
      { grant_type: 'client_credentials',
        scope: 'system/*.rs',
        client_assertion_type: 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        client_assertion: "#{client_assertion_valid}badsig" }
    end

    def make_jwt(payload, header, alg, jwk)
      token = JWT::Token.new(payload:, header:)
      token.sign!(algorithm: alg, key: jwk.signing_key)
      token.jwt
    end

    describe 'it responds to token requests' do
      describe 'it succeeds' do
        it 'when using a provided jwks url' do
          stub_request(:get, jwks_url_valid)
            .to_return(status: 200, body: jwks_valid)
          
          # run reg test to save smart_jwk_set input
          inputs = { client_id:, smart_jwk_set: jwks_url_valid}
          result = run(backend_services_reg_test, inputs)
          expect(result.result).to eq('pass')
          
          inputs = { client_id:}
          result = run(test, inputs)
          expect(result.result).to eq('wait')

          post(token_url, URI.encode_www_form(token_request_body_valid))

          expect(last_response.status).to be(200)
        end

        it 'when using provided raw jwks json' do
          # run reg test to save smart_jwk_set input
          inputs = { client_id:, smart_jwk_set: jwks_valid}
          result = run(backend_services_reg_test, inputs)
          expect(result.result).to eq('pass')
          
          inputs = { client_id:}
          result = run(test, inputs)
          expect(result.result).to eq('wait')

          post(token_url, URI.encode_www_form(token_request_body_valid))

          expect(last_response.status).to be(200)
        end
      end

      describe 'it fails' do
        it 'with 500 when no client assertion' do
          # run reg test to save smart_jwk_set input
          inputs = { client_id:, smart_jwk_set: jwks_valid}
          result = run(backend_services_reg_test, inputs)
          expect(result.result).to eq('pass')
          
          inputs = { client_id:}
          result = run(test, inputs)
          expect(result.result).to eq('wait')

          token_request_body_valid['client_assertion'] = nil
          post(token_url, URI.encode_www_form(token_request_body_valid))
          
          expect(last_response.status).to be(500)
        end

        it 'with 401 when client assertion has a bad signature' do
          # run reg test to save smart_jwk_set input
          inputs = { client_id:, smart_jwk_set: jwks_valid}
          result = run(backend_services_reg_test, inputs)
          expect(result.result).to eq('pass')
          
          inputs = { client_id:}
          result = run(test, inputs)
          expect(result.result).to eq('wait')

          post(token_url, URI.encode_www_form(token_request_body_invalid))
          
          expect(last_response.status).to be(401)
        end
      end
    end

    describe 'it responds to access requests' do
      it 'returns the tester-provided response' do
        # run reg test to save smart_jwk_set input
        inputs = { client_id:, smart_jwk_set: jwks_valid}
        result = run(backend_services_reg_test, inputs)
        expect(result.result).to eq('pass')
        
        inputs = { client_id:, echoed_fhir_response: patient_read_response }
        result = run(test, inputs)
        expect(result.result).to eq('wait')

        header('Authorization', "Bearer #{Base64.urlsafe_encode64({ client_id: client_id }.to_json, padding: false)}")
        get(patient_read_url)

        expect(last_response.status).to be(200)
        expect(last_response.body).to eq(patient_read_response)
      end

      it 'returns a resource from the tester-provided Bundle on a read' do
        # run reg test to save smart_jwk_set input
        inputs = { client_id:, smart_jwk_set: jwks_valid}
        result = run(backend_services_reg_test, inputs)
        expect(result.result).to eq('pass')

        inputs = { client_id:, fhir_read_resources_bundle:}
        result = run(test, inputs)
        expect(result.result).to eq('wait')

        header('Authorization', "Bearer #{Base64.urlsafe_encode64({ client_id: client_id }.to_json, padding: false)}")
        get(patient_read_url)

        expect(last_response.status).to be(200)
        expect(last_response.body).to match(/999/)
      end

      it 'returns an operaion outcome when no tester-provided response' do
        # run reg test to save smart_jwk_set input
        inputs = { client_id:, smart_jwk_set: jwks_valid}
        result = run(backend_services_reg_test, inputs)
        expect(result.result).to eq('pass')

        inputs = { client_id:}
        result = run(test, inputs)
        expect(result.result).to eq('wait')

        header('Authorization', "Bearer #{Base64.urlsafe_encode64({ client_id: client_id }.to_json, padding: false)}")
        get(patient_read_url)

        expect(last_response.status).to be(400)
        expect(FHIR.from_contents(last_response.body)).to be_a(FHIR::OperationOutcome)
      end
    end
  end
end
