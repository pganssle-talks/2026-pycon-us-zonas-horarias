require 'rqrcode'

module Jekyll
  module QRCodeFilter
    def to_qr_svg(url)
      qr = RQRCode::QRCode.new(url, level: :m)
      svg = qr.as_svg(
        color: '000000',
        shape_rendering: 'crispEdges',
        module_size: 4,
        standalone: true,
        use_path: true,
        offset: 4
      )
      # Replace hard-coded width/height with a viewBox so CSS can scale
      # the SVG freely. Without viewBox the coordinate system is fixed
      # and resizing just clips the paths rather than scaling them.
      svg.sub(/(<svg[^>]*)\s+width="(\d+)"\s+height="(\d+)"/) do
        "#{$1} viewBox=\"0 0 #{$2} #{$3}\""
      end
    rescue StandardError
      ''
    end
  end
end

Liquid::Template.register_filter(Jekyll::QRCodeFilter)
