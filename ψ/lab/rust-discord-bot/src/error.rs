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

    #[test]
    fn all_error_variants_have_meaningful_display_output() {
        let websocket = DiscordError::from(tungstenite::Error::AlreadyClosed);
        let json = match serde_json::from_str::<serde_json::Value>("{bad}") {
            Ok(_) => DiscordError::Gateway("expected malformed json".to_owned()),
            Err(error) => DiscordError::from(error),
        };
        let http = DiscordError::from(ureq::Error::StatusCode(401));
        let gateway = DiscordError::Gateway("missing hello".to_owned());
        let invalid_token = DiscordError::InvalidToken("empty token".to_owned());

        assert!(websocket.to_string().contains("websocket error"));
        assert!(json.to_string().contains("json error"));
        assert!(http.to_string().contains("http error"));
        assert!(gateway.to_string().contains("missing hello"));
        assert!(invalid_token.to_string().contains("empty token"));
    }

    #[test]
    fn from_tungstenite_error_wraps_as_websocket_variant() {
        let error = DiscordError::from(tungstenite::Error::AlreadyClosed);

        assert!(matches!(error, DiscordError::WebSocket(_)));
    }

    #[test]
    fn from_ureq_error_wraps_as_http_variant() {
        let error = DiscordError::from(ureq::Error::StatusCode(500));

        assert!(matches!(error, DiscordError::Http(_)));
    }

    #[test]
    fn gateway_error_with_empty_string_still_names_variant() {
        let error = DiscordError::Gateway(String::new());

        assert!(error.to_string().starts_with("gateway error:"));
    }
}
