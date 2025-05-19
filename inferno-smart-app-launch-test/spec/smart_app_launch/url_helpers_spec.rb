require_relative '../../lib/smart_app_launch/url_helpers'

RSpec.describe SMARTAppLaunch::URLHelpers, :request do
  # See: https://datatracker.ietf.org/doc/html/rfc1808#section-4
  # See: https://datatracker.ietf.org/doc/html/rfc3986#section-5.4.1
  let(:klass) { Class.new { extend SMARTAppLaunch::URLHelpers } }
  let(:url) { 'https://example.com/fhir/'}
  let(:relative_url) { 'bar' }
  let(:full_url) { 'https://example.com/fhir/bar' }

  let(:base_url) { 'http://a/b/c/d;p?q#f' }
  let(:examples) {
    {
      'g:h' => 'g:h',
      'g' => 'http://a/b/c/g',
      './g' => 'http://a/b/c/g',
      'g/' => 'http://a/b/c/g/',
      '/g' => 'http://a/g',
      '//g' => 'http://g',
      '?y' => 'http://a/b/c/d;p?y',
      'g?y' => 'http://a/b/c/g?y',
      'g?y/./x' => 'http://a/b/c/g?y/./x',
      '#s' => 'http://a/b/c/d;p?q#s',
      'g#s' => 'http://a/b/c/g#s',
      'g#s/./x' => 'http://a/b/c/g#s/./x',
      'g?y#s' => 'http://a/b/c/g?y#s',
      ';x' => 'http://a/b/c/;x',
      'g;x' => 'http://a/b/c/g;x',
      'g;x?y#s' => 'http://a/b/c/g;x?y#s',
      '.' => 'http://a/b/c/',
      './' => 'http://a/b/c/',
      '..' => 'http://a/b/',
      '../' => 'http://a/b/',
      '../g' => 'http://a/b/g',
      '../..' => 'http://a/',
      '../../' => 'http://a/',
      '../../g' => 'http://a/g'
    }
  }

  it 'passes the normal RFC1808 examples' do
    # https://datatracker.ietf.org/doc/html/rfc1808#section-5.1
    examples.each do |embedded, absolute|
      new_url = klass.make_url_absolute(base_url, embedded)
      expect(new_url).to eq(absolute)
    end
  end

  it 'does not overwrite absolute urls' do
    new_url = klass.make_url_absolute(url, 'https://foo.org')
    expect(new_url).to eq('https://foo.org')

    new_url = klass.make_url_absolute(url, 'https://foo.org/')
    expect(new_url).to eq('https://foo.org/')
  end

  it 'returns nil when a nil embedded URL is provided' do
    new_url = klass.make_url_absolute(url, nil)
    expect(new_url).to eq(nil)
  end

  it 'returns the base URL when an empty embedded URL is provided' do
    new_url = klass.make_url_absolute(url, '')
    expect(new_url).to eq(url)
  end

  it 'treats embedded URLs starting with a slash as non-relative' do
    leading_slash_url = klass.make_url_absolute(url, 'bar')
    expect(leading_slash_url).to eq('https://example.com/fhir/bar')

    leading_slash_url = klass.make_url_absolute(url, '/bar')
    expect(leading_slash_url).to eq('https://example.com/bar')
  end

  it 'handles relative urls with multiple path components' do
    new_url = klass.make_url_absolute(url, 'bar/baz')
    expect(new_url).to eq('https://example.com/fhir/bar/baz')
  end
end
