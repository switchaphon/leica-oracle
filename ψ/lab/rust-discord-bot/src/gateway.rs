use std::{
    io::ErrorKind,
    net::TcpStream,
    time::{Duration, Instant},
};

use serde_json::{json, Value};
use tungstenite::{
    connect,
    stream::MaybeTlsStream,
    Message, WebSocket,
};

use crate::{
    error::DiscordError,
    types::{
        GatewayPayload, HelloData, IdentifyData, IdentifyProperties, MessageCreateEvent,
        MessageData,
    },
};

const GATEWAY_URL: &str = "wss://gateway.discord.gg/?v=10&encoding=json";
const OP_DISPATCH: u64 = 0;
const OP_HEARTBEAT: u64 = 1;
const OP_IDENTIFY: u64 = 2;
const OP_HELLO: u64 = 10;
const MESSAGE_CREATE: &str = "MESSAGE_CREATE";
const MESSAGE_INTENTS: u64 = 33_280;

pub struct DiscordGateway {
    socket: WebSocket<MaybeTlsStream<TcpStream>>,
    last_sequence: Option<u64>,
    heartbeat_interval: Option<Duration>,
    next_heartbeat: Option<Instant>,
}

impl DiscordGateway {
    pub fn connect() -> Result<Self, DiscordError> {
        let (mut socket, _) = connect(GATEWAY_URL)?;
        set_read_timeout(socket.get_mut(), Duration::from_secs(1))?;

        Ok(Self {
            socket,
            last_sequence: None,
            heartbeat_interval: None,
            next_heartbeat: None,
        })
    }

    pub fn receive_hello(&mut self) -> Result<HelloData, DiscordError> {
        loop {
            let payload = self.read_payload()?;
            self.record_sequence(payload.s);

            if payload.op == OP_HELLO {
                let data = payload
                    .d
                    .ok_or_else(|| DiscordError::Gateway("hello payload missing data".to_owned()))?;
                return Ok(serde_json::from_value(data)?);
            }
        }
    }

    pub fn send_identify(&mut self, token: &str) -> Result<(), DiscordError> {
        let data = IdentifyData {
            token: token.to_owned(),
            intents: MESSAGE_INTENTS,
            properties: IdentifyProperties {
                os: std::env::consts::OS.to_owned(),
                browser: "leica-discord".to_owned(),
                device: "leica-discord".to_owned(),
            },
        };
        let payload = json!({ "op": OP_IDENTIFY, "d": data });

        self.socket.send(Message::Text(payload.to_string()))?;
        Ok(())
    }

    pub fn start_heartbeat(&mut self, interval_ms: u64) {
        let interval = Duration::from_millis(interval_ms);
        self.heartbeat_interval = Some(interval);
        self.next_heartbeat = Some(Instant::now() + interval);
    }

    pub fn next_message(&mut self) -> Result<MessageData, DiscordError> {
        loop {
            let payload = self.read_payload()?;
            self.record_sequence(payload.s);

            if payload.op == OP_DISPATCH && payload.t.as_deref() == Some(MESSAGE_CREATE) {
                let data = payload.d.ok_or_else(|| {
                    DiscordError::Gateway("MESSAGE_CREATE payload missing data".to_owned())
                })?;
                let event = serde_json::from_value::<MessageCreateEvent>(data)?;
                return Ok(event.message);
            }
        }
    }

    fn read_payload(&mut self) -> Result<GatewayPayload, DiscordError> {
        loop {
            self.send_heartbeat_if_due()?;

            let message = match self.socket.read() {
                Ok(message) => message,
                Err(tungstenite::Error::Io(error)) if error.kind() == ErrorKind::WouldBlock => {
                    continue;
                }
                Err(tungstenite::Error::Io(error)) if error.kind() == ErrorKind::TimedOut => {
                    continue;
                }
                Err(error) => return Err(DiscordError::from(error)),
            };

            match message {
                Message::Text(text) => return parse_gateway_payload(&text),
                Message::Binary(bytes) => return Ok(serde_json::from_slice(&bytes)?),
                Message::Ping(bytes) => self.socket.send(Message::Pong(bytes))?,
                Message::Pong(_) | Message::Frame(_) => {}
                Message::Close(frame) => {
                    return Err(DiscordError::Gateway(format!(
                        "gateway closed: {}",
                        close_reason(frame.as_ref())
                    )));
                }
            }
        }
    }

    fn record_sequence(&mut self, sequence: Option<u64>) {
        if let Some(value) = sequence {
            self.last_sequence = Some(value);
        }
    }

    fn send_heartbeat_if_due(&mut self) -> Result<(), DiscordError> {
        let Some(next_heartbeat) = self.next_heartbeat else {
            return Ok(());
        };

        if Instant::now() < next_heartbeat {
            return Ok(());
        }

        self.socket
            .send(Message::Text(heartbeat_payload(self.last_sequence).to_string()))?;

        if let Some(interval) = self.heartbeat_interval {
            self.next_heartbeat = Some(Instant::now() + interval);
        }

        Ok(())
    }
}

pub fn parse_gateway_payload(text: &str) -> Result<GatewayPayload, DiscordError> {
    Ok(serde_json::from_str(text)?)
}

#[cfg(test)]
pub fn parse_hello(text: &str) -> Result<HelloData, DiscordError> {
    let payload = parse_gateway_payload(text)?;
    if payload.op != OP_HELLO {
        return Err(DiscordError::Gateway("expected hello payload".to_owned()));
    }

    let data = payload
        .d
        .ok_or_else(|| DiscordError::Gateway("hello payload missing data".to_owned()))?;
    Ok(serde_json::from_value(data)?)
}

#[cfg(test)]
pub fn parse_message_create(text: &str) -> Result<Option<MessageData>, DiscordError> {
    let payload = parse_gateway_payload(text)?;
    if payload.op != OP_DISPATCH || payload.t.as_deref() != Some(MESSAGE_CREATE) {
        return Ok(None);
    }

    let data = payload
        .d
        .ok_or_else(|| DiscordError::Gateway("MESSAGE_CREATE payload missing data".to_owned()))?;
    Ok(Some(serde_json::from_value::<MessageCreateEvent>(data)?.message))
}

fn heartbeat_payload(sequence: Option<u64>) -> Value {
    json!({ "op": OP_HEARTBEAT, "d": sequence })
}

fn set_read_timeout(
    stream: &mut MaybeTlsStream<TcpStream>,
    timeout: Duration,
) -> Result<(), DiscordError> {
    match stream {
        MaybeTlsStream::Plain(tcp_stream) => tcp_stream
            .set_read_timeout(Some(timeout))
            .map_err(|error| DiscordError::from(tungstenite::Error::Io(error)))?,
        MaybeTlsStream::NativeTls(tls_stream) => tls_stream
            .get_ref()
            .set_read_timeout(Some(timeout))
            .map_err(|error| DiscordError::from(tungstenite::Error::Io(error)))?,
        _ => {
            return Err(DiscordError::Gateway(
                "unsupported websocket stream type".to_owned(),
            ));
        }
    }

    Ok(())
}

fn close_reason(frame: Option<&tungstenite::protocol::CloseFrame>) -> String {
    frame
        .map(|close| format!("{} {}", close.code, close.reason))
        .unwrap_or_else(|| "no close frame".to_owned())
}

#[cfg(test)]
mod tests {
    use super::{heartbeat_payload, parse_gateway_payload, parse_hello, parse_message_create};
    use crate::error::DiscordError;

    #[test]
    fn parse_gateway_hello_payload() -> Result<(), DiscordError> {
        let hello = parse_hello(r#"{"op":10,"d":{"heartbeat_interval":45000},"s":null,"t":null}"#)?;

        assert_eq!(hello.heartbeat_interval, 45_000);
        Ok(())
    }

    #[test]
    fn parse_message_create_event() -> Result<(), DiscordError> {
        let event = r#"{
            "op":0,
            "d":{
                "id":"m1",
                "channel_id":"c1",
                "content":"<@42> sawasdee",
                "author":{"id":"7","username":"human","bot":false},
                "mentions":[{"id":"42","username":"oracle","bot":true}]
            },
            "s":9,
            "t":"MESSAGE_CREATE"
        }"#;

        let message = parse_message_create(event)?
            .ok_or_else(|| DiscordError::Gateway("expected message".to_owned()))?;

        assert_eq!(message.channel_id, "c1");
        assert_eq!(message.mentions.len(), 1);
        Ok(())
    }

    #[test]
    fn malformed_json_returns_discord_json_error() {
        let error = parse_gateway_payload("{not-json}");

        assert!(matches!(error, Err(DiscordError::Json(_))));
    }

    #[test]
    fn heartbeat_payload_uses_last_sequence() {
        let payload = heartbeat_payload(Some(12));

        assert_eq!(payload["op"], 1);
        assert_eq!(payload["d"], 12);
    }
}
