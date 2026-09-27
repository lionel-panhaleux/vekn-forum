# After the phpBB importer (wiki/operations.md#phpbb-import), by `rails runner` with RAILS_DB and
# IMPORT_SETTINGS set and the import bundle (Gemfile here, for mysql2). Re-running converges.
require "mysql2"

settings = YAML.load_file(ENV.fetch("IMPORT_SETTINGS"))
db = settings["database"]
mysql =
  Mysql2::Client.new(
    host: db["host"],
    port: db["port"],
    username: db["username"],
    password: db["password"],
    database: db["schema"],
  )
imported = CategoryCustomField.where(name: "import_id").pluck(:value, :category_id).to_h

# The importer writes a forum's permalink only for a category it creates.
forums = settings["vekn"]["sections"].keys + settings["vekn"]["restricted"].keys
merged = settings["import"]["category_mappings"].select { it["target_category_id"] }
(forums.map { [it, it] } + merged.map { [it["source_category_id"], it["target_category_id"]] })
  .each do |forum_id, target_id|
    url = "viewforum.php?f=#{forum_id}"
    Permalink.create!(url: url, category_id: imported.fetch(target_id.to_s)) if !Permalink.find_by_url(url)
  end

# wiki/design.md#category-icons: a board the importer created takes its section's icon.
Category
  .where(id: imported.values, style_type: Category.style_types[:square])
  .where.not(parent_category_id: nil)
  .includes(:parent_category)
  .find_each do |category|
    parent = category.parent_category
    category.update!(style_type: "icon", icon: parent.icon, color: parent.color, text_color: parent.text_color)
  end

# The importer rewrites a link to a topic it has already imported; the rest are resolved here through
# the permalinks, and a link to what was never imported (Playtest Ind) keeps the old host.
legacy = %r{https?://(?:www\.)?vekn\.fr/forum/((?:viewtopic|viewforum)\.php\?[^\s)\]"<]*)}i
icons = settings["vekn"]["disciplines"].flat_map { [[it, it], [it.upcase, it.upcase]] }.to_h
icons.merge!(settings["vekn"]["clans"])
smiley = /(?<![\w:]):(#{icons.keys.map { Regexp.escape(it) }.join("|")}):(?![\w:])/
Post
  .joins(:_custom_fields)
  .where(post_custom_fields: { name: "import_id" })
  .find_each do |post|
    raw =
      post.raw.gsub(legacy) do |link|
        Permalink.find_by_url("forum/#{CGI.unescapeHTML($1)}")&.target_url || link
      end
    # The old site's card tag (krcg.js drew it as span.krcg-card) and icon smilies become
    # wiki/design.md#theming's card display.
    raw = raw.gsub(%r{\[card\](.+?)\[/card\]}i, '[[\1]]').gsub(smiley) { "[#{icons.fetch($1)}]" }
    next if raw == post.raw
    post.update_columns(raw: raw)
    post.rebake!
  end

# Rights are the bridge's (wiki/engine.md#login), and an imported account has not logged in through
# it: a phpBB admin or moderator keeps neither, and a legacy address gets no digest of a forum its
# owner has not joined.
legacy_users =
  User.real.joins(:_custom_fields).where(user_custom_fields: { name: "import_id" })
    .where.missing(:single_sign_on_record)
legacy_users.where("admin OR moderator").find_each do |user|
  user.update!(admin: false, moderator: false)
  puts "revoked the phpBB rights of #{user.username}"
end
UserOption.where(user_id: legacy_users.select(:id)).update_all(email_digests: false)

# The importer fails to create a second phpBB account with an address already taken, and gives its
# posts to the system user: they go to the account holding that address.
users = UserCustomField.where(name: "import_id").pluck(:value)
mysql
  .query(<<~SQL)
    SELECT u.user_id, u.user_email FROM #{db["table_prefix"]}users u
    WHERE u.user_posts > 0 AND u.user_email <> ''
  SQL
  .reject { users.include?(it["user_id"].to_s) }
  .each do |row|
    owner = UserEmail.find_by(email: row["user_email"].downcase)&.user or next
    post_ids =
      mysql.query("SELECT post_id FROM #{db["table_prefix"]}posts WHERE poster_id = #{row["user_id"].to_i}").map { it["post_id"].to_s }
    orphans =
      Post.joins(:_custom_fields).where(
        user_id: Discourse::SYSTEM_USER_ID,
        post_custom_fields: { name: "import_id", value: post_ids },
      )
    next if orphans.none?
    orphans
      .group_by(&:topic_id)
      .each do |topic_id, posts|
        PostOwnerChanger.new(
          post_ids: posts.map(&:id),
          topic_id: topic_id,
          new_owner: owner,
          acting_user: Discourse.system_user,
          skip_revision: true,
        ).change_owner!
      end
    puts "gave phpBB user #{row["user_id"]}'s posts to #{owner.username}"
  end

# The importer takes every post: what phpBB had hidden (soft-deleted, unapproved) is deleted again,
# a hidden topic with its first post.
hidden =
  mysql.query(<<~SQL).map { it["post_id"].to_s }
    SELECT p.post_id FROM #{db["table_prefix"]}posts p JOIN #{db["table_prefix"]}topics t USING (topic_id)
    WHERE p.post_visibility <> 1 OR (t.topic_visibility <> 1 AND p.post_id = t.topic_first_post_id)
  SQL
Post
  .joins(:_custom_fields)
  .where(post_custom_fields: { name: "import_id", value: hidden })
  .find_each { PostDestroyer.new(Discourse.system_user, it, context: "hidden in phpBB").destroy }

# Roles are archon's (wiki/dogmas.md#data): phpBB's groups are not carried over.
Group.joins(:_custom_fields).where(group_custom_fields: { name: "import_id" }).destroy_all
