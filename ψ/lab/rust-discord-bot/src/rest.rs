use crate::{error::DiscordError, types::CreateMessage};

const DISCORD_API_BASE: &str = "https://discord.com/api/v10";

pub fn send_message(token: &str, channel_id: &str, content: &str) -> Result<(), DiscordError> {
    let url = message_url(channel_id);
    let authorization = authorization_header(token);
    let body = CreateMessage {
        content: content.to_owned(),
    };

    ureq::post(&url)
        .header("Authorization", authorization)
        .header("Content-Type", "application/json")
        .send_json(&body)?;

    Ok(())
}

fn message_url(channel_id: &str) -> String {
    format!("{DISCORD_API_BASE}/channels/{channel_id}/messages")
}

fn authorization_header(token: &str) -> String {
    format!("Bot {token}")
}

#[cfg(test)]
mod tests {
    use super::{authorization_header, message_url, DISCORD_API_BASE};

    #[test]
    fn discord_api_base_targets_v10() {
        assert_eq!(DISCORD_API_BASE, "https://discord.com/api/v10");
    }

    #[test]
    fn message_url_preserves_channel_id_special_characters() {
        let url = message_url("channel:with/slash?raw=true");

        assert_eq!(
            url,
            "https://discord.com/api/v10/channels/channel:with/slash?raw=true/messages"
        );
    }

    #[test]
    fn authorization_header_uses_exact_bot_prefix() {
        let header = authorization_header("token-123");

        assert_eq!(header, "Bot token-123");
    }
}
