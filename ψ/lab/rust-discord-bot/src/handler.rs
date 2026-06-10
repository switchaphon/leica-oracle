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

    for character in content.chars() {
        if current.chars().count() == DISCORD_MESSAGE_LIMIT {
            chunks.push(current);
            current = String::new();
        }
        current.push(character);
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
}
