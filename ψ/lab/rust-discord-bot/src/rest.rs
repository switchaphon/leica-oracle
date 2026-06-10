use crate::{error::DiscordError, types::CreateMessage};

const DISCORD_API_BASE: &str = "https://discord.com/api/v10";

pub fn send_message(token: &str, channel_id: &str, content: &str) -> Result<(), DiscordError> {
    let url = format!("{DISCORD_API_BASE}/channels/{channel_id}/messages");
    let authorization = format!("Bot {token}");
    let body = CreateMessage {
        content: content.to_owned(),
    };

    ureq::post(&url)
        .header("Authorization", authorization)
        .header("Content-Type", "application/json")
        .send_json(&body)?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::DISCORD_API_BASE;

    #[test]
    fn discord_api_base_targets_v10() {
        assert_eq!(DISCORD_API_BASE, "https://discord.com/api/v10");
    }
}
