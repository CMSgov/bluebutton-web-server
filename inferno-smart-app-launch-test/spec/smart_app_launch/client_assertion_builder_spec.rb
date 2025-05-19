require_relative '../../lib/smart_app_launch/client_assertion_builder'
require_relative '../../lib/smart_app_launch/jwks'

RSpec.describe SMARTAppLaunch::ClientAssertionBuilder do
  let(:client_auth_encryption_methods) { ['ES384', 'RS384'] }
  let(:iss) { 'ISS' }
  let(:sub) { 'SUB' }
  let(:aud) { 'AUD' }
  let(:default_jwks) { SMARTAppLaunch::JWKS.jwks }

  def build_and_decode_jwt(encryption_method, kid, custom_jwks = nil)
    jwt = described_class.build(client_auth_encryption_method: encryption_method, iss:, sub:, aud:, kid:, custom_jwks:)
    jwks =
      if custom_jwks.present?
        JWT::JWK::Set.new(JSON.parse(custom_jwks))
      else
        default_jwks
      end
    return JWT.decode(jwt, kid, true, algorithms: [encryption_method], jwks:)
  end

  describe '.build' do
    context 'with unspecified key id' do
      it 'creates a valid JWT' do
        client_auth_encryption_methods.each do |client_auth_encryption_method|
          payload, header = build_and_decode_jwt(client_auth_encryption_method, nil)

          expect(header['alg']).to eq(client_auth_encryption_method)
          expect(header['typ']).to eq('JWT')
          expect(payload['iss']).to eq(iss)
          expect(payload['sub']).to eq(sub)
          expect(payload['aud']).to eq(aud)
          expect(payload['exp']).to be_present
          expect(payload['jti']).to be_present
        end
      end
    end

    context 'with specified key id' do
      it 'creates a valid JWT with correct algorithm and kid' do
        encryption_method = 'ES384'
        kid = '4b49a739d1eb115b3225f4cf9beb6d1b'
        payload, header = build_and_decode_jwt(encryption_method, kid)

        expect(header['alg']).to eq(encryption_method)
        expect(header['typ']).to eq('JWT')
        expect(header['kid']).to eq(kid)
        expect(payload['iss']).to eq(iss)
        expect(payload['sub']).to eq(sub)
        expect(payload['aud']).to eq(aud)
        expect(payload['exp']).to be_present
        expect(payload['jti']).to be_present
      end

      it 'throws exception when key id not found for algorithm' do
        encryption_method = 'RS384'
        kid = '4b49a739d1eb115b3225f4cf9beb6d1b'

        expect {
          build_and_decode_jwt(encryption_method, kid)
        }.to raise_error(Inferno::Exceptions::AssertionException)
      end
    end

    context 'with a custom jwks' do
      let(:custom_jwks) do
        {
          keys: [
            {
              p: '0ldL6PGNrWsSTl8OKTToxWZHYpl1PbRLe8dk7FxoOigd645QXmLkLRWv9chP5gHzZaKQd57F2HUkrRa-qGQ5OoXVERjI9Yhlyb48KcDlsByD3SNngLAjn8wW7-FpmrvG5O0J3gw8ahh20OLjhXmTawz_vOvNO0orIOA3RbH6Vp8',
              kty: 'RSA',
              q: 'yZHm04wk8NEu0BIyLGyEKUXgFaV1AgIwv69RplQb9OSsmfPsJCXbMkT2YighRifgHfK-CYsph7P-hFHX-DcA7RFsNmXTeZsXl4FDLdqtscO4QW-P3CNxA9UMic2WSu1jPtoGXguDiZ3KtKwQf14TKjhNcPILGCfGi6FSqNE97is',
              d: 'WPtbrIZZDZPvy6oI4Ka7xTrh4FN45fc_5iC_YVNDTGGH7DPstM_wSWO9__yPGb1pSq7OD20J33X4BY030aS4ojKB_Lp-ZHvfVcxgqHV23KHMsF3uDGHuWkyv3o7r8KTOIWDuLGV-rbdbB4Xy3qUc3xz8QBs9E62pr7gX215FhkgbAhzDU8tDLHyK4QCOlkUelgWicpyxckx0jgeNx_R672GMPrAwgaJJ4dMHXzPnxHJNKFk9B5nNvaKs3eQnS4kXLT2o4a7PxebPQVC9hWPftssM0rT_DKKCvglUKkdWKU_UJvdrr6wp0-8mMEArlz70bdcG7vd-hMqwMiz9Qv1fJQ',
              e: 'AQAB',
              kid: 'lj_kNBurp5jmxVpRMH57w-R8n_fojB3kD1xxQ2XuVRY',
              qi: 'M7BpozlFkEcbV-4mA2EMFxN1xKSrW6tTfIleDSzDOZ_cO4wcs9CG2EB9YIDrtrRKlTbUbnsNcKVzFFqVTYJ2ldSjxbDzl8tJMnu1TeXAQ7HxVmXnEW_P2uykTpkJxnwiWj5yVH-vw6GofR1viK3ST0sTFE0woDOAcox_pRyX6uY',
              dp: 'IGgEsPnuOwahBmQMuXqGVktguicscfpCGuroeKXwBO3DVlRRu4j-4JdTyck3zhcE2ebG3TcgAi5iHSzA6Q6v5n1SC1VHONTv4bomaMRoXs613i8jNidtBaSa8BBJheZiSUjf2U8HS81DGQGrzheiB78z83Zc40KVDHae7WTzTb8',
              alg: 'RS384',
              dq: 'S3h_bpG4exo3ZtyJQKzYxwNMpY4vwzLCweKItbgkR4sfPP1hWx95dNbxUUspOjVP6qaqlLQwNokkMLLcJCmkBR9S3wM9LPju2mEhoBeSlU5svMNin8_9TqwEZ8w8C43abPwBClFRTMNx1DfgbW_xyQsPo8xcbwzlf_5FDsRZZcU',
              n: 'pZ5rtCPmABR0WnyiUz5vOSDzUmQuZV2inR6Gaq1CbXSZNzQVur8PnowKAI5-iYRhdDCZ41zF7zuxpmwmlVMU3ZjkSWfwdn7tIXp1qBYnyN2c8tK62lxXEpkd9MBHMGtcda_y87BPIDrs2UcDbb9VQyRAzV9CQyfB65yuuDv5JAdY91ZqZaa-xq6I3wutynU0fd8_mJ5ykdHVY9q6RCyF6pZNaV_jrGZ-sqaVualFaLHBIAXGDraYifujWvEfw6zuZYYd6PnA9U_jyF75FAVcrNS87_f22w0r6Sy9Ri9iNzb2AFZC4HT32XsriAFYMaQfkVxsdTgRHI3V-6PiFHdetQ',
              key_ops: ['sign']
            }
          ]
        }
      end

      it 'creates a valid JWT' do
        payload, header = build_and_decode_jwt('RS384', nil, custom_jwks.to_json)

        expect(header['alg']).to eq('RS384')
        expect(payload['iss']).to eq(iss)
        expect(payload['sub']).to eq(sub)
        expect(payload['aud']).to eq(aud)
        expect(payload['exp']).to be_present
        expect(payload['jti']).to be_present
      end
    end
  end
end
