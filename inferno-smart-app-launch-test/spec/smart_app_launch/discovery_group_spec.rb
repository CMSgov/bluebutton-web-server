require_relative '../../lib/smart_app_launch/discovery_stu1_group'

RSpec.describe SMARTAppLaunch::DiscoverySTU1Group do
  let(:suite_id) { 'smart' }
  let(:group) { Inferno::Repositories::TestGroups.new.find('smart_discovery') }
  let(:url) { 'http://example.com/fhir' }
  let(:well_known_url) { 'http://example.com/fhir/.well-known/smart-configuration' }
  let(:well_known_config) do
    {
      'authorization_endpoint' => 'https://example.com/fhir/auth/authorize',
      'token_endpoint' => 'https://example.com/fhir/auth/token',
      'token_endpoint_auth_methods_supported' => ['client_secret_basic'],
      'registration_endpoint' => 'https://example.com/fhir/auth/register',
      'scopes_supported' =>
        ['openid', 'profile', 'launch', 'launch/patient', 'patient/*.*', 'user/*.*', 'offline_access'],
      'response_types_supported' => ['code', 'code id_token', 'id_token', 'refresh_token'],
      'management_endpoint' => 'https://example.com/fhir/user/manage',
      'introspection_endpoint' => 'https://example.com/fhir/user/introspect',
      'revocation_endpoint' => 'https://example.com/fhir/user/revoke',
      'capabilities' =>
        ['launch-ehr', 'client-public', 'client-confidential-symmetric', 'context-ehr-patient', 'sso-openid-connect'],
      'issuer' => 'https://example.com',
      'jwks_uri' => 'https://example.com/.well-known/jwks.json',
      'grant_types_supported' => ['authorization_code'],
      'code_challenge_methods_supported' => ['S256']
    }
  end

  describe 'capability statement test' do
    let(:runnable) { group.tests[2] }
    let(:minimal_capabilities) do
      FHIR::CapabilityStatement.new(
        fhirVersion: '4.0.1',
        rest: [
          {
            mode: 'server'
          }
        ]
      )
    end

    let(:full_extensions) do
      [
        {
          url: 'authorize',
          valueUri: "#{url}/authorize"
        },
        {
          url: 'introspect',
          valueUri: "#{url}/introspect"
        },
        {
          url: 'manage',
          valueUri: "#{url}/manage"
        },
        {
          url: 'register',
          valueUri: "#{url}/register"
        },
        {
          url: 'revoke',
          valueUri: "#{url}/revoke"
        },
        {
          url: 'token',
          valueUri: "#{url}/token"
        }
      ]
    end
    let(:full_capabilities) { capabilities_with_smart(full_extensions) }

    let(:relative_extensions) do
      [
        {
          url: 'authorize',
          valueUri: 'authorize'
        },
        {
          url: 'introspect',
          valueUri: '/introspect'
        },
        {
          url: 'manage',
          valueUri: "nested/manage"
        },
        {
          url: 'register',
          valueUri: "/nested/register"
        },
        {
          url: 'revoke',
          valueUri: "#{url}/revoke"
        },
        {
          url: 'token',
          valueUri: "http://foobar.quz/token"
        }
      ]
    end
    let(:relative_capabilities) { capabilities_with_smart(relative_extensions) }

    def capabilities_with_smart(extensions)
      FHIR::CapabilityStatement.new(
        fhirVersion: '4.0.1',
        rest: [
          security: {
            service: [
              {
                coding: [
                  {
                    system: 'http://hl7.org/fhir/restful-security-service',
                    code: 'SMART-on-FHIR'
                  }
                ]
              }
            ],
            extension: [
              {
                url: 'http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris',
                extension: extensions
              }
            ]
          }
        ]
      )
    end

    it 'passes when all required extensions are present' do
      stub_request(:get, "#{url}/metadata")
        .to_return(status: 200, body: full_capabilities.to_json)

      result = run(runnable, url: url)

      expect(result.result).to eq('pass')
    end

    it 'passes when all required extensions are present with relative URLs' do
      stub_request(:get, "#{url}/metadata")
        .to_return(status: 200, body: relative_capabilities.to_json)

      result = run(runnable, url: url)

      expect(result.result).to eq('pass')
    end

    it 'converts relative URLs to absolute URLs' do
      stub_request(:get, "#{url}/metadata")
        .to_return(status: 200, body: relative_capabilities.to_json)

      run(runnable, url: url)

      expected_outputs = {
        capability_authorization_url: 'http://example.com/fhir/authorize',
        capability_introspection_url: 'http://example.com/introspect',
        capability_management_url: 'http://example.com/fhir/nested/manage',
        capability_registration_url: 'http://example.com/nested/register',
        capability_revocation_url: 'http://example.com/fhir/revoke',
        capability_token_url: 'http://foobar.quz/token'
      }

      expected_outputs.each do |name, value|
        expect(session_data_repo.load(test_session_id: test_session.id, name: name)).to eq(value.to_s)
      end
    end

    it 'fails when a non-200 response is received' do
      stub_request(:get, "#{url}/metadata")
        .to_return(status: 500, body: minimal_capabilities.to_json)

      result = run(runnable, url: url)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/Unexpected response status/)
    end

    it 'fails when no SMART extensions are returned' do
      stub_request(:get, "#{url}/metadata")
        .to_return(status: 200, body: minimal_capabilities.to_json)

      result = run(runnable, url: url)

      expect(result.result).to eq('fail')
      expect(result.result_message).to eq('No SMART extensions found in CapabilityStatement')
    end

    it 'fails when no authorize extension is returned' do
      extensions = full_extensions.reject { |extension| extension[:url] == 'authorize' }
      stub_request(:get, "#{url}/metadata")
        .to_return(status: 200, body: capabilities_with_smart(extensions).to_json)

      result = run(runnable, url: url)

      expect(result.result).to eq('fail')
      expect(result.result_message).to eq('No `authorize` extension found')
    end

    it 'fails when no token extension is returned' do
      extensions = full_extensions.reject { |extension| extension[:url] == 'token' }
      stub_request(:get, "#{url}/metadata")
        .to_return(status: 200, body: capabilities_with_smart(extensions).to_json)

      result = run(runnable, url: url)

      expect(result.result).to eq('fail')
      expect(result.result_message).to eq('No `token` extension found')
    end
  end

  describe 'endpoints match test' do
    let(:runnable) { group.tests[3] }
    let(:full_inputs) do
      [
        'authorization',
        'token',
        'introspection',
        'management',
        'registration',
        'revocation'
      ].each_with_object({}) do |type, inputs|
        inputs["well_known_#{type}_url".to_sym] = "#{type.upcase}_URL"
        inputs["capability_#{type}_url".to_sym] = "#{type.upcase}_URL"
      end
    end

    it 'passes if all urls match' do
      result = run(runnable, full_inputs)

      expect(result.result).to eq('pass')
    end

    it 'fails if a url does not match' do
      full_inputs[:well_known_introspection_url] = 'abc'
      result = run(runnable, full_inputs)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/The following urls do not match:\n- Introspection/)
      expect(result.result_message).to include(full_inputs[:well_known_introspection_url])
      expect(result.result_message).to include(full_inputs[:capability_introspection_url])
    end
  end
end
