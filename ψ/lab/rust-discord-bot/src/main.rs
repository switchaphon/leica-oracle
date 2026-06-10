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

    eprintln!("[bot] connecting to gateway...");
    let mut gateway = DiscordGateway::connect()?;
    let hello = gateway.receive_hello()?;
    eprintln!("[bot] hello received, heartbeat interval: {}ms", hello.heartbeat_interval);
    gateway.start_heartbeat(hello.heartbeat_interval);
    gateway.send_identify(&token)?;
    eprintln!("[bot] identify sent, waiting for messages...");

    loop {
        let message = gateway.next_message()?;
        eprintln!("[bot] message from {}: {}", message.author.username, message.content);
        if let Some(chunks) = handle_message(&message, &bot_user_id) {
            eprintln!("[bot] responding with {} chunk(s)", chunks.len());
            for chunk in chunks {
                send_message(&token, &message.channel_id, &chunk)?;
            }
            eprintln!("[bot] sent!");
        } else {
            eprintln!("[bot] ignored (not mentioned)");
        }
    }
}
