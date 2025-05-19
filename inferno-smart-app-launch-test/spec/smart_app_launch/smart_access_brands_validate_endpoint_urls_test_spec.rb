require_relative '../../lib/smart_app_launch/smart_access_brands_retrieve_bundle_test'

RSpec.describe SMARTAppLaunch::SMARTAccessBrandsValidateEndpointURLs do
  let(:suite_id) { 'smart_access_brands' }
  let(:results_repo) { Inferno::Repositories::Results.new }
  let(:result) { repo_create(:result, test_session_id: test_session.id) }

  let(:smart_access_brands_bundle) do
    JSON.parse(File.read(File.join(
                           __dir__, '..', 'fixtures', 'smart_access_brands_example.json'
                         )))
  end

  let(:capability_statement) do
    JSON.parse(File.read(File.join(
                           __dir__, '..', 'fixtures', 'r4_capability_statement.json'
                         )))
  end

  let(:user_access_brands_publication_url) { 'http://fhirserver.org/smart_access_brands_example.json' }
  let(:base_url) { 'http://example.com/api/FHIR/R4' }

  def create_user_access_brands_request(url: user_access_brands_publication_url, body: nil, status: 200)
    repo_create(
      :request,
      name: 'retrieve_smart_access_brands_bundle',
      direction: 'outgoing',
      url:,
      result:,
      test_session_id: test_session.id,
      response_body: body.is_a?(Hash) ? body.to_json : body,
      status:,
      tags: ['smart_access_brands_bundle']
    )
  end

  def entity_result_message(runnable)
    results_repo.current_results_for_test_session_and_runnables(test_session.id, [runnable])
      .first
      .messages
      .map(&:message)
      .join(' ')
  end

  def entity_result_message_type(runnable)
    results_repo.current_results_for_test_session_and_runnables(test_session.id, [runnable])
      .first
      .messages
      .map(&:type)
      .first
  end

  describe 'SMART Access Brands Validate Endpoints URLs Test' do
    let(:test) do
      Class.new(SMARTAppLaunch::SMARTAccessBrandsValidateEndpointURLs) do
        http_client do
          url :user_access_brands_publication_url
          headers Accept: 'application/json, application/fhir+json'
        end

        input :user_access_brands_publication_url
      end
    end

    it 'passes if all Endpoints in Bundle contain valid URLs that return successful capability statements' do
      uri_template = Addressable::Template.new "#{base_url}/{id}/metadata"
      capability_statement_request = stub_request(:get, uri_template)
        .to_return(status: 200, body: capability_statement.to_json, headers: {})

      create_user_access_brands_request(body: smart_access_brands_bundle)

      result = run(test, user_access_brands_publication_url:, endpoint_availability_success_rate: 'all')

      expect(result.result).to eq('pass')
      expect(capability_statement_request).to have_been_made.times(2)
    end

    it 'fails if Endpoint in Bundle contains an invalid URLs' do
      smart_access_brands_bundle['entry'][1]['resource']['address'] = 'invalid_url'

      create_user_access_brands_request(body: smart_access_brands_bundle)

      result = run(test, user_access_brands_publication_url:, endpoint_availability_success_rate: 'all')

      expect(result.result).to eq('fail')
      expect(result.result_message).to eq('"invalid_url" is not a valid URI')
    end

    it 'fails if Endpoints in Bundle contain URLs that do not return a successful capability statement' do
      uri_template = Addressable::Template.new "#{base_url}/{id}/metadata"
      capability_statement_request = stub_request(:get, uri_template)
        .to_return(status: 404, body: capability_statement.to_json, headers: {})

      create_user_access_brands_request(body: smart_access_brands_bundle)

      result = run(test, user_access_brands_publication_url:, endpoint_availability_success_rate: 'all')

      expect(result.result).to eq('fail')
      expect(result.result_message).to eq('Unexpected response status: expected 200, but received 404')
      expect(capability_statement_request).to have_been_made
    end

    it 'fails if Endpoints in Bundle contain URLs that do not return a FHIR resource' do
      uri_template = Addressable::Template.new "#{base_url}/{id}/metadata"
      capability_statement_request = stub_request(:get, uri_template)
        .to_return(status: 200, body: { 'example' => 'example' }.to_json, headers: {})

      create_user_access_brands_request(body: smart_access_brands_bundle)

      result = run(test, user_access_brands_publication_url:, endpoint_availability_success_rate: 'all')

      expect(result.result).to eq('fail')
      expect(result.result_message).to eq('The content received does not appear to be a valid FHIR resource')
      expect(capability_statement_request).to have_been_made
    end

    it 'fails if Endpoint in Bundle contain URLs returns non capability statement' do
      capability_statement['resourceType'] = 'Patient'
      uri_template = Addressable::Template.new "#{base_url}/{id}/metadata"
      capability_statement_request = stub_request(:get, uri_template)
        .to_return(status: 200, body: capability_statement.to_json, headers: {})

      create_user_access_brands_request(body: smart_access_brands_bundle)

      result = run(test, user_access_brands_publication_url:, endpoint_availability_success_rate: 'all')

      expect(result.result).to eq('fail')
      expect(result.result_message).to eq(
        'Unexpected resource type: expected CapabilityStatement, but received Patient'
      )
      expect(capability_statement_request).to have_been_made
    end

    it 'passes and only checks the availability of number of endpoints equal to the endpoint availability limit' do
      uri_template = Addressable::Template.new "#{base_url}/{id}/metadata"
      capability_statement_request = stub_request(:get, uri_template)
        .to_return(status: 200, body: capability_statement.to_json, headers: {})

      create_user_access_brands_request(body: smart_access_brands_bundle)

      result = run(test, user_access_brands_publication_url:, endpoint_availability_success_rate: 'all',
                         endpoint_availability_limit: 1)

      expect(result.result).to eq('pass')
      expect(capability_statement_request).to have_been_made
    end

    it 'passes if at least 1 endpoint is available when success rate input is set to at least 1' do
      smart_access_brands_bundle['entry'][1]['resource']['address'] = "#{base_url}/fake/address/1"

      uri_template = Addressable::Template.new "#{base_url}/{id}/metadata"
      capability_statement_request_success = stub_request(:get, uri_template)
        .to_return(status: 200, body: capability_statement.to_json, headers: {})

      fake_uri_template = Addressable::Template.new "#{base_url}/fake/address/{id}/metadata"
      capability_statement_request_fail = stub_request(:get, fake_uri_template)
        .to_return(status: 404, body: '', headers: {})

      create_user_access_brands_request(body: smart_access_brands_bundle)

      result = run(test, user_access_brands_publication_url:, endpoint_availability_success_rate: 'at_least_1')

      expect(result.result).to eq('pass')
      expect(entity_result_message(test)).to match('Unexpected response status: expected 200, but received 404')
      expect(entity_result_message_type(test)).to eq('warning')
      expect(capability_statement_request_success).to have_been_made
      expect(capability_statement_request_fail).to have_been_made
    end

    it 'passes and does not retrieve any capability statements if success rate input set to none' do
      uri_template = Addressable::Template.new "#{base_url}/{id}/metadata"
      capability_statement_request = stub_request(:get, uri_template)
        .to_return(status: 200, body: capability_statement.to_json, headers: {})

      create_user_access_brands_request(body: smart_access_brands_bundle)

      result = run(test, user_access_brands_publication_url:, endpoint_availability_success_rate: 'none')

      expect(result.result).to eq('pass')
      expect(capability_statement_request).to have_been_made.times(0)
    end
  end
end
