require_relative 'lib/smart_app_launch/version'

Gem::Specification.new do |spec|
  spec.name          = 'smart_app_launch_test_kit'
  spec.version       = SMARTAppLaunch::VERSION
  spec.authors       = ['Stephen MacVicar']
  spec.email         = ['inferno@groups.mitre.org']
  spec.summary       = 'Inferno Tests for the SMART Application Launch Framework Implementation Guide'
  spec.description   = 'Inferno Tests for the SMART Application Launch Framework Implementation Guide'
  spec.homepage      = 'https://github.com/inferno-framework/smart-app-launch-test-kit'
  spec.license       = 'Apache-2.0'
  spec.add_runtime_dependency 'inferno_core', '>= 0.6.3'
  spec.add_runtime_dependency 'json-jwt', '~> 1.15.3'
  spec.add_runtime_dependency 'jwt', '~> 2.6'
  spec.add_runtime_dependency 'tls_test_kit', '~> 0.3.0'
  spec.add_development_dependency 'database_cleaner-sequel', '~> 1.8'
  spec.add_development_dependency 'factory_bot', '~> 6.1'
  spec.add_development_dependency 'rack-test', '~> 1.1.0'
  spec.add_development_dependency 'rspec', '~> 3.10'
  spec.add_development_dependency 'webmock', '~> 3.11'
  spec.required_ruby_version = Gem::Requirement.new('>= 3.3.6')
  spec.metadata['inferno_test_kit'] = 'true'
  spec.metadata['homepage_uri'] = spec.homepage
  spec.metadata['source_code_uri'] = 'https://github.com/inferno-framework/smart-app-launch-test-kit'
  spec.files = `[ -d .git ] && git ls-files -z lib config/presets LICENSE`.split("\x0")

  spec.require_paths = ['lib']
end
