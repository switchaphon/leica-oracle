use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Deserialize, Serialize)]
pub struct GatewayPayload {
    pub op: u64,
    pub d: Option<Value>,
    pub s: Option<u64>,
    pub t: Option<String>,
}

#[derive(Debug, Deserialize, Serialize, PartialEq, Eq)]
pub struct HelloData {
    pub heartbeat_interval: u64,
}

#[derive(Debug, Serialize, PartialEq, Eq)]
pub struct IdentifyData {
    pub token: String,
    pub intents: u64,
    pub properties: IdentifyProperties,
}

#[derive(Debug, Serialize, PartialEq, Eq)]
pub struct IdentifyProperties {
    pub os: String,
    pub browser: String,
    pub device: String,
}

#[derive(Debug, Deserialize, Serialize, PartialEq, Eq)]
pub struct MessageCreateEvent {
    #[serde(flatten)]
    pub message: MessageData,
}

#[derive(Debug, Deserialize, Serialize, Clone, PartialEq, Eq)]
pub struct MessageData {
    pub id: String,
    pub channel_id: String,
    pub content: String,
    pub author: Author,
    #[serde(default)]
    pub mentions: Vec<Author>,
}

#[derive(Debug, Deserialize, Serialize, Clone, PartialEq, Eq)]
pub struct Author {
    pub id: String,
    pub username: String,
    #[serde(default)]
    pub bot: bool,
}

#[derive(Debug, Serialize, PartialEq, Eq)]
pub struct CreateMessage {
    pub content: String,
}

#[cfg(test)]
mod tests {
    use super::{Author, GatewayPayload, HelloData, MessageData};

    #[test]
    fn parse_gateway_hello_payload() -> Result<(), serde_json::Error> {
        let payload: GatewayPayload =
            serde_json::from_str(r#"{"op":10,"d":{"heartbeat_interval":41250},"s":null,"t":null}"#)?;
        let data: HelloData = serde_json::from_value(
            payload
                .d
                .ok_or_else(|| serde_json::Error::io(std::io::ErrorKind::InvalidData.into()))?,
        )?;

        assert_eq!(payload.op, 10);
        assert_eq!(data.heartbeat_interval, 41_250);
        Ok(())
    }

    #[test]
    fn message_data_with_empty_mentions_array_deserializes() -> Result<(), serde_json::Error> {
        let message: MessageData = serde_json::from_str(
            r#"{
                "id":"m1",
                "channel_id":"c1",
                "content":"hello",
                "author":{"id":"human","username":"human","bot":false},
                "mentions":[]
            }"#,
        )?;

        assert!(message.mentions.is_empty());
        Ok(())
    }

    #[test]
    fn message_data_without_mentions_defaults_to_empty() -> Result<(), serde_json::Error> {
        let message: MessageData = serde_json::from_str(
            r#"{
                "id":"m1",
                "channel_id":"c1",
                "content":"hello",
                "author":{"id":"human","username":"human","bot":false}
            }"#,
        )?;

        assert!(message.mentions.is_empty());
        Ok(())
    }

    #[test]
    fn author_bot_false_and_missing_bot_both_deserialize_false() -> Result<(), serde_json::Error> {
        let explicit: Author =
            serde_json::from_str(r#"{"id":"1","username":"human","bot":false}"#)?;
        let missing: Author = serde_json::from_str(r#"{"id":"2","username":"human"}"#)?;

        assert!(!explicit.bot);
        assert!(!missing.bot);
        Ok(())
    }

    #[test]
    fn gateway_payload_with_null_sequence_deserializes() -> Result<(), serde_json::Error> {
        let payload: GatewayPayload =
            serde_json::from_str(r#"{"op":10,"d":{"heartbeat_interval":1},"s":null,"t":null}"#)?;

        assert_eq!(payload.s, None);
        Ok(())
    }
}
