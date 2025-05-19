require_relative '../../lib/smart_app_launch/smart_access_brands_retrieve_bundle_test'

RSpec.describe SMARTAppLaunch::SMARTAccessBrandsValidateEndpoints do
  let(:suite_id) { 'smart_access_brands' }
  let(:results_repo) { Inferno::Repositories::Results.new }
  let(:result) { repo_create(:result, test_session_id: test_session.id) }

  let(:smart_access_brands_bundle) do
    JSON.parse(File.read(File.join(
                           __dir__, '..', 'fixtures', 'smart_access_brands_example.json'
                         )))
  end

  let(:operation_outcome_success) do
    {
      outcomes: [{
        issues: []
      }],
      sessionId: 'b8cf5547-1dc7-4714-a797-dc2347b93fe2'
    }
  end

  let(:operation_outcome_failure) do
    {
      outcomes: [{
        issues: [{
          level: 'ERROR',
          message: 'Resource does not conform to profile'
        }]
      }],
      sessionId: 'b8cf5547-1dc7-4714-a797-dc2347b93fe2'
    }
  end

  let(:validator_url) { ENV.fetch('FHIR_RESOURCE_VALIDATOR_URL') }
  let(:user_access_brands_publication_url) { 'http://fhirserver.org/smart_access_brands_example.json' }

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

  describe 'SMART Access Brands Validate Endpoints Test' do
    let(:test) do
      Class.new(SMARTAppLaunch::SMARTAccessBrandsValidateEndpoints) do
        fhir_resource_validator do
          url ENV.fetch('FHIR_RESOURCE_VALIDATOR_URL')

          cli_context do
            txServer nil
            displayWarnings true
            disableDefaultResourceFetcher true
          end

          igs('hl7.fhir.uv.smart-app-launch#2.2.0')
        end
      end
    end

    it 'passes if User Access Brands Bundle contains valid Endpoints' do
      validation_request = stub_request(:post, "#{validator_url}/validate")
        .to_return(status: 200, body: operation_outcome_success.to_json)

      result = run(test, user_access_brands_bundle: smart_access_brands_bundle.to_json)

      expect(result.result).to eq('pass')
      expect(validation_request).to have_been_made.times(2)
    end

    it 'passes if inputted User Access Brands Bundle contains valid Endpoints' do
      validation_request = stub_request(:post, "#{validator_url}/validate")
        .to_return(status: 200, body: operation_outcome_success.to_json)

      create_user_access_brands_request(body: smart_access_brands_bundle)

      result = run(test)

      expect(result.result).to eq('pass')
      expect(validation_request).to have_been_made.times(2)
    end

    it 'skips if no User Access Brands Bundle requests were made' do
      result = run(test)

      expect(result.result).to eq('skip')
      expect(result.result_message).to match(
        'No User Access Brands request was made in the previous test, and no User Access Brands Bundle was provided'
      )
    end

    it 'skips if User Access Brands Bundle request does not contain a response body' do
      create_user_access_brands_request
      result = run(test)

      expect(result.result).to eq('skip')
      expect(result.result_message).to eq('No SMART Access Brands Bundle contained in the response')
    end

    it 'fails if User Access Brands Bundle is an invalid JSON' do
      create_user_access_brands_request(body: '[[')

      result = run(test)

      expect(result.result).to eq('fail')
      expect(result.result_message).to eq('Invalid JSON. ')
    end

    it 'skips if User Access Brands Bundle is empty' do
      smart_access_brands_bundle['entry'] = []
      create_user_access_brands_request(body: smart_access_brands_bundle)
      result = run(test)

      expect(result.result).to eq('skip')
      expect(result.result_message).to eq('The given Bundle does not contain any resources')
    end

    it "fails if the User Access Brands Bundle's contained Endpoints fail validation" do
      validation_request = stub_request(:post, "#{validator_url}/validate")
        .to_return(status: 200, body: operation_outcome_failure.to_json)

      create_user_access_brands_request(body: smart_access_brands_bundle)

      result = run(test)

      expect(result.result).to eq('fail')
      expect(result.result_message).to eq(
        'The following bundle entries are invalid: Endpoint#examplehospital-ehr1, Endpoint#examplehospital-ehr2'
      )
      expect(validation_request).to have_been_made.times(2)
    end

    it 'fails if Endpoint is not referenced by any Brands found in Bundle' do
      validation_request = stub_request(:post, "#{validator_url}/validate")
        .to_return(status: 200, body: operation_outcome_success.to_json)

      smart_access_brands_bundle['entry'].first['resource']['endpoint'].delete_at(1)
      create_user_access_brands_request(body: smart_access_brands_bundle)

      result = run(test)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(
        'Endpoint with id: examplehospital-ehr2 does not have any associated Organizations in the Bundle'
      )
      expect(validation_request).to have_been_made.times(2)
    end
  end
end
