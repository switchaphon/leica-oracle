use thiserror::Error;

#[derive(Debug, Error)]
pub enum DiscordError {
    #[error("websocket error: {0}")]
    WebSocket(#[source] Box<tungstenite::Error>),

    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("http error: {0}")]
    Http(#[source] Box<ureq::Error>),

    #[error("gateway error: {0}")]
    Gateway(String),

    #[error("invalid token: {0}")]
    InvalidToken(String),
}

impl From<tungstenite::Error> for DiscordError {
    fn from(error: tungstenite::Error) -> Self {
        Self::WebSocket(Box::new(error))
    }
}

impl From<ureq::Error> for DiscordError {
    fn from(error: ureq::Error) -> Self {
        Self::Http(Box::new(error))
    }
}

#[cfg(test)]
mod tests {
    use super::DiscordError;

    #[test]
    fn invalid_token_message_contains_reason() {
        let error = DiscordError::InvalidToken("DISCORD_TOKEN not set".to_owned());

        assert!(error.to_string().contains("DISCORD_TOKEN not set"));
    }
}
