# One site's settings (wiki/engine.md#login, wiki/operations.md#deploy), run by `rails runner` with
# RAILS_DB set; the dev stack and the deploy both run it. Every value comes from the environment.

# Group names are validated as usernames: 3 characters minimum by default, and the role groups the
# bridge creates include `ic`, `nc`, `pt`.
SiteSetting.min_username_length = 2
SiteSetting.set_locale_from_accept_language_header = true
SiteSetting.default_locale = ENV.fetch("SITE_LOCALE")
SiteSetting.discourse_connect_url = ENV.fetch("SITE_CONNECT_URL")
SiteSetting.discourse_connect_secret = ENV.fetch("SITE_CONNECT_SECRET")
SiteSetting.enable_discourse_connect = true
SiteSetting.email_editable = false
SiteSetting.auth_overrides_email = true
SiteSetting.force_https = ENV.fetch("SITE_URL").start_with?("https://")
SiteSetting.backup_frequency = 1
SiteSetting.notification_email = ENV["SITE_EMAIL"] if ENV["SITE_EMAIL"]
if ENV["SITE_GATED"]
  SiteSetting.login_required = true
  SiteSetting.allow_index_in_robots_txt = false
end

# The key's value lives with the bridge; Discourse keeps only its hash, and generates none when
# given one.
key = ENV.fetch("SITE_API_KEY")
hash = ApiKey.hash_key(key)
ApiKey.where(description: "bridge").where.not(key_hash: hash).destroy_all
ApiKey.find_or_create_by!(description: "bridge", key_hash: hash) do |k|
  k.truncated_key = key[0..3]
  k.created_by_id = Discourse::SYSTEM_USER_ID
end
SiteSetting.enable_powered_by_discourse = false
SiteSetting.interface_color_selector = "sidebar_footer"
SiteSetting.allow_uncategorized_topics = false

# Discourse seeds General and Site Feedback until a human joins; they serve no section
# (wiki/design.md#cut). Removed while only the system has posted there: its topics go to the trash, via
# Uncategorized, which Discourse lists like any other category when this setting has lost it.
uncategorized = Category.find_by(id: SiteSetting.uncategorized_category_id)
raise "uncategorized_category_id #{SiteSetting.uncategorized_category_id} names no category" if !uncategorized
removed =
  %w[general_category_id meta_category_id].filter_map do |setting|
    category = Category.find_by(id: SiteSetting.get(setting)) or next
    topics = Topic.with_deleted.where(category_id: category.id).where.not(id: category.topic_id)
    posts = Post.with_deleted.where(topic_id: topics.select(:id))
    next if posts.where.not(user_id: Discourse::SYSTEM_USER_ID).exists?
    topics.find_each do |topic|
      topic.update_columns(category_id: uncategorized.id)
      next if topic.deleted_at
      PostDestroyer.new(Discourse.system_user, topic.first_post, context: "site provisioning").destroy
    end
    category.reload.destroy!
  end
if removed.any?
  # The web processes cache categories per locale; a destroy here clears only this process's.
  I18n.available_locales.each { |locale| I18n.with_locale(locale) { Site.clear_cache } }
  Site.clear_anon_cache!
end

# The base theme (wiki/design.md#theming), re-imported from its directory on every run; found by
# name, since the import creates a new theme when not handed one.
theme = Theme.find_by(name: "VEKN", component: false)
theme = RemoteTheme.import_theme_from_directory(ENV.fetch("SITE_THEME_DIR"), theme_id: theme&.id)
theme.set_default!
Theme.where.not(id: theme.id).where(user_selectable: true).find_each { |t| t.update!(user_selectable: false) }

# The site's tokens. Its palettes are not the theme's own: a re-import deletes the theme's palettes
# its about.json does not list.
light, dark = theme.color_schemes.find_by(name: "VEKN"), theme.color_schemes.find_by(name: "VEKN Dark")
if (dir = ENV["SITE_IDENTITY_DIR"])
  identity = JSON.parse(File.read(File.join(dir, "identity.json")))
  SiteSetting.title = identity["title"]
  SiteSetting.heading_font = identity["heading_font"] || SiteSetting.defaults[:heading_font]
  changed = false
  light, dark =
    { "" => "light", " Dark" => "dark" }.map do |suffix, mode|
      scheme = ColorScheme.find_or_create_by!(name: "#{ENV.fetch("RAILS_DB")}#{suffix}", theme_id: nil)
      identity["palettes"][mode].each do |name, hex|
        color = scheme.color_scheme_colors.find_or_initialize_by(name: name)
        next if color.hex == hex
        color.update!(hex: hex)
        changed = true
      end
      scheme
    end
  # A palette's own save bumps its stylesheet only for themes using it as their light palette, and
  # a web process keeps serving the old colours otherwise.
  if changed
    [light, dark].each(&:save!)
    ColorScheme.publish_discourse_stylesheets!
  end
  %w[logo logo_small large_icon].each do |setting|
    # UploadCreator optimizes the image beside its source: hand it a copy in a writable place.
    Tempfile.create([setting, ".png"]) do |file|
      IO.copy_stream(File.join(dir, "#{setting}.png"), file)
      file.rewind
      upload = UploadCreator.new(file, "#{setting}.png").create_for(Discourse::SYSTEM_USER_ID)
      SiteSetting.set(setting, upload)
    end
  end
end
theme.update!(color_scheme: light, dark_color_scheme: dark)
