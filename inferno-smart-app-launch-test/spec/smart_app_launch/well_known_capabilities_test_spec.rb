require_relative '../../lib/smart_app_launch/well_known_capabilities_stu1_test'
require_relative '../../lib/smart_app_launch/well_known_capabilities_stu2_test'

RSpec.describe "Well-Known Tests" do
  let(:test_v1) { Inferno::Repositories::Tests.new.find('well_known_capabilities_stu1') }
  let(:test_v2) { Inferno::Repositories::Tests.new.find('well_known_capabilities_stu2') }
  let(:suite_id) { 'smart'}
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

  shared_examples 'well-known tests' do |required_fields|
    it 'passes when the well-known configuration contains all required fields' do
      result = run(runnable, well_known_configuration: valid_config.to_json)

      expect(result.result).to eq('pass')
    end

    required_fields.each_key do |field|
      it 'fails if a required field is missing' do
        valid_config.reject! { |key, _| key == field }
        result = run(runnable, well_known_configuration: valid_config.to_json)

        expect(result.result).to eq('fail')
        expect(result.result_message).to eq("Well-known configuration does not include `#{field}`")
      end
    end

    required_fields.each_key do |field|
      it "fails if required field `#{field}` is blank" do
        valid_config[field] = ''
        result = run(runnable, well_known_configuration: valid_config.to_json)

        expect(result.result).to eq('fail')
        expect(result.result_message).to eq("Well-known configuration field `#{field}` is blank")
      end
    end

    required_fields.each do |field, type|
      it "fails if a required field `#{field}` is the wrong type" do
        valid_config[field] = 1

        result = run(runnable, well_known_configuration: valid_config.to_json)

        expect(result.result).to eq('fail')
        expect(result.result_message).to match(/must be type: #{type.to_s.downcase}/)
      end
    end

    it 'fails if the capabilities field contains a non-string entry' do
      valid_config['capabilities'].concat [1, nil]
      result = run(runnable, well_known_configuration: valid_config.to_json)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/must be an array of strings/)
      expect(result.result_message).to match(/`1`/)
      expect(result.result_message).to match(/`nil`/)
    end
  end

  describe SMARTAppLaunch::WellKnownCapabilitiesSTU1Test do
    stu1_required_fields = {
        'authorization_endpoint' => String,
        'token_endpoint' => String,
        'capabilities' => Array
    }
    let(:runnable) { test_v1 }
    let(:valid_config) { well_known_config.slice(*stu1_required_fields.keys) }

    it_behaves_like 'well-known tests', stu1_required_fields
  end

  describe SMARTAppLaunch::WellKnownCapabilitiesSTU2Test do
    stu2_required_fields = {
        'authorization_endpoint' => String,
        'token_endpoint' => String,
        'capabilities' => Array,
        'grant_types_supported' => Array,
        'code_challenge_methods_supported' => Array
    }

    let(:runnable) { test_v2 }
    let(:valid_config) { well_known_config.slice(*stu2_required_fields.keys, 'issuer', 'jwks_uri') }

    it_behaves_like 'well-known tests', stu2_required_fields

    it 'fails if `issuer` is missing while `sso-openid-connect` is listed as a capability' do
      valid_config.delete('issuer')
      result = run(runnable, well_known_configuration: valid_config.to_json)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match('Well-known `issuer` field must be a string and present when server capabilities includes `sso-openid-connect`')
    end

    it 'fails if `jwks_uri` is missing while `sso-openid-connect` is listed as a capability' do
      valid_config.delete('jwks_uri')
      result = run(runnable, well_known_configuration: valid_config.to_json)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match('Well-known `jwks_uri` field must be a string and present when server capabilites includes `sso-openid-coneect`')
    end

    it 'warns if `issuer` is present while `sso-openid-connect` is not listed as a capability' do
      valid_config['capabilities'].reject! { |capability| capability == 'sso-openid-connect' }
      result = run(runnable, well_known_configuration: valid_config.to_json)
      expect(result.result).to eq('pass')
      warning_messages = Inferno::Repositories::Messages.new.messages_for_result(result.id).filter { |message| message.type == 'warning' }
      expect(warning_messages.any? { |wm| wm.message.include? 'Well-known `issuer` is omitted when server capabilites does not include `sso-openid-connect`'}).to be_truthy
    end
  end
end
