require_relative '../../lib/smart_app_launch/backend_services_authorization_request_builder'

RSpec.describe SMARTAppLaunch::BackendServicesAuthorizationRequestBuilder do
  let(:encryption_method) { 'RS384' }
  let(:scope) { 'system/*' }
  let(:iss) { 'ISS'}
  let(:sub) { 'SUB' }
  let(:aud) { 'AUD' }
  let(:kid) { nil }

  describe '.build' do
    context 'when using default argument values' do
      it 'creates a valid request query' do
        request_query = described_class.build(encryption_method: encryption_method,
                                                scope: scope,
                                                iss: iss,
                                                sub: sub,
                                                aud: aud
                                                )

        request_body = Rack::Utils.parse_nested_query(request_query[:body])
        request_headers = request_query[:headers]

        expect(request_body['client_assertion']).to be_present
        expect(request_body['client_assertion_type']).to eq('urn:ietf:params:oauth:client-assertion-type:jwt-bearer')
        expect(request_body['grant_type']).to eq('client_credentials')
        expect(request_body['scope']).to eq(scope)

        expect(request_headers[:content_type]).to eq('application/x-www-form-urlencoded')
        expect(request_headers[:accept]).to eq('application/json')
      end
    end

    context 'when specifying non-default argument values' do 
      it 'creates request query that uses provided values' do 
        
        specific_content_type = 'specifc_content_type'
        specific_grant_type = 'specific_grant_type'
        specific_client_assertion_type = 'specific_client_assertion_type'
        
        request_query = described_class.build(encryption_method: encryption_method,
                                                scope: scope,
                                                iss: iss,
                                                sub: sub,
                                                aud: aud,
                                                content_type: specific_content_type,
                                                grant_type: specific_grant_type,
                                                client_assertion_type: specific_client_assertion_type
                                                )

        request_body = Rack::Utils.parse_nested_query(request_query[:body])
        request_headers = request_query[:headers]

        expect(request_body['client_assertion']).to be_present
        expect(request_body['client_assertion_type']).to eq(specific_client_assertion_type)
        expect(request_body['grant_type']).to eq(specific_grant_type)
        expect(request_body['scope']).to eq(scope)

        expect(request_headers[:content_type]).to eq(specific_content_type)
        expect(request_headers[:accept]).to eq('application/json')
      end 
    end
  end
end