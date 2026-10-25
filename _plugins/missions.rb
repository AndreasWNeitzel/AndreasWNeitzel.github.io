# Liquid filters for the site: italicise mission names and keep initials together.
module SiteFilters
  MISSIONS = %w[Gaia Ariel ARIEL TESS Kepler HAYDN PLATO Cheops Euclid].freeze

  def missions(text)
    return text if text.nil?
    MISSIONS.reduce(text.to_s) do |s, m|
      s.gsub(/(?<![\w<>\/])#{m}(?=[\s,.:;)\/]|$)/, "<i>#{m}</i>")
    end
  end

  def initials(text)
    return text if text.nil?
    text.to_s.gsub(/\b([A-Z])\. (?=[A-Z])/, '\1.&nbsp;')
  end

  def span(entry)
    start = entry["date"].to_s
    finish = entry["end_date"].to_s
    return start if finish.empty?
    "#{start} to #{finish}"
  end
end
Liquid::Template.register_filter(SiteFilters)
