# One page per entry of _data/tools.yml at /software/tools/<id>/, drawn by _layouts/tool.html.
# An entry whose loop is not installed (assets/video/<loop>.av1.mp4) gets no page; the Software page skips its card
# by the same test, so a tool appears only once its approved loop is in place.
module ToolPages
  class Generator < Jekyll::Generator
    safe true
    priority :normal

    def generate(site)
      Array(site.data["tools"]).each do |t|
        next unless File.exist?(File.join(site.source, "assets", "video", "#{t['loop']}.av1.mp4"))
        page = Jekyll::PageWithoutAFile.new(site, site.source, File.join("software", "tools", t["id"]), "index.html")
        page.data.merge!(
          "layout" => "tool",
          "title" => t["title"],
          "tool" => t["id"],
          "nav_section" => "Software",
          "description" => t["description"],
          "lede" => t["line"]
        )
        site.pages << page
      end
    end
  end
end
