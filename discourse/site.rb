# One site's settings for the bridge (wiki/engine.md#login), run by `rails runner` with RAILS_DB set;
# the dev stack and the deploy both run it. Every value comes from the environment.

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
