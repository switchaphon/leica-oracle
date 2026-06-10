use crate::types::MessageData;

const DISCORD_MESSAGE_LIMIT: usize = 2_000;

pub fn should_respond(message: &MessageData, bot_user_id: &str) -> bool {
    message.mentions.iter().any(|author| author.id == bot_user_id)
}

pub fn handle_message(message: &MessageData, bot_user_id: &str) -> Option<Vec<String>> {
    if should_respond(message, bot_user_id) {
        Some(chunk_message("Oracle heard you."))
    } else {
        None
    }
}

pub fn chunk_message(content: &str) -> Vec<String> {
    if content.is_empty() {
        return vec![String::new()];
    }

    let mut chunks = Vec::new();
    let mut current = String::new();
    let mut current_len = 0;

    for character in content.chars() {
        if current_len == DISCORD_MESSAGE_LIMIT {
            chunks.push(current);
            current = String::new();
            current_len = 0;
        }
        current.push(character);
        current_len += 1;
    }

    if !current.is_empty() {
        chunks.push(current);
    }

    chunks
}

#[cfg(test)]
mod tests {
    use super::{chunk_message, handle_message, should_respond};
    use crate::types::{Author, MessageData};

    fn message_with_mentions(mentions: Vec<Author>) -> MessageData {
        MessageData {
            id: "m1".to_owned(),
            channel_id: "c1".to_owned(),
            content: "hello".to_owned(),
            author: Author {
                id: "human".to_owned(),
                username: "human".to_owned(),
                bot: false,
            },
            mentions,
        }
    }

    fn author(id: &str) -> Author {
        Author {
            id: id.to_owned(),
            username: format!("user-{id}"),
            bot: false,
        }
    }

    #[test]
    fn silence_rule_mention_self_responds() {
        let message = message_with_mentions(vec![author("bot-1")]);

        assert!(should_respond(&message, "bot-1"));
        assert!(handle_message(&message, "bot-1").is_some());
    }

    #[test]
    fn silence_rule_mention_other_ignores() {
        let message = message_with_mentions(vec![author("other-bot")]);

        assert!(!should_respond(&message, "bot-1"));
        assert!(handle_message(&message, "bot-1").is_none());
    }

    #[test]
    fn thai_text_over_two_thousand_chars_splits_on_char_boundaries() {
        let content = "ก".repeat(2_005);
        let chunks = chunk_message(&content);

        assert_eq!(chunks.len(), 2);
        assert_eq!(chunks[0].chars().count(), 2_000);
        assert_eq!(chunks[1].chars().count(), 5);
        assert_eq!(chunks.concat(), content);
    }

    #[test]
    fn empty_message_content_with_mention_still_responds() {
        let mut message = message_with_mentions(vec![author("bot-1")]);
        message.content = String::new();

        assert!(handle_message(&message, "bot-1").is_some());
    }

    #[test]
    fn message_deserialized_without_mentions_defaults_to_silent() -> Result<(), serde_json::Error> {
        let message: MessageData = serde_json::from_str(
            r#"{
                "id":"m1",
                "channel_id":"c1",
                "content":"hello",
                "author":{"id":"human","username":"human"}
            }"#,
        )?;

        assert!(message.mentions.is_empty());
        assert!(!should_respond(&message, "bot-1"));
        Ok(())
    }

    #[test]
    fn message_where_author_is_bot_user_requires_explicit_mention() {
        let message = MessageData {
            id: "m1".to_owned(),
            channel_id: "c1".to_owned(),
            content: "self-authored".to_owned(),
            author: author("bot-1"),
            mentions: Vec::new(),
        };

        assert!(!should_respond(&message, "bot-1"));
    }

    #[test]
    fn multiple_mentions_including_bot_responds() {
        let message = message_with_mentions(vec![author("human-2"), author("bot-1")]);

        assert!(should_respond(&message, "bot-1"));
    }

    #[test]
    fn another_bot_mentioning_this_bot_still_responds() {
        let mut message = message_with_mentions(vec![author("bot-1")]);
        message.author = Author {
            id: "other-bot".to_owned(),
            username: "relay".to_owned(),
            bot: true,
        };

        assert!(should_respond(&message, "bot-1"));
    }

    #[test]
    fn exactly_two_thousand_chars_returns_one_chunk() {
        let content = "a".repeat(2_000);
        let chunks = chunk_message(&content);

        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0], content);
    }

    #[test]
    fn two_thousand_one_chars_returns_two_chunks() {
        let content = "a".repeat(2_001);
        let chunks = chunk_message(&content);

        assert_eq!(chunks.len(), 2);
        assert_eq!(chunks[0].chars().count(), 2_000);
        assert_eq!(chunks[1].chars().count(), 1);
    }

    #[test]
    fn empty_string_returns_single_empty_chunk() {
        let chunks = chunk_message("");

        assert_eq!(chunks, vec![String::new()]);
    }

    #[test]
    fn emoji_text_splits_on_char_boundary() {
        let content = "🔥".repeat(2_001);
        let chunks = chunk_message(&content);

        assert_eq!(chunks.len(), 2);
        assert_eq!(chunks[0].chars().count(), 2_000);
        assert_eq!(chunks[1].chars().count(), 1);
        assert_eq!(chunks.concat(), content);
    }

    #[test]
    fn mixed_thai_emoji_ascii_text_splits_and_reassembles() {
        let content = "ไทย🔥abc".repeat(401);
        let chunks = chunk_message(&content);

        assert_eq!(chunks.len(), 2);
        assert!(chunks.iter().all(|chunk| chunk.chars().count() <= 2_000));
        assert_eq!(chunks.concat(), content);
    }

    #[test]
    fn single_unicode_char_is_one_chunk_even_when_multibyte() {
        let chunks = chunk_message("𒀱");

        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0].chars().count(), 1);
        assert_eq!(chunks[0], "𒀱");
    }

    #[test]
    fn stress_chunking_large_unicode_message() {
        let content = "ก🔥a".repeat(10_001);
        let chunks = chunk_message(&content);

        assert_eq!(chunks.len(), 16);
        assert!(chunks.iter().all(|chunk| chunk.chars().count() <= 2_000));
        assert_eq!(chunks.concat(), content);
    }
}
