RSpec.describe SMARTAppLaunch::SMARTClientAccessAppLaunchConfidentialSymmetricInteraction, :request do # rubocop:disable RSpec/SpecFilePathFormat
  let(:suite_id) { 'smart_client_stu2_2' }

  describe 'during the acess wait test' do
    let(:static_uuid) { 'f015a331-3a86-4566-b72f-b5b85902cdca' }
    let(:test) { described_class }
    let(:alcs_reg_test) { suite.children[1].children[0] } # app launch confidential symmetric reg test
    let(:test_session) do # overriden to add suite options
      repo_create(
        :test_session,
        suite: suite_id,
        suite_options: [Inferno::DSL::SuiteOption.new(
          id: :client_type,
          value: SMARTAppLaunch::SMARTClientOptions::SMART_APP_LAUNCH_CONFIDENTIAL_SYMMETRIC
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
    let(:token_endpoint) { 'https://inferno.healthit.gov/suites/custom/smart_client_stu2_2/auth/token' }
    let(:authorization_url) { "/custom/#{suite_id}#{SMARTAppLaunch::AUTHORIZATION_PATH}" }
    let(:authorization_code_token) { described_class.client_id_to_token(client_id, 10) }
    let(:client_id) { 'test_client' }
    let(:smart_client_secret) { 'secret' }
    let(:redirect_uri) { "https://inferno.healthit.gov/redirect"}
    let(:token_request_body_valid) do
      { grant_type: 'authorization_code',
        scope: 'system/*.rs'
      }
    end

    describe 'it responds to token requests' do
      it 'it succeeds when providing the client secret' do
        
        # run reg test to save smart_jwk_set input
        inputs = { client_id:, smart_client_secret:, smart_redirect_uris: redirect_uri}
        result = run(alcs_reg_test, inputs)
        expect(result.result).to eq('pass')
        
        inputs = { client_id:}
        result = run(test, inputs)
        expect(result.result).to eq('wait')

        query_string = Rack::Utils.build_query({client_id: , redirect_uri: })
        get("#{authorization_url}?#{query_string}")
        expect(last_response.status).to eq(302)
        token_request_body_valid['code'] = 
          Rack::Utils.parse_query(URI.parse(last_response.headers['Location']).query)['code']

        header('Authorization', "Basic #{Base64.strict_encode64("#{client_id}:#{smart_client_secret}")}")
        post(token_url, URI.encode_www_form(token_request_body_valid))
        expect(last_response.status).to be(200)
      end

      it 'it fails when the basic header is bad' do
        
        # run reg test to save smart_jwk_set input
        inputs = { client_id:, smart_client_secret:, smart_redirect_uris: redirect_uri}
        result = run(alcs_reg_test, inputs)
        expect(result.result).to eq('pass')
        
        inputs = { client_id:}
        result = run(test, inputs)
        expect(result.result).to eq('wait')

        query_string = Rack::Utils.build_query({client_id: , redirect_uri: })
        get("#{authorization_url}?#{query_string}")
        expect(last_response.status).to eq(302)
        token_request_body_valid['code'] = 
          Rack::Utils.parse_query(URI.parse(last_response.headers['Location']).query)['code']

        header('Authorization', "Basic bad")
        post(token_url, URI.encode_www_form(token_request_body_valid))
        expect(last_response.status).to be(401)
      end

      it 'it fails when no basic auth header' do
        
        # run reg test to save smart_jwk_set input
        inputs = { client_id:, smart_client_secret:, smart_redirect_uris: redirect_uri}
        result = run(alcs_reg_test, inputs)
        expect(result.result).to eq('pass')
        
        inputs = { client_id:}
        result = run(test, inputs)
        expect(result.result).to eq('wait')

        query_string = Rack::Utils.build_query({client_id: , redirect_uri: })
        get("#{authorization_url}?#{query_string}")
        expect(last_response.status).to eq(302)
        token_request_body_valid['code'] = 
          Rack::Utils.parse_query(URI.parse(last_response.headers['Location']).query)['code']

        post(token_url, URI.encode_www_form(token_request_body_valid))
        expect(last_response.status).to be(401)
      end

    end

    describe 'it responds to access requests' do
      it 'returns the tester-provided response' do
        # run reg test to save smart_jwk_set input
        inputs = { client_id:, smart_client_secret:, smart_redirect_uris: redirect_uri}
        result = run(alcs_reg_test, inputs)
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
        inputs = { client_id:, smart_client_secret:, smart_redirect_uris: redirect_uri}
        result = run(alcs_reg_test, inputs)
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
        inputs = { client_id:, smart_client_secret:, smart_redirect_uris: redirect_uri}
        result = run(alcs_reg_test, inputs)
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
