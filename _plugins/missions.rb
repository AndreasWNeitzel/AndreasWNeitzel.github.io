# Liquid filters for the site: italicise mission names, keep initials together, format date
# spans, and merge the ledger export into one typed, dated list for the home-page timeline.
module SiteFilters
  MISSIONS = %w[Gaia Ariel ARIEL TESS Kepler HAYDN PLATO Cheops Euclid].freeze
  MONTHS = %w[Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec].freeze

  def missions(text)
    return text if text.nil?
    MISSIONS.reduce(text.to_s) do |s, m|
      s.gsub(/(?<![\w<>\/])#{m}(?=[\s,.:;)\/?'’]|$)/, "<i>#{m}</i>")
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

  # "2026-07-06" -> "Jul 2026"; "2026" -> "2026"
  def month_year(value)
    s = value.to_s
    return s unless s =~ /\A(\d{4})-(\d{2})/
    "#{MONTHS[Regexp.last_match(2).to_i - 1]} #{Regexp.last_match(1)}"
  end

  def entry_url(e, cat)
    ids = e["identifiers"] || {}
    return "https://doi.org/#{ids['doi']}" if ids["doi"]
    return "https://arxiv.org/abs/#{ids['arxiv']}" if ids["arxiv"]
    return "https://hdl.handle.net/#{ids['handle']}" if ids["handle"]
    return ids["url"] if ids["url"]
    return ids["repo"] if ids["repo"]
    nil
  end

  # Returns rows {when, sort, kind, tag, label, title, meta, url, link} newest first.
  def timeline(ledger)
    rows = []
    (ledger || {}).each do |cat, entries|
      next if cat == "skills" || !entries.is_a?(Array)
      entries.each do |e|
        kind, tag, label = classify(cat, e)
        next if kind.nil?
        date = e["date"].to_s
        url = entry_url(e, cat)
        url = "/observing/paranal/" if e["id"].to_s.include?("paranal")
        meta = [e["venue"], e["institution"], e["location"]].compact.map(&:to_s).reject(&:empty?).uniq.join(" · ")
        meta = e["tagline"].to_s if meta.empty? && e["tagline"]
        rows << {
          "when" => month_year(date), "sort" => date.ljust(10, "0"), "kind" => kind, "tag" => tag, "label" => label,
          "title" => e["title"].to_s, "meta" => meta, "url" => url,
          "link" => url.to_s.include?("doi.org") ? "DOI" : url.to_s.include?("arxiv") ? "arXiv" : "Open"
        }
      end
    end
    rows.sort_by { |r| r["sort"] }.reverse
  end

  def timeline_counts(rows)
    counts = Hash.new(0)
    rows.each { |r| r["kind"].split(" ").each { |k| counts[k] += 1 } }
    counts
  end

  private

  def classify(cat, e)
    k = e["kind"].to_s
    case cat
    when "publications"
      return ["paper", "data", "data"] if k == "data"
      return ["paper", "paper", "thesis"] if k == "thesis"
      return nil if k == "in-preparation"
      ["paper", "paper", e["role"] == "first-author" ? "paper · first author" : "paper"]
    when "presentations"
      poster = %w[poster pitch].include?(k)
      lab = poster ? (k == "pitch" ? "poster pitch" : "poster") : (k == "seminar" ? "seminar" : "talk")
      lab += " · co-author" if e["role"] == "co-author"
      ["talk", poster ? "poster" : "talk", lab]
    when "funding"
      k == "computing" ? ["hpc", "hpc", "HPC"] : ["grant", "grant", k == "grant" ? "project" : "fellowship"]
    when "events"
      return ["observing", "observing", "observing"] if k == "observing-run"
      ["service", "event", k.empty? ? "event" : k]
    when "software"
      ["software", "software", k == "docs" ? "manual" : "software"]
    when "awards" then ["award", "award", "award"]
    when "positions" then ["position", "position", "position"]
    when "education" then ["position", "position", "degree"]
    when "service" then ["service", "service", "organiser"]
    when "teaching" then ["service", "teaching", "teaching"]
    when "outreach" then ["service", "service", "outreach"]
    when "memberships" then ["position", "membership", "consortium"]
    end
  end
end
Liquid::Template.register_filter(SiteFilters)
