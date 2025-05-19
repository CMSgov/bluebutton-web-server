require_relative '../../lib/smart_app_launch/standalone_launch_group_stu2'

RSpec.describe SMARTAppLaunch::StandaloneLaunchGroupSTU2, :request do
  let(:suite_id) { 'smart' }

  it 'has a properly configured auth input' do
    auth_input = described_class.available_inputs[:standalone_smart_auth_info]

    expect(auth_input).to be_present

    options = auth_input.options

    expect(options[:mode]).to eq('auth')

    components = options[:components]

    pkce_support_component = components.find { |component| component[:name] == :pkce_support }

    expect(pkce_support_component[:default]).to eq('enabled')
    expect(pkce_support_component[:locked]).to eq(true)

    pkce_challenge_component = components.find { |component| component[:name] == :pkce_code_challenge_method }

    expect(pkce_challenge_component[:default]).to eq('S256')
    expect(pkce_challenge_component[:locked]).to eq(true)

    requested_scopes_component = components.find { |component| component[:name] == :requested_scopes }

    expect(requested_scopes_component[:default]).to eq('launch/patient openid fhirUser offline_access patient/*.rs')

    auth_type_component = components.find { |component| component[:name] == :auth_type }

    expected_list_options = Inferno::DSL::AuthInfo.default_auth_type_component_without_backend_services[:options][:list_options]
    list_options = auth_type_component.dig(:options, :list_options)

    expect(list_options).to match_array(expected_list_options)
  end
end
