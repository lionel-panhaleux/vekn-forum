# Before the phpBB importer (wiki/operations.md#phpbb-import), by `rails runner` with RAILS_DB and
# IMPORT_SETTINGS set and the import bundle (Gemfile here, for mysql2). Re-running converges.
require "mysql2"

settings = YAML.load_file(ENV.fetch("IMPORT_SETTINGS"))
vekn = settings["vekn"]
section = ->(slug) { Category.find_by!(slug: slug, parent_category_id: nil) }
tag = ->(category, forum_id) do
  category.custom_fields["import_id"] = forum_id.to_s
  category.save_custom_fields
end

# The importer skips a forum whose import_id a category already carries and puts its topics and
# child forums there.
vekn["sections"].each { |forum_id, slug| tag.(section.(slug), forum_id) }

# Created before any topic lands, so a private board is never public, even for a moment.
vekn["restricted"].each do |forum_id, spec|
  next if CategoryCustomField.exists?(name: "import_id", value: forum_id.to_s)
  parent = section.(spec["parent"])
  category =
    Category.new(
      name: spec["name"],
      slug: spec["slug"],
      user: Discourse.system_user,
      parent_category_id: parent.id,
      style_type: "icon",
      icon: parent.icon,
      color: parent.color,
      text_color: parent.text_color,
    )
  category.set_permissions(spec["groups"].to_h { [it, :full] })
  category.save!
  tag.(category, forum_id)
end

# The importer creates a user only when no account has their email, and fails otherwise: a member
# who logged in before the import takes their phpBB account's import_id, so its posts become theirs —
# the same email match as the legacy claim (wiki/engine.md#login).
db = settings["database"]
mysql =
  Mysql2::Client.new(
    host: db["host"],
    port: db["port"],
    username: db["username"],
    password: db["password"],
    database: db["schema"],
  )
mysql
  .query("SELECT user_id, user_email FROM #{db["table_prefix"]}users WHERE user_email <> ''")
  .each do |row|
    user = UserEmail.find_by(email: row["user_email"].downcase)&.user or next
    next if user.custom_fields["import_id"].present?
    user.custom_fields["import_id"] = row["user_id"].to_s
    user.save_custom_fields
    puts "linked #{user.username} to phpBB user #{row["user_id"]}"
  end
