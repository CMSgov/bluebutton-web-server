# 0.6.3
* Fix typos and presets by @karlnaden in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/101
* FI-3973: decouple client credentials tokens from suite options by @karlnaden in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/102

# 0.6.2
* FI-3981 - Client authorization code tests by @karlnaden in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/96
* FI-3912: Update readme for AuthInfo by @Jammjammjamm in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/98
* FI-4013: Allow 401 in invalid client responses in backend services by @Jammjammjamm in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/99

# 0.6.1
* Fix SMART Auth Input for Token Introspection Response Group by @emichaud998 in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/92
* FI-3905: Backend Services Token Introspection Support by @emichaud998 in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/93
* FI-3825 - client suite for backend services by @karlnaden in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/94

# 0.6.0
* **Breaking Change**: FI 3093: Transition to use auth info by @vanessuniq in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/84 As a
  result of this change, any test kits which rely on the SMART App Launch Test
  Kit will need to be updated to use AuthInfo rather than OAuthCredentials
  inputs.

# 0.5.1
* FI-3788: Add default redirect/launch/post auth uris by @Jammjammjamm in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/89

# 0.5.0
* FI-3648: Add Spec for Shared Tests and Implement Features for the Failing
  Tests by @vanessuniq in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/86

# 0.4.6
* FI-3018: Allow multi-line custom headers in token introspection request by
  @emichaud998 in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/77
* FI-3257: Use Custom Authorization Header Input in Invalid Token Test by
  @emichaud998 in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/81
* FI-2919: SMART CORS Support Tests by @emichaud998 in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/75

# 0.4.5
* FI-3247: Add note that CORS is not yet tested by @Jammjammjamm in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/79

# 0.4.4
* FI-2874: Create New SMART v2.2 Suite and Update fhirContext by @emichaud998 in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/74
* FI-3053: Introspection URL Fix by @emichaud998 in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/76
* FI-3037: SMART User Access Brands Suite by @emichaud998 in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/73

# 0.4.3
* Dependency Updates 2024-04-05 by @Jammjammjamm in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/67
* FI-2429: Disable inferno validator by @dehall in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/68
* Dependency Updates 2024-06-05 by @Jammjammjamm in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/69
* Dependency Updates 2024-07-03 by @Jammjammjamm in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/71
* FI-2479: Asymmetric token refresh by @Jammjammjamm in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/70


# 0.4.2
* FI-2469 README Updates by @alisawallace in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/62
* FI-2470: Make Necessary Inputs Optional for New inferno_core Changes by
  @emichaud998 in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/63
* Dependency Updates 2024-03-19 by @Jammjammjamm in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/64
* Fix RubyGems URLs for homepage and source_code by @Shaumik-Ashraf in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/65

# 0.4.1
* FI-2395: Data Rights Legend by @bmath10 in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/60
* FI-2247 backend services migration by @alisawallace in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/59

# 0.4.0

* Fix jwt dependency by @Jammjammjamm in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/52
* Check fhirContext by @emichaud998 in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/56
* Add Token introspection tests by @arscan in
  https://github.com/inferno-framework/smart-app-launch-test-kit/pull/57

# 0.3.0

* Add support for asymmetric client auth to SMART v2.
* Add a message to the test result when redirecting the user to the auth
  endpoint.
* Use `docker compose` instead of `docker-compose`.

# 0.2.2

* Fix typos and launch test description.

# 0.2.1

* Update to support new development workflow. See [the template
  repository](https://github.com/inferno-framework/inferno-template#development-with-ruby)
  for details.
* Fix a bug in token refresh test where the original refresh token was not
  included in the smart credentials output when the refresh response did not
  contain a new refresh token.

# 0.2.0

* Update to use new version of inferno_core with ruby 3.

# 0.1.8

* Handle relative urls from the discovery endpoints.

# 0.1.7

* Update title for STU2 suite.

# 0.1.6

* Fix an unhandled exception in the discovery group.

# 0.1.5

* Add support for creating an authorization request using POST and integrate
  this change into App Redirect Test STU2, EHR Launch Group STU2, and
  Standalone Launch Group STU2.
* Set default scopes using SMARTv2 style in the SMART STU2 suite.
* Add `ignore_missing_scopes_check` configuration option to the Token Response
  Body Test in the EHR Launch Group (STU1 and STU2) and SMART Standalone Launch
  Group (STU1 and STU2).

# 0.1.4

Note: This kit contains separate suites for both the STU1 and STU2 versions of
the SMART App Launch Framework. However, development is ongoing and the SMART
STU2 suite is not yet fully complete.

* Create separate TestSuites for containing SMART STU1 and STU2.
* Include additional field requirements for Well-known configuration tests in
  SMART STU2 suite.
* Add an Accept header to Well-known configuration request.
* Provide documentation concerning the TestGroups available in this kit.
* Require PKCE for SMART STU2 Standalone and EHR launches.
* Improve wait messages.

# 0.1.3

* Update OpenID Token Payload test to check for `sub` claim.
* Fix url creation to account for `nil` params.

# 0.1.2

* Update scope validation for token refresh to accept a subset of the originally
  granted scopes.
* Lengthen PKCE code verifier to match spec.

# 0.1.1

* Allow a custom `launch` value in redirect test.
* Update links to SMART App Launch IG.

# 0.1.0

Initial public launch
