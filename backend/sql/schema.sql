PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  username TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'muted', 'banned')),
  approval_status TEXT NOT NULL DEFAULT 'pending' CHECK (approval_status IN ('pending', 'approved', 'rejected')),
  approved_by_user_pk INTEGER,
  approved_at DATETIME,
  rejected_reason TEXT,
  muted_until DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at DATETIME,
  FOREIGN KEY (approved_by_user_pk) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE refresh_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  token_hash TEXT NOT NULL UNIQUE,
  expires_at DATETIME NOT NULL,
  revoked_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE account_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id TEXT NOT NULL UNIQUE,
  user_pk INTEGER,
  email TEXT NOT NULL,
  request_type TEXT NOT NULL CHECK (request_type IN ('forgot_id', 'reset_password', 'change_user_id')),
  token_hash TEXT NOT NULL,
  new_user_id TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'expired', 'cancelled')),
  expires_at DATETIME NOT NULL,
  confirmed_at DATETIME,
  requested_by_admin_pk INTEGER,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY (requested_by_admin_pk) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE trails (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  age_group TEXT NOT NULL CHECK (age_group IN ('10-12', '13-15', '16-17', 'all')),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
  created_by INTEGER,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE lessons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trail_id INTEGER NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  position INTEGER NOT NULL,
  duration_min INTEGER NOT NULL CHECK (duration_min BETWEEN 2 AND 6),
  cards_json TEXT NOT NULL CHECK (json_valid(cards_json)),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (trail_id) REFERENCES trails(id) ON DELETE CASCADE
);

CREATE TABLE quizzes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trail_id INTEGER NOT NULL,
  lesson_id INTEGER,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  passing_score INTEGER NOT NULL DEFAULT 70 CHECK (passing_score BETWEEN 0 AND 100),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (trail_id) REFERENCES trails(id) ON DELETE CASCADE,
  FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE SET NULL
);

CREATE TABLE quiz_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quiz_id INTEGER NOT NULL,
  position INTEGER NOT NULL,
  prompt TEXT NOT NULL,
  explanation TEXT NOT NULL,
  FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

CREATE TABLE quiz_options (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER NOT NULL,
  position INTEGER NOT NULL,
  option_text TEXT NOT NULL,
  is_correct INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
  FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE
);

CREATE TABLE challenges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trail_id INTEGER NOT NULL,
  lesson_id INTEGER,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  steps_json TEXT NOT NULL CHECK (json_valid(steps_json)),
  safety_notes_json TEXT NOT NULL CHECK (json_valid(safety_notes_json)),
  xp_reward INTEGER NOT NULL DEFAULT 20 CHECK (xp_reward >= 0),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (trail_id) REFERENCES trails(id) ON DELETE CASCADE,
  FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE SET NULL
);

CREATE TABLE lesson_completion (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  lesson_id INTEGER NOT NULL,
  seconds_spent INTEGER NOT NULL DEFAULT 0 CHECK (seconds_spent >= 0),
  completed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_pk, lesson_id),
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
);

CREATE TABLE quiz_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  quiz_id INTEGER NOT NULL,
  score INTEGER NOT NULL CHECK (score >= 0),
  max_score INTEGER NOT NULL CHECK (max_score > 0),
  answers_json TEXT NOT NULL CHECK (json_valid(answers_json)),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

CREATE TABLE challenge_completion (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  challenge_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('in_progress', 'completed')),
  checklist_json TEXT NOT NULL CHECK (json_valid(checklist_json)),
  completed_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_pk, challenge_id),
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE
);

CREATE TABLE xp_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('lesson', 'quiz', 'challenge', 'mission_response_useful', 'checkin', 'coop', 'admin_adjustment')),
  source_id TEXT,
  points INTEGER NOT NULL,
  reason TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE achievements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  achievement_key TEXT NOT NULL,
  title TEXT NOT NULL,
  unlocked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  meta_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(meta_json)),
  UNIQUE (user_pk, achievement_key),
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE emotion_checkins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  emotion TEXT NOT NULL CHECK (emotion IN ('alegria', 'tristeza', 'raiva', 'medo', 'ansiedade', 'frustracao', 'calma', 'orgulho', 'confusao')),
  intensity INTEGER NOT NULL CHECK (intensity BETWEEN 1 AND 5),
  context_tags_json TEXT NOT NULL CHECK (json_valid(context_tags_json)),
  need_tags_json TEXT NOT NULL CHECK (json_valid(need_tags_json)),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE support_cards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_key TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL CHECK (category IN ('ansiedade', 'frustracao', 'autoestima', 'conflitos', 'foco_rotina', 'social', 'familia', 'escola')),
  tone TEXT NOT NULL CHECK (tone IN ('escuta', 'ideias_praticas', 'motivacao', 'acalmar', 'organizar_passos')),
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  guided_actions_json TEXT NOT NULL CHECK (json_valid(guided_actions_json)),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE missions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  creator_user_pk INTEGER NOT NULL,
  target_user_pk INTEGER,
  category TEXT NOT NULL CHECK (category IN ('ansiedade', 'frustracao', 'autoestima', 'conflitos', 'foco_rotina', 'social', 'familia', 'escola')),
  intensity INTEGER NOT NULL CHECK (intensity BETWEEN 1 AND 5),
  context_tags_json TEXT NOT NULL CHECK (json_valid(context_tags_json)),
  want_now TEXT NOT NULL CHECK (want_now IN ('escuta', 'ideias_praticas', 'motivacao', 'acalmar', 'organizar_passos')),
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed', 'resolved', 'flagged', 'removed')),
  expires_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (creator_user_pk) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (target_user_pk) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE mission_responses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id INTEGER NOT NULL,
  responder_user_pk INTEGER NOT NULL,
  card_id INTEGER NOT NULL,
  guided_actions_selected_json TEXT NOT NULL CHECK (json_valid(guided_actions_selected_json)),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'hidden', 'removed')),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (mission_id, responder_user_pk),
  FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
  FOREIGN KEY (responder_user_pk) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (card_id) REFERENCES support_cards(id) ON DELETE RESTRICT
);

CREATE TABLE mission_feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id INTEGER NOT NULL,
  response_id INTEGER NOT NULL,
  from_user_pk INTEGER NOT NULL,
  is_useful INTEGER NOT NULL CHECK (is_useful IN (0, 1)),
  is_best_response INTEGER NOT NULL DEFAULT 0 CHECK (is_best_response IN (0, 1)),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (mission_id, from_user_pk),
  UNIQUE (response_id, from_user_pk),
  FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
  FOREIGN KEY (response_id) REFERENCES mission_responses(id) ON DELETE CASCADE,
  FOREIGN KEY (from_user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE coop_challenges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('cooperacao', 'comunicacao', 'autocuidado', 'organizacao')),
  description TEXT NOT NULL,
  steps_json TEXT NOT NULL CHECK (json_valid(steps_json)),
  max_members INTEGER NOT NULL DEFAULT 4 CHECK (max_members BETWEEN 2 AND 8),
  visibility TEXT NOT NULL DEFAULT 'public_safe' CHECK (visibility IN ('public_safe', 'private_invite')),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
  created_by_user_pk INTEGER,
  start_at DATETIME,
  end_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by_user_pk) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE coop_memberships (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  coop_challenge_id INTEGER NOT NULL,
  user_pk INTEGER NOT NULL,
  role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('member', 'leader')),
  progress_step INTEGER NOT NULL DEFAULT 0 CHECK (progress_step >= 0),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'left')),
  joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (coop_challenge_id, user_pk),
  FOREIGN KEY (coop_challenge_id) REFERENCES coop_challenges(id) ON DELETE CASCADE,
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE coop_progress_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  coop_challenge_id INTEGER NOT NULL,
  user_pk INTEGER NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('joined', 'left', 'step_completed')),
  step_index INTEGER,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (coop_challenge_id) REFERENCES coop_challenges(id) ON DELETE CASCADE,
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE generated_trails (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  trail_key TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  difficulty TEXT NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')),
  focus_tags_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(focus_tags_json)),
  lesson_bundle_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(lesson_bundle_json)),
  recommended_xp INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_pk, trail_key),
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE coop_pairs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_low_pk INTEGER NOT NULL,
  user_high_pk INTEGER NOT NULL,
  requested_by_user_pk INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'rejected')),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  confirmed_at DATETIME,
  rejected_at DATETIME,
  UNIQUE (user_low_pk, user_high_pk),
  CHECK (user_low_pk <> user_high_pk),
  FOREIGN KEY (user_low_pk) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (user_high_pk) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (requested_by_user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE friendship_xp_rewards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  milestone INTEGER NOT NULL,
  xp_awarded INTEGER NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_pk, milestone),
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE user_mascot_inventory (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  item_id TEXT NOT NULL,
  item_name TEXT NOT NULL,
  rarity TEXT NOT NULL CHECK (rarity IN ('common', 'rare', 'epic')),
  slot TEXT NOT NULL CHECK (slot IN ('head', 'face', 'neck', 'back', 'effect', 'hand', 'chest')),
  obtained_from TEXT NOT NULL CHECK (obtained_from IN ('seed', 'levelup')),
  obtained_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_pk, item_id),
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE user_mascot_equipment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  mascot_id TEXT NOT NULL CHECK (mascot_id IN ('fox', 'owl')),
  item_id TEXT,
  equipped_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_pk, mascot_id),
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE user_level_reward_claims (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER NOT NULL,
  level INTEGER NOT NULL CHECK (level >= 1),
  item_id TEXT NOT NULL,
  duplicate_converted INTEGER NOT NULL DEFAULT 0 CHECK (duplicate_converted IN (0, 1)),
  converted_xp INTEGER NOT NULL DEFAULT 0 CHECK (converted_xp >= 0),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_pk, level),
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reporter_user_pk INTEGER NOT NULL,
  target_type TEXT NOT NULL CHECK (target_type IN ('mission', 'mission_response', 'user', 'coop_challenge')),
  target_id TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (reason IN ('assedio', 'dados_pessoais', 'improprio', 'bullying', 'spam', 'outro')),
  details_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(details_json)),
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_review', 'resolved', 'dismissed')),
  resolved_by_user_pk INTEGER,
  resolution_note TEXT,
  resolved_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (reporter_user_pk) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (resolved_by_user_pk) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE blocks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  blocker_user_pk INTEGER NOT NULL,
  blocked_user_pk INTEGER NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (blocker_user_pk, blocked_user_pk),
  CHECK (blocker_user_pk <> blocked_user_pk),
  FOREIGN KEY (blocker_user_pk) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (blocked_user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE moderation_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  admin_user_pk INTEGER NOT NULL,
  target_user_pk INTEGER NOT NULL,
  action TEXT NOT NULL CHECK (action IN ('warn', 'mute', 'ban', 'unban', 'reset_password', 'reset_user_id')),
  reason TEXT NOT NULL,
  duration_minutes INTEGER,
  metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json)),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (admin_user_pk) REFERENCES users(id) ON DELETE RESTRICT,
  FOREIGN KEY (target_user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_user_pk INTEGER,
  actor_role TEXT NOT NULL,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(payload_json)),
  ip_address TEXT,
  user_agent TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (actor_user_pk) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE exports_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_id TEXT NOT NULL UNIQUE,
  requested_by_user_pk INTEGER NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'ready', 'failed')),
  file_path TEXT,
  summary_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(summary_json)),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (requested_by_user_pk) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE api_usage_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_pk INTEGER,
  ip_address TEXT,
  action_key TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status_role ON users(status, role);
CREATE INDEX idx_users_approval_status ON users(approval_status, created_at);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_pk);
CREATE INDEX idx_refresh_tokens_exp ON refresh_tokens(expires_at);

CREATE INDEX idx_account_requests_email_type ON account_requests(email, request_type);
CREATE INDEX idx_account_requests_status_exp ON account_requests(status, expires_at);

CREATE INDEX idx_lessons_trail_pos ON lessons(trail_id, position);
CREATE INDEX idx_quizzes_trail ON quizzes(trail_id);
CREATE UNIQUE INDEX idx_quiz_questions_quiz_pos ON quiz_questions(quiz_id, position);
CREATE UNIQUE INDEX idx_quiz_options_q_pos ON quiz_options(question_id, position);
CREATE INDEX idx_challenges_trail ON challenges(trail_id);

CREATE INDEX idx_lesson_completion_user ON lesson_completion(user_pk, completed_at);
CREATE INDEX idx_quiz_attempts_user ON quiz_attempts(user_pk, created_at);
CREATE INDEX idx_challenge_completion_user ON challenge_completion(user_pk, created_at);
CREATE INDEX idx_xp_events_user_time ON xp_events(user_pk, created_at);

CREATE INDEX idx_emotion_checkins_user_date ON emotion_checkins(user_pk, created_at);

CREATE INDEX idx_cards_category_tone ON support_cards(category, tone);
CREATE INDEX idx_missions_feed ON missions(status, category, created_at DESC);
CREATE INDEX idx_missions_creator ON missions(creator_user_pk, created_at DESC);
CREATE INDEX idx_missions_target ON missions(target_user_pk, status, created_at DESC);
CREATE INDEX idx_mission_responses_mission ON mission_responses(mission_id, created_at);
CREATE INDEX idx_mission_feedback_response ON mission_feedback(response_id, is_useful);

CREATE INDEX idx_coop_challenges_status ON coop_challenges(status, created_at);
CREATE INDEX idx_coop_memberships_user ON coop_memberships(user_pk, status);
CREATE INDEX idx_coop_progress_challenge ON coop_progress_events(coop_challenge_id, created_at);
CREATE INDEX idx_generated_trails_user ON generated_trails(user_pk, created_at);
CREATE INDEX idx_coop_pairs_status ON coop_pairs(status, created_at);
CREATE INDEX idx_coop_pairs_users ON coop_pairs(user_low_pk, user_high_pk);
CREATE INDEX idx_friendship_rewards_user ON friendship_xp_rewards(user_pk, created_at);
CREATE INDEX idx_mascot_inventory_user ON user_mascot_inventory(user_pk, obtained_at DESC);
CREATE INDEX idx_mascot_equipment_user ON user_mascot_equipment(user_pk, mascot_id);
CREATE INDEX idx_level_rewards_user ON user_level_reward_claims(user_pk, level);

CREATE INDEX idx_reports_status_time ON reports(status, created_at);
CREATE INDEX idx_reports_target ON reports(target_type, target_id);
CREATE INDEX idx_blocks_blocker ON blocks(blocker_user_pk);

CREATE INDEX idx_moderation_actions_target ON moderation_actions(target_user_pk, created_at);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id, created_at);

CREATE INDEX idx_exports_user_time ON exports_reports(requested_by_user_pk, created_at);
CREATE INDEX idx_api_usage_action_time ON api_usage_events(action_key, created_at);
CREATE INDEX idx_api_usage_user_time ON api_usage_events(user_pk, action_key, created_at);

CREATE TRIGGER trg_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER trg_account_requests_updated_at
AFTER UPDATE ON account_requests
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE account_requests SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER trg_trails_updated_at
AFTER UPDATE ON trails
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE trails SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER trg_lessons_updated_at
AFTER UPDATE ON lessons
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE lessons SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER trg_quizzes_updated_at
AFTER UPDATE ON quizzes
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE quizzes SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER trg_challenges_updated_at
AFTER UPDATE ON challenges
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE challenges SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER trg_missions_updated_at
AFTER UPDATE ON missions
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE missions SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER trg_coop_challenges_updated_at
AFTER UPDATE ON coop_challenges
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE coop_challenges SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER trg_coop_memberships_updated_at
AFTER UPDATE ON coop_memberships
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE coop_memberships SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER trg_generated_trails_updated_at
AFTER UPDATE ON generated_trails
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE generated_trails SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER trg_reports_updated_at
AFTER UPDATE ON reports
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE reports SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER trg_exports_reports_updated_at
AFTER UPDATE ON exports_reports
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE exports_reports SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
