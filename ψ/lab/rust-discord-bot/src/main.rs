#![deny(clippy::unwrap_used)]

mod error;
mod gateway;
mod handler;
mod rest;
mod types;

use error::DiscordError;
use gateway::DiscordGateway;
use handler::handle_message;
use rest::send_message;

fn main() -> Result<(), DiscordError> {
    let token = std::env::var("DISCORD_TOKEN")
        .map_err(|_| DiscordError::InvalidToken("DISCORD_TOKEN not set".to_owned()))?;
    let bot_user_id = std::env::var("DISCORD_BOT_USER_ID")
        .map_err(|_| DiscordError::InvalidToken("DISCORD_BOT_USER_ID not set".to_owned()))?;

    let mut gateway = DiscordGateway::connect()?;
    let hello = gateway.receive_hello()?;
    gateway.start_heartbeat(hello.heartbeat_interval);
    gateway.send_identify(&token)?;

    loop {
        let message = gateway.next_message()?;
        if let Some(chunks) = handle_message(&message, &bot_user_id) {
            for chunk in chunks {
                send_message(&token, &message.channel_id, &chunk)?;
            }
        }
    }
}
