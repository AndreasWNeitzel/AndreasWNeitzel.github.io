# Links that leave the site, and PDFs (the CV among them), open in a new tab, so a reader keeps the page they came from.
# Runs on the rendered HTML of every page and document; a link that already sets its own target is left alone.
module NewTab
  ANCHOR = /<a\b[^>]*>/i

  def self.leaves?(tag, host)
    href = tag[/\bhref\s*=\s*["']([^"']+)["']/i, 1].to_s
    return false if href.empty? || href.start_with?("#", "mailto:", "tel:", "javascript:")
    return true if href =~ /\.pdf(\?|#|\z)/i
    href =~ %r{\A(https?:)?//}i && !href.include?(host)
  end

  def self.apply(html, host)
    html.gsub(ANCHOR) do |tag|
      next tag if tag =~ /\btarget\s*=/i || !leaves?(tag, host)
      rel = tag =~ /\brel\s*=/i ? "" : ' rel="noopener"'
      tag.sub(/>\z/, %( target="_blank"#{rel}>))
    end
  end
end

Jekyll::Hooks.register [:pages, :documents], :post_render do |doc|
  next unless doc.output_ext == ".html" && doc.output
  host = doc.site.config["url"].to_s.sub(%r{\Ahttps?://}, "")
  host = "andreaswneitzel.github.io" if host.empty?
  doc.output = NewTab.apply(doc.output, host)
end
