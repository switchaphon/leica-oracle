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
    use super::{GatewayPayload, HelloData};

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
}
