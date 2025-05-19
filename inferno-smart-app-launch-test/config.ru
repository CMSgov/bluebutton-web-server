require 'inferno'

use Rack::Static,
    urls: Inferno::Utils::StaticAssets.static_assets_map,
    root: Inferno::Utils::StaticAssets.inferno_path

Inferno::Application.finalize!

use Inferno::Utils::Middleware::RequestLogger

run Inferno::Web.app
